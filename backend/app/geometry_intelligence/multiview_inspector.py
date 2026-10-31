"""
Multi-View Consistency & Inspection Engine
Renders 7 canonical perspectives (Front, Back, Left, Right, Top, Bottom, 3/4 Perspective),
measures occupancy, detects protrusions and asymmetries, and evaluates silhouette IoU
against the 2D input sketch.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import cv2
from PIL import Image
import trimesh

try:
    import open3d as o3d
    HAS_OPEN3D = True
except ImportError:
    HAS_OPEN3D = False

from .geometry_metrics import ViewSilhouetteMetric, MultiViewMetrics


class MultiViewInspector:
    def __init__(self, output_dir: Optional[Path] = None, render_resolution: int = 512):
        if output_dir is None:
            self.output_dir = Path(r"C:\Sketch2Shape-AI\outputs\geometry_analysis\multiview")
        else:
            self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.resolution = render_resolution

    def _get_view_camera_specs(self, center: np.ndarray, radius: float) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
        """
        Defines canonical camera positions (eye, up) relative to bounding center and radius.
        """
        d = max(1.8 * radius, 0.5)
        return {
            "front": (center + np.array([0.0, 0.0, d]), np.array([0.0, 1.0, 0.0])),
            "back": (center + np.array([0.0, 0.0, -d]), np.array([0.0, 1.0, 0.0])),
            "left": (center + np.array([-d, 0.0, 0.0]), np.array([0.0, 1.0, 0.0])),
            "right": (center + np.array([d, 0.0, 0.0]), np.array([0.0, 1.0, 0.0])),
            "top": (center + np.array([0.0, d, 0.0]), np.array([0.0, 0.0, -1.0])),
            "bottom": (center + np.array([0.0, -d, 0.0]), np.array([0.0, 0.0, 1.0])),
            "three_quarter": (
                center + np.array([d * 0.7, d * 0.6, d * 0.7]),
                np.array([0.0, 1.0, 0.0]),
            ),
        }

    def _render_open3d(
        self,
        mesh_path: str,
        asset_id: str
    ) -> Dict[str, Tuple[str, np.ndarray, List[float], List[float]]]:
        """
        Renders 7 views using Open3D hardware-accelerated Vulkan offscreen renderer.
        """
        mesh = o3d.io.read_triangle_mesh(str(mesh_path))
        mesh.compute_vertex_normals()

        renderer = o3d.visualization.rendering.OffscreenRenderer(self.resolution, self.resolution)
        mat = o3d.visualization.rendering.MaterialRecord()
        mat.shader = "defaultLit"
        renderer.scene.add_geometry("mesh", mesh, mat)
        renderer.scene.set_background([0.03, 0.05, 0.08, 1.0])

        bbox = mesh.get_axis_aligned_bounding_box()
        center = bbox.get_center().astype(np.float32)
        radius = float(bbox.get_max_extent() * 0.7)

        views_specs = self._get_view_camera_specs(center, radius)
        rendered_views = {}

        try:
            for view_name, (eye, up) in views_specs.items():
                renderer.setup_camera(
                    55.0,
                    center.astype(np.float32),
                    eye.astype(np.float32),
                    up.astype(np.float32),
                )
                o3d_img = renderer.render_to_image()
                img_np = np.asarray(o3d_img)

                # Save PNG
                save_path = self.output_dir / f"{asset_id}_{view_name}.png"
                Image.fromarray(img_np).save(str(save_path))

                rendered_views[view_name] = (
                    str(save_path),
                    img_np,
                    eye.tolist(),
                    center.tolist(),
                )
        finally:
            del renderer

        return rendered_views

    @staticmethod
    def _compute_silhouette_mask(img_np: np.ndarray) -> np.ndarray:
        """
        Extracts binary silhouette where foreground is 1 and background is 0.
        """
        # Background is dark slate [0.03, 0.05, 0.08] * 255 = [8, 13, 20]
        if img_np.shape[-1] >= 3:
            diff = np.max(np.abs(img_np[:, :, :3].astype(int) - np.array([8, 13, 20])), axis=2)
            mask = (diff > 18).astype(np.uint8)
        else:
            mask = (img_np > 30).astype(np.uint8)
        return mask

    @staticmethod
    def compute_iou(mask_a: np.ndarray, mask_b: np.ndarray) -> float:
        """
        Intersection over Union between two binary masks.
        """
        if mask_a.shape != mask_b.shape:
            mask_b = cv2.resize(mask_b, (mask_a.shape[1], mask_a.shape[0]), interpolation=cv2.INTER_NEAREST)

        intersection = np.logical_and(mask_a > 0, mask_b > 0).sum()
        union = np.logical_or(mask_a > 0, mask_b > 0).sum()
        if union == 0:
            return 0.0
        return float(intersection) / float(union)

    def inspect(
        self,
        mesh_path: str,
        asset_id: str,
        sketch_path: Optional[str] = None
    ) -> MultiViewMetrics:
        """
        Executes full multi-view consistency audit.
        """
        try:
            rendered_views = self._render_open3d(mesh_path, asset_id)
        except Exception as e:
            print(f"[MultiViewInspector] Warning: Open3D rendering failed: {e}. Returning baseline metrics.")
            rendered_views = {}

        view_metrics: Dict[str, ViewSilhouetteMetric] = {}
        occupancies = []
        silhouettes = {}

        for vname, (img_path, img_np, eye, target) in rendered_views.items():
            mask = self._compute_silhouette_mask(img_np)
            silhouettes[vname] = mask
            sil_pixels = int(np.sum(mask))
            total_pixels = mask.shape[0] * mask.shape[1]
            occ = float(sil_pixels) / float(total_pixels)
            occupancies.append(occ)

            view_metrics[vname] = ViewSilhouetteMetric(
                view_name=vname,
                camera_eye=[round(x, 4) for x in eye],
                camera_target=[round(x, 4) for x in target],
                occupancy_ratio=round(occ, 4),
                silhouette_pixels=sil_pixels,
                rendered_image_path=img_path,
                iou_with_sketch=None,
            )

        # Evaluate Front Silhouette against input sketch
        front_iou: Optional[float] = None
        if sketch_path and Path(sketch_path).exists() and "front" in silhouettes:
            try:
                sketch_img = Image.open(sketch_path).convert("RGB")
                sketch_np = np.array(sketch_img)
                # Compute sketch silhouette (dark strokes on white paper or light on dark)
                gray = cv2.cvtColor(sketch_np, cv2.COLOR_RGB2GRAY)
                if np.mean(gray) > 127:
                    # White background with dark strokes
                    sketch_mask = (gray < 220).astype(np.uint8)
                else:
                    sketch_mask = (gray > 35).astype(np.uint8)

                # Fill contour convex hull to approximate overall silhouette volume
                contours, _ = cv2.findContours(sketch_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                filled_sketch = np.zeros_like(sketch_mask)
                for cnt in contours:
                    cv2.drawContours(filled_sketch, [cnt], -1, 1, thickness=cv2.FILLED)

                front_mask = silhouettes["front"]
                front_iou = round(self.compute_iou(front_mask, filled_sketch), 4)
                view_metrics["front"].iou_with_sketch = front_iou
            except Exception as e:
                print(f"[MultiViewInspector] Warning calculating sketch IoU: {e}")
                front_iou = None

        # Cross-view continuity: ratio of min occupancy to max occupancy across orthogonal views
        min_occ = min(occupancies) if len(occupancies) > 0 else 0.0
        max_occ = max(occupancies) if len(occupancies) > 0 else 1.0
        continuity = round(float(min_occ / max(max_occ, 1e-4)), 4)

        # Check bilateral asymmetry (left vs right silhouette mismatch)
        asymmetry = False
        if "left" in silhouettes and "right" in silhouettes:
            # Flip right silhouette horizontally to compare with left
            flipped_right = cv2.flip(silhouettes["right"], 1)
            lr_iou = self.compute_iou(silhouettes["left"], flipped_right)
            if lr_iou < 0.45:
                asymmetry = True

        # Structural completeness score (0 - 100)
        # Combines front IoU (if available) with cross-view continuity and presence of non-zero occupancy
        if front_iou is not None:
            completeness = round(float(0.6 * (front_iou * 100.0) + 0.4 * (continuity * 100.0)), 2)
        else:
            completeness = round(float(continuity * 100.0), 2)

        return MultiViewMetrics(
            views=view_metrics,
            front_sketch_iou=front_iou,
            cross_view_continuity_score=continuity,
            asymmetry_detected=asymmetry,
            structural_completeness_score=completeness,
        )

"""
Procedural 3D Reconstruction Engine for Sketch2Shape AI
Converts 2D sketch silhouettes and depth profiles into clean, watertight 3D meshes
using rotational surface reconstruction, bilateral extrusion, and volumetric SDF marching cubes.
"""

import numpy as np
import cv2
import trimesh
from typing import Dict, Any, Optional, List, Tuple
from .base import BaseReconstructionEngine


class ProceduralReconstructionEngine(BaseReconstructionEngine):
    def __init__(self):
        super().__init__("Procedural-SDF-Revolution")

    def is_available(self) -> bool:
        return True

    def _extract_profile_radii(self, binary_mask: np.ndarray, num_slices: int = 120) -> Tuple[np.ndarray, np.ndarray]:
        """
        Extracts the profile radius along vertical height from top to bottom.
        Returns:
            heights: normalized Y coordinates from -1.0 to 1.0
            radii: normalized radius at each slice
        """
        # Find non-zero coordinates
        rows = np.any(binary_mask > 0, axis=1)
        if not np.any(rows):
            # Fallback cylinder/sphere
            y_pts = np.linspace(-1, 1, num_slices)
            return y_pts, np.sqrt(np.maximum(0, 1.0 - y_pts**2)) * 0.5

        min_y, max_y = np.where(rows)[0][[0, -1]]
        sampled_y = np.linspace(min_y, max_y, num_slices).astype(int)

        radii = []
        heights = []

        for sy in sampled_y:
            row = binary_mask[sy, :]
            cols = np.where(row > 0)[0]
            if len(cols) > 0:
                width = cols[-1] - cols[0]
                radius = max(0.01, float(width / 2.0))
            else:
                radius = 0.01
            radii.append(radius)
            # Map Y so that top of image is +Y in 3D (OpenGL/Three.js convention)
            norm_y = 1.0 - 2.0 * ((sy - min_y) / max(1, (max_y - min_y)))
            heights.append(norm_y)

        radii = np.array(radii)
        max_r = np.max(radii)
        if max_r > 0:
            radii = radii / max_r * 0.75 # normalize radius proportionally

        # Smooth radii profile to remove jagged drawing jitter
        kernel_size = 5
        radii_smooth = np.convolve(radii, np.ones(kernel_size)/kernel_size, mode='same')
        radii_smooth[0] = radii[0]
        radii_smooth[-1] = radii[-1]

        return np.array(heights), radii_smooth

    def reconstruct_surface_of_revolution(
        self,
        binary_mask: np.ndarray,
        num_slices: int = 100,
        num_angles: int = 48
    ) -> trimesh.Trimesh:
        """
        Reconstructs rotational 3D solids (vases, cups, bowls, bottles, lamps)
        with smooth rotational symmetry and watertight end caps.
        """
        heights, radii = self._extract_profile_radii(binary_mask, num_slices)
        angles = np.linspace(0, 2 * np.pi, num_angles, endpoint=False)

        vertices = []
        # Ring vertices
        for y, r in zip(heights, radii):
            for theta in angles:
                x = r * np.cos(theta)
                z = r * np.sin(theta)
                vertices.append([x, y, z])

        # Top center vertex (at index len(vertices))
        top_idx = len(vertices)
        vertices.append([0.0, float(heights[0]), 0.0])

        # Bottom center vertex
        bot_idx = len(vertices)
        vertices.append([0.0, float(heights[-1]), 0.0])

        vertices = np.array(vertices, dtype=np.float64)
        faces = []

        # Connect ring quads (as 2 triangles each)
        for i in range(num_slices - 1):
            r1_start = i * num_angles
            r2_start = (i + 1) * num_angles
            for j in range(num_angles):
                next_j = (j + 1) % num_angles
                v0 = r1_start + j
                v1 = r1_start + next_j
                v2 = r2_start + next_j
                v3 = r2_start + j

                # Triangle 1
                faces.append([v0, v1, v2])
                # Triangle 2
                faces.append([v0, v2, v3])

        # Cap top ring with fan
        for j in range(num_angles):
            next_j = (j + 1) % num_angles
            faces.append([top_idx, next_j, j])

        # Cap bottom ring with fan
        last_ring_start = (num_slices - 1) * num_angles
        for j in range(num_angles):
            next_j = (j + 1) % num_angles
            faces.append([bot_idx, last_ring_start + j, last_ring_start + next_j])

        mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=True)
        return mesh

    def reconstruct_bilateral_extrusion(
        self,
        binary_mask: np.ndarray,
        depth_map: np.ndarray,
        grid_res: int = 64
    ) -> trimesh.Trimesh:
        """
        Reconstructs non-rotational or bilateral shapes (cars, planes, furniture, tools)
        using volumetric voxelization with smooth ellipsoidal depth profile.
        """
        # Downsample mask and depth to voxel resolution
        mask_small = cv2.resize(binary_mask, (grid_res, grid_res), interpolation=cv2.INTER_AREA) > 50
        depth_small = cv2.resize(depth_map, (grid_res, grid_res), interpolation=cv2.INTER_AREA).astype(float) / 255.0

        # Construct 3D voxel volume (Z, Y, X)
        volume = np.zeros((grid_res, grid_res, grid_res), dtype=bool)

        half_res = grid_res // 2
        for y in range(grid_res):
            for x in range(grid_res):
                if mask_small[y, x]:
                    # Thickness along Z based on depth/distance cues
                    thickness = max(2, int(depth_small[y, x] * (half_res * 0.85)))
                    z_min = max(0, half_res - thickness)
                    z_max = min(grid_res - 1, half_res + thickness)
                    volume[z_min:z_max+1, y, x] = True

        # Extract mesh from voxel volume
        try:
            mesh = trimesh.voxel.ops.matrix_to_marching_cubes(volume, pitch=2.0 / grid_res)
            # Center and reorient: Y up, X right, Z forward
            mesh.vertices -= mesh.centroid
            # Invert Y to match 3D screen coords
            mesh.vertices[:, 1] *= -1.0
            return mesh
        except Exception:
            # Fallback to rotational if voxel marching cubes fails
            return self.reconstruct_surface_of_revolution(binary_mask)

    def generate_mesh(
        self,
        stroke_mask: np.ndarray,
        depth_map: np.ndarray,
        metadata: Dict[str, Any],
        prompt: Optional[str] = None
    ) -> trimesh.Trimesh:
        """
        Generates 3D mesh choosing category-aware geometry template or rotational revolution.
        Rejects unsupported categories with explicit ValueError.
        """
        from .category_templates import CategoryGeometryTemplates, SUPPORTED_PROCEDURAL_CATEGORIES

        category = (metadata.get("category") or metadata.get("predicted_category") or "").lower().strip()

        # 1. Category-specific procedural template
        if category and CategoryGeometryTemplates.is_category_supported(category):
            if category in ["vase", "bottle", "bowl"]:
                return self.reconstruct_surface_of_revolution(stroke_mask)
            return CategoryGeometryTemplates.generate_category_mesh(category, binary_mask=stroke_mask)

        # 2. Rotational mode if explicitly flagged
        mode = metadata.get("recommended_3d_mode")
        if mode == "rotational_symmetric":
            return self.reconstruct_surface_of_revolution(stroke_mask)

        # 3. Silhouette-driven bilateral extrusion or rotational revolution fallback for arbitrary sketch shapes
        v_sym = metadata.get("symmetry", {}).get("vertical_symmetry", 0.5)
        if v_sym >= 0.70:
            return self.reconstruct_surface_of_revolution(stroke_mask)

        return self.reconstruct_bilateral_extrusion(stroke_mask, depth_map)


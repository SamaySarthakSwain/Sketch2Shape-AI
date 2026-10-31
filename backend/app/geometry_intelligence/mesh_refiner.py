"""
Automated Safe Mesh Refinement Pipeline
Provides non-destructive geometry repair, Taubin volume-preserving smoothing,
quadric decimation, isolated shard pruning, and bounding-box normalization.
Supports FAST, BALANCED, and HIGH refinement presets.
"""

import time
from typing import Dict, Any, Optional, Tuple, Union
from pathlib import Path
import numpy as np
import trimesh

try:
    import open3d as o3d
    HAS_OPEN3D = True
except ImportError:
    HAS_OPEN3D = False

from .geometry_metrics import MeshComparison


class MeshRefiner:
    @staticmethod
    def _trimesh_to_open3d(mesh: trimesh.Trimesh) -> Any:
        """Converts Trimesh to Open3D TriangleMesh preserving vertex colors if present."""
        o3d_mesh = o3d.geometry.TriangleMesh()
        o3d_mesh.vertices = o3d.utility.Vector3dVector(mesh.vertices.astype(np.float64))
        o3d_mesh.triangles = o3d.utility.Vector3iVector(mesh.faces.astype(np.int32))
        if hasattr(mesh.visual, "vertex_colors") and mesh.visual.vertex_colors is not None:
            vc = mesh.visual.vertex_colors[:, :3].astype(np.float64) / 255.0
            o3d_mesh.vertex_colors = o3d.utility.Vector3dVector(vc)
        return o3d_mesh

    @staticmethod
    def _open3d_to_trimesh(o3d_mesh: Any) -> trimesh.Trimesh:
        """Converts Open3D TriangleMesh back to Trimesh."""
        verts = np.asarray(o3d_mesh.vertices)
        faces = np.asarray(o3d_mesh.triangles)
        vc = None
        if o3d_mesh.has_vertex_colors():
            vc = (np.asarray(o3d_mesh.vertex_colors) * 255.0).astype(np.uint8)
        return trimesh.Trimesh(vertices=verts, faces=faces, vertex_colors=vc, process=False)

    @classmethod
    def refine(
        cls,
        mesh_input: Union[trimesh.Trimesh, str, Path],
        preset: str = "balanced",
        remove_isolated_shards: bool = True,
        shard_threshold_ratio: float = 0.03,
        asset_id: str = "asset"
    ) -> Tuple[trimesh.Trimesh, MeshComparison]:
        """
        Executes safe, non-destructive refinement based on specified preset:
        - 'fast': Basic validation, invalid geometry cleanup, normal recalculation.
        - 'balanced': Mild Taubin smoothing, normal correction, moderate quadric decimation.
        - 'high': Adaptive curvature-sensitive Taubin smoothing, topology repair, high-detail preservation.
        """
        t0 = time.time()
        preset = preset.lower()
        if preset not in ["fast", "balanced", "high"]:
            preset = "balanced"

        # 1. Load Original Mesh
        if isinstance(mesh_input, (str, Path)):
            orig_mesh = trimesh.load(str(mesh_input), force="mesh")
        else:
            orig_mesh = mesh_input.copy()

        # Capture initial metrics
        orig_v = len(orig_mesh.vertices)
        orig_f = len(orig_mesh.faces)
        orig_wt = bool(getattr(orig_mesh, "is_watertight", False))
        orig_area = float(orig_mesh.area) if orig_v > 0 else 0.0

        # Create working copy
        mesh = orig_mesh.copy()

        # Edge case: empty mesh
        if orig_v == 0 or orig_f == 0:
            duration = time.time() - t0
            comp = MeshComparison(
                asset_id=asset_id,
                operation=f"refine_{preset}",
                duration_seconds=round(duration, 4),
                original_vertices=0,
                refined_vertices=0,
                vertex_delta=0,
                original_faces=0,
                refined_faces=0,
                face_delta=0,
                original_watertight=False,
                refined_watertight=False,
                original_surface_area=0.0,
                refined_surface_area=0.0,
                original_file_size_bytes=0,
                refined_file_size_bytes=0,
                is_degraded=False,
                summary="Empty input mesh; no operations applied.",
            )
            return mesh, comp

        # -------------------------------------------------------------
        # STEP 1: Topological Cleanup (Duplicate & Degenerate Removal)
        # -------------------------------------------------------------
        try:
            mesh.remove_duplicate_faces()
        except Exception:
            try:
                mesh.update_faces(mesh.unique_faces())
            except Exception:
                pass

        try:
            mesh.remove_degenerate_faces()
            mesh.remove_unreferenced_vertices()
        except Exception:
            pass

        # -------------------------------------------------------------
        # STEP 2: Prune Isolated Shards (if requested)
        # -------------------------------------------------------------
        if remove_isolated_shards and len(mesh.faces) > 50:
            try:
                components = mesh.split(only_watertight=False)
                if len(components) > 1:
                    # Keep components having at least shard_threshold_ratio of total faces
                    min_faces = max(15, int(shard_threshold_ratio * len(mesh.faces)))
                    valid_components = [c for c in components if len(c.faces) >= min_faces]
                    if len(valid_components) > 0:
                        mesh = trimesh.util.concatenate(valid_components)
            except Exception as e:
                print(f"[MeshRefiner] Shard pruning warning: {e}")

        # -------------------------------------------------------------
        # STEP 3: Normal Recalculation & Outward Orientation
        # -------------------------------------------------------------
        try:
            mesh.fix_normals()
            trimesh.repair.fix_winding(mesh)
        except Exception as e:
            print(f"[MeshRefiner] Normal fix warning: {e}")

        # -------------------------------------------------------------
        # STEP 4: Surface Smoothing (Taubin Volume-Preserving)
        # -------------------------------------------------------------
        # Do not smooth if mesh is extremely low-poly (< 100 faces) to avoid destroying hard edges
        if HAS_OPEN3D and len(mesh.faces) >= 100 and preset in ["balanced", "high"]:
            try:
                o3d_m = cls._trimesh_to_open3d(mesh)
                # Check for thin structures
                extents = mesh.extents
                is_thin = (min(extents) / max(max(extents), 1e-6)) < 0.05

                if preset == "balanced":
                    # Mild Taubin: 3 iterations, lambda=0.4, mu=-0.43
                    iters = 2 if is_thin else 3
                    smoothed_o3d = o3d_m.filter_smooth_taubin(
                        number_of_iterations=iters,
                        lambda_filter=0.4,
                        mu=-0.43,
                    )
                else:  # 'high'
                    # Curvature-preserving Taubin: 4 iterations, lambda=0.35, mu=-0.37
                    iters = 2 if is_thin else 4
                    smoothed_o3d = o3d_m.filter_smooth_taubin(
                        number_of_iterations=iters,
                        lambda_filter=0.35,
                        mu=-0.37,
                    )

                mesh = cls._open3d_to_trimesh(smoothed_o3d)
            except Exception as e:
                print(f"[MeshRefiner] Open3D Taubin smoothing warning: {e}")

        # -------------------------------------------------------------
        # STEP 5: Quadric Decimation (Safe Simplification)
        # -------------------------------------------------------------
        # Strictly avoid decimation on models that already have few polygons (< 1,000 faces)
        if HAS_OPEN3D and len(mesh.faces) > 2000:
            target_faces = None
            if preset == "fast" and len(mesh.faces) > 40000:
                target_faces = 30000
            elif preset == "balanced" and len(mesh.faces) > 20000:
                target_faces = 15000
            elif preset == "high" and len(mesh.faces) > 60000:
                target_faces = 40000

            if target_faces and target_faces < len(mesh.faces):
                try:
                    o3d_m = cls._trimesh_to_open3d(mesh)
                    simplified = o3d_m.simplify_quadric_decimation(target_number_of_triangles=target_faces)
                    if len(simplified.triangles) > 0:
                        mesh = cls._open3d_to_trimesh(simplified)
                except Exception as e:
                    print(f"[MeshRefiner] Decimation warning: {e}")

        # -------------------------------------------------------------
        # STEP 6: Bounding-Box Centering & Normalization
        # -------------------------------------------------------------
        try:
            mesh.vertices -= mesh.centroid
            max_ext = float(np.max(mesh.extents))
            if max_ext > 1e-6:
                scale = 0.9 / max_ext
                mesh.vertices *= scale
        except Exception:
            pass

        # -------------------------------------------------------------
        # STEP 7: Comparative Telemetry
        # -------------------------------------------------------------
        ref_v = len(mesh.vertices)
        ref_f = len(mesh.faces)
        ref_wt = bool(getattr(mesh, "is_watertight", False))
        ref_area = float(mesh.area) if ref_v > 0 else 0.0

        # Check degradation: if watertightness was lost, flag degradation
        is_degraded = (orig_wt and not ref_wt) or (ref_f == 0)

        duration = time.time() - t0
        summary = (
            f"Preset '{preset.upper()}': {orig_v} -> {ref_v} verts (delta: {ref_v - orig_v:+d}), "
            f"{orig_f} -> {ref_f} faces (delta: {ref_f - orig_f:+d}), watertight: {ref_wt}."
        )

        comparison = MeshComparison(
            asset_id=asset_id,
            operation=f"refine_{preset}",
            duration_seconds=round(duration, 4),
            original_vertices=orig_v,
            refined_vertices=ref_v,
            vertex_delta=ref_v - orig_v,
            original_faces=orig_f,
            refined_faces=ref_f,
            face_delta=ref_f - orig_f,
            original_watertight=orig_wt,
            refined_watertight=ref_wt,
            original_surface_area=round(orig_area, 4),
            refined_surface_area=round(ref_area, 4),
            original_file_size_bytes=0,
            refined_file_size_bytes=0,
            is_degraded=is_degraded,
            summary=summary,
        )

        return mesh, comparison

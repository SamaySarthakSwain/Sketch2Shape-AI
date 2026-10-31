"""
3D Surface and Differential Geometry Analyzer Module
Inspects surface area, mathematical volume, normal orientations,
discrete curvature estimates, and surface roughness.
"""

from typing import Optional, Tuple
import numpy as np
import trimesh
from .geometry_metrics import SurfaceMetrics


class SurfaceAnalyzer:
    @staticmethod
    def analyze(mesh: trimesh.Trimesh) -> SurfaceMetrics:
        """
        Computes metric surface properties and curvature approximations.
        """
        if mesh is None or len(mesh.vertices) == 0:
            return SurfaceMetrics(
                surface_area=0.0,
                volume=None,
                is_volume_valid=False,
                normal_consistency=False,
                inverted_normals_count=0,
                mean_curvature_estimate=0.0,
                gaussian_curvature_estimate=0.0,
                surface_roughness_std=0.0,
            )

        # 1. Surface Area
        try:
            surface_area = float(mesh.area)
        except Exception:
            surface_area = 0.0

        # 2. Mathematical Volume
        is_watertight = bool(getattr(mesh, "is_watertight", False))
        volume: Optional[float] = None
        is_volume_valid = False

        if is_watertight:
            try:
                v = float(mesh.volume)
                if not np.isnan(v) and v > 0:
                    volume = round(v, 6)
                    is_volume_valid = True
            except Exception:
                volume = None
                is_volume_valid = False

        # 3. Normal Consistency & Inversion Check
        normal_consistency = bool(getattr(mesh, "is_winding_consistent", False))
        inverted_normals_count = 0

        try:
            # Check face normals relative to centroid
            centroid = mesh.centroid
            face_centers = mesh.triangles_center
            face_normals = mesh.face_normals

            vecs = face_centers - centroid
            dists = np.linalg.norm(vecs, axis=1, keepdims=True)
            dists = np.maximum(dists, 1e-6)
            radial_dirs = vecs / dists

            # Dot product with face normal
            dots = np.sum(face_normals * radial_dirs, axis=1)
            # If pointing towards centroid, considered inverted
            inverted_normals_count = int(np.sum(dots < -0.1))
        except Exception:
            inverted_normals_count = 0

        # 4. Curvature & Roughness Estimates
        mean_curv = 0.0
        gauss_curv = 0.0
        roughness_std = 0.0

        try:
            # Discrete Gaussian Curvature via angle defect: 2*pi - sum(angles_at_v)
            # Use trimesh angles
            angles = mesh.face_angles
            angles_flat = angles.reshape(-1)
            vert_indices = mesh.faces.reshape(-1)
            angle_sums = np.bincount(vert_indices, weights=angles_flat, minlength=len(mesh.vertices))
            defects = 2.0 * np.pi - angle_sums
            gauss_curv = float(np.mean(np.abs(defects)))
        except Exception:
            gauss_curv = 0.0

        try:
            # Mean curvature estimate via Laplacian vertex displacement
            if hasattr(trimesh.smoothing, "laplacian_calculation"):
                lap, _ = trimesh.smoothing.laplacian_calculation(mesh)
                lap_coords = lap.dot(mesh.vertices)
                displacements = np.linalg.norm(lap_coords, axis=1)
                mean_curv = float(np.mean(displacements))
                roughness_std = float(np.std(displacements))
            else:
                # Fallback dihedral angles
                dihedrals = mesh.face_adjacency_angles
                if len(dihedrals) > 0:
                    roughness_std = float(np.std(dihedrals))
                    mean_curv = float(np.mean(dihedrals))
        except Exception:
            mean_curv = 0.0
            roughness_std = 0.0

        return SurfaceMetrics(
            surface_area=round(surface_area, 6),
            volume=volume,
            is_volume_valid=is_volume_valid,
            normal_consistency=normal_consistency,
            inverted_normals_count=inverted_normals_count,
            mean_curvature_estimate=round(mean_curv, 4),
            gaussian_curvature_estimate=round(gauss_curv, 4),
            surface_roughness_std=round(roughness_std, 4),
        )

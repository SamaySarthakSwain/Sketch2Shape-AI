"""
3D Spatial and Symmetry Analyzer Module
Measures bounding-box extents, aspect ratios, principal inertia axes,
and reflection symmetry scores across canonical coordinate planes.
"""

from typing import Dict, Any, List
import numpy as np
from scipy.spatial import KDTree
import trimesh
from .geometry_metrics import SpatialMetrics


class SymmetryAnalyzer:
    @staticmethod
    def _compute_reflection_symmetry(vertices: np.ndarray, axis: int) -> float:
        """
        Calculates reflection symmetry across plane perpendicular to given axis (0=X, 1=Y, 2=Z).
        Uses KDTree nearest neighbor distances normalized by bounding diagonal.
        Returns score in [0.0, 1.0], where 1.0 is perfectly symmetric.
        """
        if len(vertices) < 4:
            return 0.0

        reflected = vertices.copy()
        reflected[:, axis] *= -1.0

        tree = KDTree(vertices)
        dists, _ = tree.query(reflected, k=1)

        diag = np.linalg.norm(np.ptp(vertices, axis=0))
        if diag <= 1e-6:
            return 1.0

        # Mean normalized distance
        norm_mean_dist = np.mean(dists) / diag
        # Exponential falloff: score = exp(-5 * norm_mean_dist)
        score = float(np.clip(np.exp(-6.0 * norm_mean_dist), 0.0, 1.0))
        return round(score, 4)

    @classmethod
    def analyze(cls, mesh: trimesh.Trimesh) -> SpatialMetrics:
        """
        Extracts spatial bounding boxes, aspect ratios, and plane symmetries.
        """
        if mesh is None or len(mesh.vertices) == 0:
            return SpatialMetrics(
                bounding_box_min=[0.0, 0.0, 0.0],
                bounding_box_max=[0.0, 0.0, 0.0],
                dimensions_xyz=[0.0, 0.0, 0.0],
                aspect_ratios={"xy": 1.0, "zy": 1.0, "xz": 1.0},
                center_of_mass=[0.0, 0.0, 0.0],
                principal_extents=[0.0, 0.0, 0.0],
                approximate_symmetry_scores={"x_plane": 0.0, "y_plane": 0.0, "z_plane": 0.0},
            )

        # 1. Bounding Box & Dimensions
        bounds = mesh.bounds
        b_min = bounds[0].tolist()
        b_max = bounds[1].tolist()
        extents = (bounds[1] - bounds[0]).tolist()

        dx = max(extents[0], 1e-6)
        dy = max(extents[1], 1e-6)
        dz = max(extents[2], 1e-6)

        aspect_ratios = {
            "xy": round(dx / dy, 4),
            "zy": round(dz / dy, 4),
            "xz": round(dx / dz, 4),
        }

        # 2. Center of Mass & Centroid
        try:
            com = mesh.center_mass.tolist() if getattr(mesh, "is_watertight", False) else mesh.centroid.tolist()
        except Exception:
            com = mesh.centroid.tolist()

        # 3. Principal Extents
        try:
            # SVD or PCA on centered vertices
            centered = mesh.vertices - mesh.centroid
            _, s, _ = np.linalg.svd(centered, full_matrices=False)
            principal_extents = (s / np.sqrt(len(mesh.vertices))).tolist()
        except Exception:
            principal_extents = extents

        # 4. Approximate Symmetry across X=0 (sagittal), Y=0 (axial), Z=0 (coronal)
        centered_v = mesh.vertices - mesh.centroid
        sym_x = cls._compute_reflection_symmetry(centered_v, axis=0)  # Left-Right
        sym_y = cls._compute_reflection_symmetry(centered_v, axis=1)  # Top-Bottom
        sym_z = cls._compute_reflection_symmetry(centered_v, axis=2)  # Front-Back

        return SpatialMetrics(
            bounding_box_min=[round(x, 4) for x in b_min],
            bounding_box_max=[round(x, 4) for x in b_max],
            dimensions_xyz=[round(x, 4) for x in extents],
            aspect_ratios=aspect_ratios,
            center_of_mass=[round(x, 4) for x in com],
            principal_extents=[round(x, 4) for x in principal_extents],
            approximate_symmetry_scores={
                "x_plane": sym_x,
                "y_plane": sym_y,
                "z_plane": sym_z,
            },
        )

"""
3D Connected Component and Structural Anomaly Analyzer Module
Detects isolated shards, thin structures, unexpected protrusions,
and disconnected parts.
"""

from typing import List, Tuple
import numpy as np
import trimesh
from .geometry_metrics import StructuralMetrics


class ComponentAnalyzer:
    @staticmethod
    def analyze(mesh: trimesh.Trimesh) -> StructuralMetrics:
        """
        Inspects multi-body component distribution, floating fragments,
        and extreme geometric outliers.
        """
        if mesh is None or len(mesh.vertices) == 0:
            return StructuralMetrics(
                component_sizes=[],
                isolated_fragments_count=0,
                has_unexpected_protrusions=False,
                max_protrusion_distance=0.0,
                thin_structures_detected=False,
            )

        total_faces = len(mesh.faces)
        total_verts = len(mesh.vertices)

        # 1. Connected components and sizes
        try:
            sub_meshes = mesh.split(only_watertight=False)
            component_sizes = [len(m.faces) for m in sub_meshes]
            component_sizes.sort(reverse=True)
        except Exception:
            sub_meshes = [mesh]
            component_sizes = [total_faces]

        # 2. Isolated fragments (components with < 3% of total faces and < 50 faces)
        isolated_fragments = 0
        if len(sub_meshes) > 1:
            for sm in sub_meshes[1:]:  # Largest component is index 0
                if len(sm.faces) < max(10, int(0.03 * total_faces)):
                    isolated_fragments += 1

        # 3. Protrusion Analysis (radial distance outliers)
        has_protrusions = False
        max_dist = 0.0
        try:
            dists = np.linalg.norm(mesh.vertices - mesh.centroid, axis=1)
            max_dist = float(np.max(dists))
            q75, q25 = np.percentile(dists, [75, 25])
            iqr = q75 - q25
            outlier_threshold = q75 + 3.0 * iqr
            if max_dist > outlier_threshold and (np.sum(dists > outlier_threshold) < 0.02 * total_verts):
                has_protrusions = True
        except Exception:
            has_protrusions = False
            max_dist = 0.0

        # 4. Thin structure detection
        extents = mesh.extents
        max_extent = max(extents) if len(extents) > 0 else 1.0
        min_extent = min(extents) if len(extents) > 0 else 0.0
        thin_detected = (min_extent / max(max_extent, 1e-6)) < 0.04

        return StructuralMetrics(
            component_sizes=component_sizes,
            isolated_fragments_count=isolated_fragments,
            has_unexpected_protrusions=has_protrusions,
            max_protrusion_distance=round(max_dist, 4),
            thin_structures_detected=thin_detected,
        )

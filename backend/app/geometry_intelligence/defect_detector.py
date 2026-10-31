"""
3D Mesh Defect Detector Module
Identifies concrete geometric, topological, and coordinate anomalies.
"""

from typing import List
import numpy as np
import trimesh
from .geometry_metrics import (
    TopologyMetrics,
    SurfaceMetrics,
    StructuralMetrics,
    DefectReport,
)


class DefectDetector:
    @staticmethod
    def detect(
        mesh: trimesh.Trimesh,
        topology: TopologyMetrics,
        surface: SurfaceMetrics,
        structural: StructuralMetrics,
    ) -> DefectReport:
        """
        Aggregates anomaly flags and builds an interpretable defect report.
        """
        defect_list: List[str] = []

        # 1. Non-finite coordinates (NaN / Inf)
        non_finite = 0
        if mesh is not None and len(mesh.vertices) > 0:
            nan_verts = np.isnan(mesh.vertices).any(axis=1)
            inf_verts = np.isinf(mesh.vertices).any(axis=1)
            non_finite = int(np.sum(nan_verts | inf_verts))
            if non_finite > 0:
                defect_list.append(f"Non-finite vertex coordinates: {non_finite} vertices contain NaN or Inf.")

        # 2. Non-manifold edges
        if topology.non_manifold_edges_count > 0:
            defect_list.append(
                f"Non-manifold geometry: {topology.non_manifold_edges_count} edges share more than 2 faces."
            )

        # 3. Open boundaries / non-watertight holes
        if not topology.is_watertight:
            defect_list.append(
                f"Open mesh boundary: {topology.boundary_edges_count} boundary edges detected (mesh is not watertight)."
            )

        # 4. Degenerate faces
        if topology.degenerate_faces_count > 0:
            defect_list.append(
                f"Degenerate faces: {topology.degenerate_faces_count} triangles have zero area or duplicate vertex indices."
            )

        # 5. Duplicate vertices
        if topology.duplicate_vertices_count > 0:
            defect_list.append(
                f"Redundant vertices: {topology.duplicate_vertices_count} duplicate coincident vertex coordinates detected."
            )

        # 6. Isolated shards
        if structural.isolated_fragments_count > 0:
            defect_list.append(
                f"Isolated fragments: {structural.isolated_fragments_count} floating disconnected components detected."
            )

        # 7. Inconsistent or inverted normals
        unoriented_normals = not surface.normal_consistency or (surface.inverted_normals_count > 0.2 * topology.face_count)
        if unoriented_normals:
            defect_list.append(
                f"Normal orientation defect: Inconsistent face winding or {surface.inverted_normals_count} inverted normals."
            )

        # 8. Extreme protrusions
        if structural.has_unexpected_protrusions:
            defect_list.append(
                f"Unexpected protrusion: Geometric spike detected at distance {structural.max_protrusion_distance:.2f}."
            )

        has_defects = len(defect_list) > 0

        return DefectReport(
            has_defects=has_defects,
            defect_count=len(defect_list),
            non_manifold_edges=topology.non_manifold_edges_count,
            boundary_holes=topology.boundary_edges_count,
            degenerate_triangles=topology.degenerate_faces_count,
            duplicate_vertices=topology.duplicate_vertices_count,
            isolated_fragments=structural.isolated_fragments_count,
            non_finite_coordinates=non_finite,
            unoriented_normals=unoriented_normals,
            defect_list=defect_list,
        )

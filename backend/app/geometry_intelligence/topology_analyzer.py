"""
3D Topology Analyzer Module
Inspects fundamental topological properties:
- Manifoldness, boundary loops, non-manifold edges
- Euler characteristic, genus, connected components
- Degenerate faces and duplicate vertices
"""

from typing import Dict, Any, Tuple
import numpy as np
import trimesh
from .geometry_metrics import TopologyMetrics


class TopologyAnalyzer:
    @staticmethod
    def analyze(mesh: trimesh.Trimesh) -> TopologyMetrics:
        """
        Computes exact topological invariants and defect counts.
        """
        if mesh is None or len(mesh.vertices) == 0:
            return TopologyMetrics(
                vertex_count=0,
                face_count=0,
                edge_count=0,
                is_watertight=False,
                is_volume=False,
                euler_characteristic=0,
                connected_components=0,
                boundary_edges_count=0,
                non_manifold_edges_count=0,
                duplicate_vertices_count=0,
                degenerate_faces_count=0,
                is_manifold=False,
            )

        v_count = len(mesh.vertices)
        f_count = len(mesh.faces)

        # Unique edges
        edges = mesh.edges_unique
        e_count = len(edges) if edges is not None else 0

        # Watertight & volume
        is_watertight = bool(getattr(mesh, "is_watertight", False))
        is_volume = bool(getattr(mesh, "is_volume", False))

        # Euler characteristic: Chi = V - E + F
        euler = bool(getattr(mesh, "euler_number", None))
        euler_char = int(mesh.euler_number) if hasattr(mesh, "euler_number") else (v_count - e_count + f_count)

        # Connected components
        try:
            components = len(mesh.split(only_watertight=False))
        except Exception:
            components = 1

        # Boundary edges (edges shared by only 1 face)
        try:
            # trimesh edges_sorted
            edge_face_counts = mesh.edges_unique_inverse
            unique_edges = mesh.edges_unique
            # Count occurrences of each unique edge in mesh.edges
            counts = np.bincount(mesh.edges_unique_inverse)
            boundary_edges_count = int(np.sum(counts == 1))
            non_manifold_edges_count = int(np.sum(counts > 2))
        except Exception:
            boundary_edges_count = 0
            non_manifold_edges_count = 0

        # Duplicate vertices count
        try:
            # Compare unique vertices vs total
            _, unique_indices = np.unique(np.round(mesh.vertices, decimals=6), axis=0, return_index=True)
            duplicate_vertices_count = int(v_count - len(unique_indices))
        except Exception:
            duplicate_vertices_count = 0

        # Degenerate faces count
        try:
            # Faces with duplicate vertices or zero area
            f = mesh.faces
            dup_face_verts = (f[:, 0] == f[:, 1]) | (f[:, 1] == f[:, 2]) | (f[:, 2] == f[:, 0])
            area = mesh.area_faces
            zero_area = area <= 1e-12
            degenerate_faces_count = int(np.sum(dup_face_verts | zero_area))
        except Exception:
            degenerate_faces_count = 0

        is_manifold = (non_manifold_edges_count == 0) and (duplicate_vertices_count == 0)

        return TopologyMetrics(
            vertex_count=v_count,
            face_count=f_count,
            edge_count=e_count,
            is_watertight=is_watertight,
            is_volume=is_volume,
            euler_characteristic=euler_char,
            connected_components=components,
            boundary_edges_count=boundary_edges_count,
            non_manifold_edges_count=non_manifold_edges_count,
            duplicate_vertices_count=duplicate_vertices_count,
            degenerate_faces_count=degenerate_faces_count,
            is_manifold=is_manifold,
        )

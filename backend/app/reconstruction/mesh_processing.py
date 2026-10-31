"""
Mesh Processing and Post-Extraction Optimization Module
Applies mesh repair, normal realignment, quadric decimation, and canonical coordinate normalization.
"""

import numpy as np
import trimesh


class MeshProcessor:
    """
    Processes and cleans raw extracted 3D meshes before export.
    """
    @staticmethod
    def clean_and_repair(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
        """Removes degenerate faces, duplicate vertices, and unreferenced vertices."""
        m = mesh.copy()
        try:
            m.update_faces(m.nondegenerate_faces())
            m.update_faces(m.unique_faces())
            m.remove_unreferenced_vertices()
            trimesh.repair.fix_normals(m)
            trimesh.repair.fix_inversion(m)
        except Exception as e:
            print(f"[MeshProcessor] Warning during repair: {e}")
        return m

    @staticmethod
    def center_and_normalize(mesh: trimesh.Trimesh, target_scale: float = 0.9) -> trimesh.Trimesh:
        """Centers mesh at coordinate origin (0, 0, 0) and isotropically scales maximum dimension to target_scale."""
        m = mesh.copy()
        bounds = m.bounds
        if bounds is None or len(m.vertices) == 0:
            return m

        # Translate center of bounding box to origin
        center = (bounds[0] + bounds[1]) / 2.0
        m.vertices -= center

        # Isotropic scale so max bounding extent == target_scale
        extents = bounds[1] - bounds[0]
        max_extent = np.max(extents)
        if max_extent > 1e-6:
            scale_factor = target_scale / max_extent
            m.vertices *= scale_factor

        return m

    @staticmethod
    def decimate(mesh: trimesh.Trimesh, max_faces: int = 60000) -> trimesh.Trimesh:
        """
        Decimates large meshes if face count exceeds max_faces, preserving topology
        and keeping WebGL Three.js interactive framerates smooth.
        """
        m = mesh.copy()
        if len(m.faces) > max_faces:
            try:
                # Use trimesh quadric simplification
                m = m.simplify_quadric_decimation(max_faces)
            except Exception as e:
                print(f"[MeshProcessor] Simplification notice: {e}")
        return m

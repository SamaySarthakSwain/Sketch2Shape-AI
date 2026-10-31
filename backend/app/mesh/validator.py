"""
Mesh Validation and Repair Engine for Sketch2Shape AI
Performs topological analysis (watertightness, manifoldness, Euler characteristic,
normal consistency) and geometry healing/normalization.
"""

import trimesh
import numpy as np
from typing import Dict, Any, Tuple


class MeshValidator:
    def __init__(self, target_faces: int = 20000):
        self.target_faces = target_faces

    def validate(self, mesh: trimesh.Trimesh) -> Dict[str, Any]:
        """Performs comprehensive topological and geometrical validation on a mesh."""
        if not isinstance(mesh, trimesh.Trimesh):
            raise TypeError("Expected trimesh.Trimesh instance")

        v_count = len(mesh.vertices)
        f_count = len(mesh.faces)
        e_count = len(mesh.edges_unique)

        # Euler characteristic: V - E + F (should be 2 for genus-0 sphere-like watertight manifold)
        euler_char = v_count - e_count + f_count

        # Watertight & Manifold checks
        is_watertight = bool(mesh.is_watertight)
        is_winding = bool(mesh.is_winding_consistent)
        
        # Volume
        volume = float(mesh.volume) if is_watertight else 0.0
        area = float(mesh.area)

        # Degenerate faces check
        try:
            non_degenerate = trimesh.triangles.nondegenerate(mesh.triangles)
            degenerate_count = int(np.sum(~non_degenerate))
        except Exception:
            degenerate_count = 0

        # Boundary edges (naked edges)
        boundary_edges = 0
        try:
            boundary_edges = len(mesh.outline().entities) if not is_watertight else 0
        except Exception:
            pass

        # Extents & bounding box
        bounds = mesh.bounds
        extents = mesh.extents.tolist() if bounds is not None else [0, 0, 0]

        # Overall health score [0 - 100]
        health_score = 100
        if not is_watertight:
            health_score -= 30
        if not is_winding:
            health_score -= 20
        if degenerate_count > 0:
            health_score -= min(20, degenerate_count)
        health_score = max(0, health_score)

        return {
            "vertex_count": v_count,
            "face_count": f_count,
            "edge_count": e_count,
            "euler_characteristic": euler_char,
            "is_watertight": is_watertight,
            "is_winding_consistent": is_winding,
            "boundary_loops": boundary_edges,
            "degenerate_faces": degenerate_count,
            "surface_area": round(area, 4),
            "volume": round(volume, 4),
            "bounds": {
                "min": bounds[0].tolist() if bounds is not None else [0, 0, 0],
                "max": bounds[1].tolist() if bounds is not None else [0, 0, 0],
                "extents": [round(x, 4) for x in extents]
            },
            "health_score": health_score,
            "is_valid_for_3d_print": is_watertight and health_score >= 80
        }

    def repair_and_normalize(self, mesh: trimesh.Trimesh) -> Tuple[trimesh.Trimesh, Dict[str, Any]]:
        """
        Repairs mesh defects, ensures outward consistent normals,
        decimates if oversized, centers at origin, and normalizes scale.
        """
        mesh_copy = mesh.copy()

        # 1. Process mesh: cleans unreferenced vertices, duplicate faces, and degenerate faces
        mesh_copy.process(validate=True)

        # 2. Fix winding order & normals
        trimesh.repair.fix_normals(mesh_copy)
        trimesh.repair.fix_inversion(mesh_copy)

        # 3. Fill small holes if any
        try:
            trimesh.repair.fill_holes(mesh_copy)
        except Exception:
            pass

        # 4. Decimate if face count exceeds target limit for smooth browser rendering
        if len(mesh_copy.faces) > self.target_faces:
            try:
                import open3d as o3d
                o3d_m = o3d.geometry.TriangleMesh()
                o3d_m.vertices = o3d.utility.Vector3dVector(mesh_copy.vertices.astype(np.float64))
                o3d_m.triangles = o3d.utility.Vector3iVector(mesh_copy.faces.astype(np.int32))
                simp = o3d_m.simplify_quadric_decimation(target_number_of_triangles=self.target_faces)
                if len(simp.triangles) > 0:
                    mesh_copy = trimesh.Trimesh(vertices=np.asarray(simp.vertices), faces=np.asarray(simp.triangles), process=False)
            except Exception:
                try:
                    mesh_copy = mesh_copy.simplify_quadric_decimation(face_count=self.target_faces)
                except Exception:
                    pass

        # 5. Center at origin and normalize to fit inside [-1.0, 1.0] bounding sphere/box
        mesh_copy.vertices -= mesh_copy.center_mass if mesh_copy.is_watertight else mesh_copy.centroid
        max_extent = max(mesh_copy.extents)
        if max_extent > 0:
            mesh_copy.vertices *= (2.0 / max_extent)

        # Re-validate
        validation_report = self.validate(mesh_copy)

        return mesh_copy, validation_report

"""
Mesh Topology and Geometric Validation Module
Validates generated 3D meshes using Trimesh for watertightness, Euler characteristic,
non-finite vertices, degenerate faces, connected components, and volumetric integrity.
"""

import os
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import numpy as np
import trimesh


class MeshValidator:
    """
    Comprehensive geometric and topological validator for 3D meshes.
    """
    @classmethod
    def validate_trimesh(cls, mesh: trimesh.Trimesh) -> Dict[str, Any]:
        """Validates an in-memory Trimesh object."""
        if mesh is None or len(mesh.vertices) == 0 or len(mesh.faces) == 0:
            return {
                "is_valid": False,
                "error": "Mesh is empty (0 vertices or 0 faces)",
                "vertices": 0,
                "faces": 0,
                "is_watertight": False,
                "euler_characteristic": 0,
                "components": 0,
                "volume": 0.0,
                "surface_area": 0.0,
                "bounds": None
            }

        v = len(mesh.vertices)
        f = len(mesh.faces)

        # 1. Non-finite coordinates check (NaN / Inf)
        has_non_finite = not np.all(np.isfinite(mesh.vertices)) or not np.all(np.isfinite(mesh.faces))
        if has_non_finite:
            return {
                "is_valid": False,
                "error": "Mesh contains non-finite coordinates (NaN or Inf)",
                "vertices": v,
                "faces": f,
                "is_watertight": False
            }

        # 2. Topology checks
        is_watertight = bool(mesh.is_watertight)
        euler_char = int(mesh.euler_number)
        
        # 3. Degenerate faces and duplicates
        degenerate_faces = 0
        try:
            areas = mesh.area_faces
            degenerate_faces = int(np.sum(areas <= 1e-9))
        except Exception:
            pass

        duplicate_vertices = 0
        try:
            unique_verts = len(np.unique(mesh.vertices, axis=0))
            duplicate_vertices = v - unique_verts
        except Exception:
            pass

        # 4. Connected components
        try:
            components = len(mesh.split(only_watertight=False))
        except Exception:
            components = 1

        # 5. Physical bounds & dimensions
        bounds = mesh.bounds
        extents = (bounds[1] - bounds[0]).tolist() if bounds is not None else [0, 0, 0]
        
        # 6. Volume and Surface Area
        surface_area = round(float(mesh.area), 4)
        volume = round(float(mesh.volume), 4) if is_watertight else None

        return {
            "is_valid": True,
            "error": None,
            "vertices": v,
            "faces": f,
            "is_watertight": is_watertight,
            "euler_characteristic": euler_char,
            "components": components,
            "degenerate_faces": degenerate_faces,
            "duplicate_vertices": duplicate_vertices,
            "surface_area": surface_area,
            "volume": volume,
            "dimensions_xyz": [round(x, 4) for x in extents],
            "bounding_box_min": [round(x, 4) for x in bounds[0].tolist()] if bounds is not None else None,
            "bounding_box_max": [round(x, 4) for x in bounds[1].tolist()] if bounds is not None else None,
        }

    @classmethod
    def validate_file(cls, file_path: str) -> Dict[str, Any]:
        """Loads a mesh file from disk and validates its geometry."""
        p = Path(file_path)
        if not p.exists() or p.stat().st_size == 0:
            return {
                "is_valid": False,
                "error": f"File does not exist or is empty: {file_path}",
                "vertices": 0,
                "faces": 0,
                "is_watertight": False
            }

        try:
            loaded = trimesh.load(str(p), process=False)
            if isinstance(loaded, trimesh.Scene):
                # Flatten scene into single mesh if necessary
                if len(loaded.geometry) == 0:
                    return {"is_valid": False, "error": "Scene contains no geometries."}
                mesh = trimesh.util.concatenate([g for g in loaded.geometry.values() if isinstance(g, trimesh.Trimesh)])
            elif isinstance(loaded, trimesh.Trimesh):
                mesh = loaded
            else:
                return {"is_valid": False, "error": f"Unsupported object loaded: {type(loaded)}"}

            report = cls.validate_trimesh(mesh)
            report["file_path"] = str(p)
            report["file_size_bytes"] = p.stat().st_size
            return report
        except Exception as e:
            return {
                "is_valid": False,
                "error": f"Failed to load mesh with Trimesh: {str(e)}",
                "vertices": 0,
                "faces": 0,
                "is_watertight": False
            }

    validate_mesh = validate_file

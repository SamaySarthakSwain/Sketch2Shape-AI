"""
Multi-Format 3D Export Manager Module
Exports 3D meshes to binary GLTF/GLB (primary) and Wavefront OBJ + MTL (secondary).
Strictly reopens every exported asset with Trimesh to guarantee disk file validity.
"""

import os
from pathlib import Path
from typing import Dict, Any, List
import trimesh

from .mesh_validation import MeshValidator


class ExportManager:
    """
    Manages multi-format 3D export and verification.
    """
    @classmethod
    def export_all(
        cls,
        mesh: trimesh.Trimesh,
        output_dir: str,
        base_filename: str,
        formats: List[str] = None
    ) -> Dict[str, str]:
        """
        Exports the mesh into the requested formats (default: ['glb', 'obj']).
        Returns a dictionary mapping format names to their absolute file paths.
        """
        if formats is None:
            formats = ["glb", "obj"]

        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        exported_paths = {}

        # 1. Primary: Binary GLTF (.glb)
        if "glb" in formats:
            glb_file = out_path / f"{base_filename}.glb"
            glb_bytes = mesh.export(file_type="glb")
            with open(glb_file, "wb") as f:
                f.write(glb_bytes)
            
            # Reopen and strictly verify
            val = MeshValidator.validate_file(str(glb_file))
            if not val["is_valid"]:
                raise RuntimeError(f"GLB export failed integrity check: {val.get('error')}")
            exported_paths["glb"] = str(glb_file)

        # 2. Secondary: Wavefront OBJ (.obj + .mtl)
        if "obj" in formats:
            obj_file = out_path / f"{base_filename}.obj"
            obj_content = mesh.export(file_type="obj")
            with open(obj_file, "w", encoding="utf-8", errors="replace") as f:
                f.write(obj_content)

            # Reopen and strictly verify
            val = MeshValidator.validate_file(str(obj_file))
            if not val["is_valid"]:
                raise RuntimeError(f"OBJ export failed integrity check: {val.get('error')}")
            exported_paths["obj"] = str(obj_file)

        return exported_paths

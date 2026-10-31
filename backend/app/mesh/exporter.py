"""
Mesh Exporter for Sketch2Shape AI
Supports exporting 3D meshes to GLB (binary glTF for Three.js), OBJ, STL (3D printing), and PLY.
"""

import io
import trimesh
from pathlib import Path
from typing import Dict, Any, Union


class MeshExporter:
    SUPPORTED_FORMATS = ["glb", "obj", "stl", "ply"]

    @staticmethod
    def export_bytes(mesh: trimesh.Trimesh, format: str = "glb") -> bytes:
        """Exports a Trimesh object directly to in-memory bytes."""
        format_lower = format.lower().strip()
        if format_lower not in MeshExporter.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported export format '{format}'. Choose from {MeshExporter.SUPPORTED_FORMATS}")

        # Ensure correct file type argument
        file_type = "glb" if format_lower in ["glb", "gltf"] else format_lower
        result = mesh.export(file_type=file_type)

        if isinstance(result, str):
            return result.encode("utf-8")
        return result

    @staticmethod
    def export_to_file(mesh: trimesh.Trimesh, output_path: Union[str, Path], format: str = "glb") -> str:
        """Saves a mesh to a specified destination file."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        raw_bytes = MeshExporter.export_bytes(mesh, format=format)
        with open(path, "wb") as f:
            f.write(raw_bytes)
        return str(path.resolve())

    @staticmethod
    def export_all_formats(mesh: trimesh.Trimesh, base_path: Union[str, Path], file_stem: str) -> Dict[str, str]:
        """Exports the mesh in all 4 primary formats (GLB, OBJ, STL, PLY) and returns file paths."""
        base_dir = Path(base_path)
        base_dir.mkdir(parents=True, exist_ok=True)
        paths = {}
        for fmt in MeshExporter.SUPPORTED_FORMATS:
            target_file = base_dir / f"{file_stem}.{fmt}"
            MeshExporter.export_to_file(mesh, target_file, format=fmt)
            paths[fmt] = str(target_file.resolve())
        return paths

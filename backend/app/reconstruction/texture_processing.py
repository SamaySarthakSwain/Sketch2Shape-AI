"""
Texture and Material Analysis and Processing Module
Inspects vertex colors, UV parameterization, texture maps, and PBR material definitions.
Distinguishes point vertex colors from continuous UV texture maps.
"""

from typing import Dict, Any, Optional
import numpy as np
import trimesh


class TextureProcessor:
    """
    Analyzes and formats material and color properties for 3D meshes.
    """
    @staticmethod
    def inspect_texture(mesh_or_path: Any) -> Dict[str, Any]:
        """
        Convenience wrapper to inspect texture given either a Trimesh object or file path.
        """
        from pathlib import Path
        if isinstance(mesh_or_path, (str, Path)):
            m = trimesh.load(str(mesh_or_path), force="mesh")
        else:
            m = mesh_or_path
        return TextureProcessor.inspect_materials(m)

    @staticmethod
    def inspect_materials(mesh: trimesh.Trimesh) -> Dict[str, Any]:
        """
        Examines visual attributes of a mesh:
        - Vertex colors (point-wise RGBA)
        - UV coordinates (2D texture mapping)
        - Texture map image (raster diffuse / albedo)
        - Material definition (PBR / SimpleMaterial)
        """
        has_vertex_colors = False
        has_uv = False
        has_texture_image = False
        material_type = "none"

        # 1. Check Vertex Colors
        if hasattr(mesh.visual, "vertex_colors") and mesh.visual.vertex_colors is not None:
            vc = mesh.visual.vertex_colors
            if len(vc) == len(mesh.vertices):
                # Verify they aren't all uniform default gray
                color_var = np.var(vc[:, :3])
                if color_var > 1e-4:
                    has_vertex_colors = True

        # 2. Check UV Coordinates and Texture Maps
        if hasattr(mesh.visual, "uv") and mesh.visual.uv is not None:
            if len(mesh.visual.uv) == len(mesh.vertices) or len(mesh.visual.uv) > 0:
                has_uv = True

        if hasattr(mesh.visual, "material") and mesh.visual.material is not None:
            mat = mesh.visual.material
            material_type = type(mat).__name__
            if hasattr(mat, "image") and mat.image is not None:
                has_texture_image = True

        return {
            "has_vertex_colors": has_vertex_colors,
            "has_uv_coordinates": has_uv,
            "has_texture_image": has_texture_image,
            "is_textured": has_texture_image,
            "material_type": material_type,
            "texture_mode": "diffuse_texture_map" if has_texture_image else ("vertex_color_interpolation" if has_vertex_colors else "untextured_clay")
        }

"""
Texture and Material Intelligence Module
Inspects vertex colors, UV parameterization, texture maps, and PBR material definitions.
Distinguishes point vertex colors from continuous UV texture maps.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import numpy as np
from PIL import Image
import trimesh
from .geometry_metrics import TextureMetrics


class TextureAnalyzer:
    @staticmethod
    def analyze(mesh_or_path: Any) -> TextureMetrics:
        """
        Examines visual attributes of a mesh:
        - Vertex colors (point-wise RGBA)
        - UV coordinates (2D texture mapping)
        - Texture map image (raster diffuse / albedo)
        - Material definition (PBR / SimpleMaterial)
        """
        if isinstance(mesh_or_path, (str, Path)):
            try:
                mesh = trimesh.load(str(mesh_or_path), force="mesh")
            except Exception:
                return TextureMetrics(
                    has_vertex_colors=False,
                    has_uv_coordinates=False,
                    has_texture_image=False,
                    texture_resolution=None,
                    material_type="unreadable",
                    texture_mode="untextured_clay",
                    texture_status_message="Failed to load file for material inspection.",
                )
        else:
            mesh = mesh_or_path

        if mesh is None or len(mesh.vertices) == 0:
            return TextureMetrics(
                has_vertex_colors=False,
                has_uv_coordinates=False,
                has_texture_image=False,
                texture_resolution=None,
                material_type="none",
                texture_mode="untextured_clay",
                texture_status_message="Empty mesh geometry; no material properties.",
            )

        has_vertex_colors = False
        has_uv = False
        has_texture_image = False
        texture_res: Optional[List[int]] = None
        material_type = "none"

        # 1. Check Vertex Colors
        if hasattr(mesh.visual, "vertex_colors") and mesh.visual.vertex_colors is not None:
            vc = mesh.visual.vertex_colors
            if len(vc) == len(mesh.vertices):
                # Verify non-trivial color variance
                color_var = float(np.var(vc[:, :3]))
                if color_var > 1e-4:
                    has_vertex_colors = True

        # 2. Check UV Coordinates
        if hasattr(mesh.visual, "uv") and mesh.visual.uv is not None:
            uv = mesh.visual.uv
            if len(uv) > 0 and len(uv) == len(mesh.vertices):
                has_uv = True

        # 3. Check Material & Texture Image
        if hasattr(mesh.visual, "material") and mesh.visual.material is not None:
            mat = mesh.visual.material
            material_type = type(mat).__name__
            if hasattr(mat, "image") and mat.image is not None:
                has_texture_image = True
                img = mat.image
                if hasattr(img, "size"):
                    texture_res = [img.size[0], img.size[1]]
                elif isinstance(img, np.ndarray):
                    texture_res = [int(img.shape[1]), int(img.shape[0])]

        # 4. Resolve Texture Mode & Status Message
        if has_texture_image and has_uv:
            texture_mode = "uv_mapped"
            status_msg = f"Fully textured with UV mapping (resolution: {texture_res[0]}x{texture_res[1]})."
        elif has_vertex_colors and not has_uv:
            texture_mode = "vertex_colored"
            status_msg = "Vertex-colored mesh; no conventional UV texture map detected."
        elif has_uv and not has_texture_image:
            texture_mode = "uv_without_texture"
            status_msg = "UV coordinates parameterized, but texture image is missing or unbound."
        else:
            texture_mode = "untextured_clay"
            status_msg = "Untextured clay sculpture; standard PBR diffuse lighting applied."

        return TextureMetrics(
            has_vertex_colors=has_vertex_colors,
            has_uv_coordinates=has_uv,
            has_texture_image=has_texture_image,
            texture_resolution=texture_res,
            material_type=material_type,
            texture_mode=texture_mode,
            texture_status_message=status_msg,
        )

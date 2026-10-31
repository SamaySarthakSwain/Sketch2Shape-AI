"""
PBR Texture Baking & Material Application Engine
Bakes high-resolution procedural PBR textures into standard glTF 2.0 PBR materials:
- Base Color Texture (Albedo)
- Normal Map (Tangent Space)
- Combined Metallic-Roughness Texture (glTF 2.0 standard: G=Roughness, B=Metallic)
- Ambient Occlusion Map
- Exports fully textured GLB and separate texture assets.
"""

from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np
from PIL import Image
import trimesh

from .pbr_material_library import PBRMaterialLibrary, PBRMaterialDef
from .pbr_texture_generator import PBRTextureGenerator
from .uv_unwrapper import UVUnwrapper


class PBRBaker:
    @classmethod
    def apply_pbr_textures(
        cls,
        mesh: trimesh.Trimesh,
        category: str,
        style: str = "realistic",
        material_override: Optional[str] = None,
        texture_resolution: int = 1024,
        uv_mode: str = "box",
        output_dir: Optional[str] = None,
        color_palette: Optional[Dict[str, Any]] = None
    ) -> Tuple[trimesh.Trimesh, Dict[str, str]]:
        """
        Takes an untextured mesh, unwraps UVs, generates PBR texture maps,
        applies glTF 2.0 PBR material, and optionally saves texture PNGs.
        If color_palette specifies custom or sketch-extracted colors,
        faithfully tints the base color and albedo texture to match.
        Returns:
            (textured_mesh, dict_of_saved_texture_paths)
        """
        # 1. Resolve material definition
        material_def = PBRMaterialLibrary.get_material_for_category(
            category=category,
            style=style,
            material_override=material_override
        )

        # 1b. Adapt base color to sketch / prompt color palette if colorful
        if color_palette:
            is_colorful = color_palette.get("is_colorful", False)
            prim_rgb = color_palette.get("primary_color_rgb")
            if prim_rgb and (is_colorful or not material_override):
                material_def.base_color_rgb = (int(prim_rgb[0]), int(prim_rgb[1]), int(prim_rgb[2]))
            sec_rgb = color_palette.get("secondary_color_rgb")
            if sec_rgb and (is_colorful or not material_override):
                material_def.secondary_color_rgb = (int(sec_rgb[0]), int(sec_rgb[1]), int(sec_rgb[2]))

        # 2. Select appropriate UV unwrapping mode based on category
        if category in ["vase", "bottle", "bowl", "cup", "mug", "coffee cup"]:
            chosen_uv_mode = "cylindrical"
        elif category in ["apple", "sphere"]:
            chosen_uv_mode = "spherical"
        else:
            chosen_uv_mode = uv_mode

        unwrapped_mesh = UVUnwrapper.generate_uvs(mesh, mode=chosen_uv_mode)

        # 3. Generate high-resolution PBR texture set
        tex_dir = (Path(output_dir) / "textures") if output_dir else None
        tex_set = PBRTextureGenerator.generate_pbr_set(
            material=material_def,
            resolution=texture_resolution,
            output_dir=str(tex_dir) if tex_dir else None
        )

        albedo_img = tex_set["albedo"]
        normal_img = tex_set["normal"]
        roughness_img = tex_set["roughness"]
        metallic_img = tex_set["metallic"]
        ao_img = tex_set["ao"]

        # 4. Construct glTF 2.0 Combined Metallic-Roughness image:
        # Red: Unused (or AO), Green: Roughness, Blue: Metallic
        r_arr = np.array(ao_img, dtype=np.uint8)
        g_arr = np.array(roughness_img, dtype=np.uint8)
        b_arr = np.array(metallic_img, dtype=np.uint8)
        mr_combined_arr = np.stack([r_arr, g_arr, b_arr], axis=2)
        mr_combined_img = Image.fromarray(mr_combined_arr, mode="RGB")

        if tex_dir:
            mr_combined_img.save(str(tex_dir / "metallic_roughness.png"))

        # 5. Create standard glTF PBRMaterial
        pbr_mat = trimesh.visual.material.PBRMaterial(
            name=material_def.name,
            baseColorTexture=albedo_img,
            metallicRoughnessTexture=mr_combined_img,
            normalTexture=normal_img,
            occlusionTexture=ao_img,
            roughnessFactor=material_def.roughness,
            metallicFactor=material_def.metallic,
            baseColorFactor=[
                material_def.base_color_rgb[0] / 255.0,
                material_def.base_color_rgb[1] / 255.0,
                material_def.base_color_rgb[2] / 255.0,
                1.0
            ]
        )

        # 6. Bind to mesh visual
        uvs = unwrapped_mesh.visual.uv
        unwrapped_mesh.visual = trimesh.visual.TextureVisuals(
            uv=uvs,
            image=albedo_img,
            material=pbr_mat
        )

        # Record paths of generated textures
        saved_paths = {}
        if tex_dir:
            for map_name in ["albedo", "normal", "roughness", "metallic", "ao"]:
                saved_paths[map_name] = str(tex_dir / f"{map_name}.png")
            saved_paths["metallic_roughness"] = str(tex_dir / "metallic_roughness.png")

        return unwrapped_mesh, saved_paths

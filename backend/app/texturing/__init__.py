"""
PBR Texturing and Material Synthesis Subsystem
"""

from .material_styles import VisualStyle, StyleModifier, STYLE_MODIFIERS
from .pbr_material_library import PBRMaterialLibrary, PBRMaterialDef, MATERIALS_DB, CATEGORY_MATERIAL_MAPPING
from .pbr_texture_generator import PBRTextureGenerator
from .uv_unwrapper import UVUnwrapper
from .pbr_baker import PBRBaker

__all__ = [
    "VisualStyle",
    "StyleModifier",
    "STYLE_MODIFIERS",
    "PBRMaterialLibrary",
    "PBRMaterialDef",
    "MATERIALS_DB",
    "CATEGORY_MATERIAL_MAPPING",
    "PBRTextureGenerator",
    "UVUnwrapper",
    "PBRBaker",
]

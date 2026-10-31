"""
Visual Material Styles and Presets
Defines aesthetic styling rules for PBR material generation.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Tuple


class VisualStyle(str, Enum):
    REALISTIC = "realistic"
    STYLIZED = "stylized"
    CARTOON = "cartoon"
    LOW_POLY = "low_poly"
    PRODUCT_RENDER = "product_render"
    FUTURISTIC = "futuristic"
    METALLIC = "metallic"
    MATTE = "matte"
    GLOSSY = "glossy"


@dataclass
class StyleModifier:
    name: str
    roughness_multiplier: float
    metallic_multiplier: float
    saturation_multiplier: float
    normal_strength: float
    color_shift: Tuple[float, float, float] = (1.0, 1.0, 1.0)


STYLE_MODIFIERS: Dict[str, StyleModifier] = {
    VisualStyle.REALISTIC.value: StyleModifier(
        name="Realistic",
        roughness_multiplier=1.0,
        metallic_multiplier=1.0,
        saturation_multiplier=1.0,
        normal_strength=1.0,
    ),
    VisualStyle.STYLIZED.value: StyleModifier(
        name="Stylized",
        roughness_multiplier=0.85,
        metallic_multiplier=0.7,
        saturation_multiplier=1.25,
        normal_strength=1.2,
    ),
    VisualStyle.CARTOON.value: StyleModifier(
        name="Cartoon",
        roughness_multiplier=0.9,
        metallic_multiplier=0.1,
        saturation_multiplier=1.4,
        normal_strength=0.3,
    ),
    VisualStyle.LOW_POLY.value: StyleModifier(
        name="Low-Poly",
        roughness_multiplier=0.8,
        metallic_multiplier=0.2,
        saturation_multiplier=1.1,
        normal_strength=0.0,
    ),
    VisualStyle.PRODUCT_RENDER.value: StyleModifier(
        name="Product Render",
        roughness_multiplier=0.6,
        metallic_multiplier=0.8,
        saturation_multiplier=1.05,
        normal_strength=0.8,
    ),
    VisualStyle.FUTURISTIC.value: StyleModifier(
        name="Futuristic",
        roughness_multiplier=0.3,
        metallic_multiplier=0.9,
        saturation_multiplier=0.9,
        normal_strength=1.3,
    ),
    VisualStyle.METALLIC.value: StyleModifier(
        name="Metallic",
        roughness_multiplier=0.25,
        metallic_multiplier=1.0,
        saturation_multiplier=0.95,
        normal_strength=0.7,
    ),
    VisualStyle.MATTE.value: StyleModifier(
        name="Matte",
        roughness_multiplier=1.4,
        metallic_multiplier=0.1,
        saturation_multiplier=0.95,
        normal_strength=0.5,
    ),
    VisualStyle.GLOSSY.value: StyleModifier(
        name="Glossy",
        roughness_multiplier=0.2,
        metallic_multiplier=0.4,
        saturation_multiplier=1.1,
        normal_strength=0.6,
    ),
}

"""
Intelligent PBR Material Library
Maps semantic object categories and user styling choices to physically based materials.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from .material_styles import VisualStyle, STYLE_MODIFIERS


@dataclass
class PBRMaterialDef:
    name: str
    display_name: str
    base_color_rgb: Tuple[int, int, int]
    roughness: float
    metallic: float
    pattern_type: str  # 'wood', 'leather', 'automotive', 'ceramic', 'organic', 'metal', 'fabric', 'rubber', 'solid'
    secondary_color_rgb: Optional[Tuple[int, int, int]] = None
    normal_detail_strength: float = 1.0


# Comprehensive library of physical PBR materials
MATERIALS_DB: Dict[str, PBRMaterialDef] = {
    # 1. Woods
    "natural_wood": PBRMaterialDef(
        name="natural_wood",
        display_name="Natural Oak Wood",
        base_color_rgb=(165, 115, 68),
        secondary_color_rgb=(120, 78, 42),
        roughness=0.65,
        metallic=0.0,
        pattern_type="wood",
        normal_detail_strength=1.2
    ),
    "dark_walnut": PBRMaterialDef(
        name="dark_walnut",
        display_name="Dark Walnut",
        base_color_rgb=(82, 52, 34),
        secondary_color_rgb=(54, 32, 19),
        roughness=0.55,
        metallic=0.0,
        pattern_type="wood",
        normal_detail_strength=1.1
    ),

    # 2. Leathers & Fabrics
    "leather_brown": PBRMaterialDef(
        name="leather_brown",
        display_name="Cognac Leather",
        base_color_rgb=(130, 75, 45),
        secondary_color_rgb=(95, 50, 28),
        roughness=0.50,
        metallic=0.02,
        pattern_type="leather",
        normal_detail_strength=1.5
    ),
    "fabric_woven": PBRMaterialDef(
        name="fabric_woven",
        display_name="Woven Linen Fabric",
        base_color_rgb=(70, 90, 120),
        secondary_color_rgb=(50, 65, 90),
        roughness=0.85,
        metallic=0.0,
        pattern_type="fabric",
        normal_detail_strength=1.4
    ),

    # 3. Automotive & Plastics
    "automotive_red": PBRMaterialDef(
        name="automotive_red",
        display_name="Crimson Metallic Paint",
        base_color_rgb=(185, 25, 30),
        secondary_color_rgb=(230, 60, 65),
        roughness=0.18,
        metallic=0.82,
        pattern_type="automotive",
        normal_detail_strength=0.5
    ),
    "automotive_blue": PBRMaterialDef(
        name="automotive_blue",
        display_name="Midnight Blue Metallic",
        base_color_rgb=(20, 50, 140),
        secondary_color_rgb=(50, 95, 200),
        roughness=0.18,
        metallic=0.85,
        pattern_type="automotive",
        normal_detail_strength=0.5
    ),
    "rubber_tire": PBRMaterialDef(
        name="rubber_tire",
        display_name="Treaded Rubber",
        base_color_rgb=(35, 35, 38),
        secondary_color_rgb=(25, 25, 28),
        roughness=0.92,
        metallic=0.02,
        pattern_type="rubber",
        normal_detail_strength=1.6
    ),

    # 4. Ceramics & Glass
    "ceramic_glazed": PBRMaterialDef(
        name="ceramic_glazed",
        display_name="Glazed Porcelain Ceramic",
        base_color_rgb=(235, 238, 242),
        secondary_color_rgb=(200, 210, 225),
        roughness=0.14,
        metallic=0.02,
        pattern_type="ceramic",
        normal_detail_strength=0.3
    ),
    "ceramic_terracotta": PBRMaterialDef(
        name="ceramic_terracotta",
        display_name="Terracotta Clay",
        base_color_rgb=(190, 95, 65),
        secondary_color_rgb=(160, 75, 50),
        roughness=0.78,
        metallic=0.0,
        pattern_type="ceramic",
        normal_detail_strength=1.0
    ),

    # 5. Organics
    "organic_apple_red": PBRMaterialDef(
        name="organic_apple_red",
        display_name="Honeycrisp Red Apple",
        base_color_rgb=(195, 30, 35),
        secondary_color_rgb=(220, 160, 40),
        roughness=0.28,
        metallic=0.02,
        pattern_type="organic",
        normal_detail_strength=0.8
    ),
    "organic_green": PBRMaterialDef(
        name="organic_green",
        display_name="Granny Smith Green Apple",
        base_color_rgb=(110, 175, 45),
        secondary_color_rgb=(150, 210, 60),
        roughness=0.28,
        metallic=0.02,
        pattern_type="organic",
        normal_detail_strength=0.8
    ),

    # 6. Metals & Alloys
    "aircraft_aluminum": PBRMaterialDef(
        name="aircraft_aluminum",
        display_name="Brushed Aircraft Aluminum",
        base_color_rgb=(195, 200, 205),
        secondary_color_rgb=(170, 175, 180),
        roughness=0.32,
        metallic=0.92,
        pattern_type="metal",
        normal_detail_strength=0.9
    ),
    "chrome_polished": PBRMaterialDef(
        name="chrome_polished",
        display_name="Polished Mirror Chrome",
        base_color_rgb=(240, 242, 245),
        roughness=0.08,
        metallic=0.98,
        pattern_type="metal",
        normal_detail_strength=0.2
    ),
    "gold_polished": PBRMaterialDef(
        name="gold_polished",
        display_name="24K Polished Gold",
        base_color_rgb=(245, 195, 60),
        secondary_color_rgb=(220, 160, 35),
        roughness=0.15,
        metallic=0.95,
        pattern_type="metal",
        normal_detail_strength=0.3
    ),
    "steel_tempered": PBRMaterialDef(
        name="steel_tempered",
        display_name="Tempered Carbon Steel",
        base_color_rgb=(140, 145, 155),
        secondary_color_rgb=(110, 115, 125),
        roughness=0.26,
        metallic=0.88,
        pattern_type="metal",
        normal_detail_strength=0.7
    ),
}

# Semantic mapping from object category to default and alternative materials
CATEGORY_MATERIAL_MAPPING: Dict[str, Dict[str, Any]] = {
    "chair": {
        "default": "natural_wood",
        "options": ["natural_wood", "dark_walnut", "leather_brown", "fabric_woven", "steel_tempered"]
    },
    "table": {
        "default": "natural_wood",
        "options": ["natural_wood", "dark_walnut", "ceramic_glazed", "steel_tempered"]
    },
    "car": {
        "default": "automotive_red",
        "options": ["automotive_red", "automotive_blue", "chrome_polished", "steel_tempered"]
    },
    "airplane": {
        "default": "aircraft_aluminum",
        "options": ["aircraft_aluminum", "automotive_blue", "chrome_polished", "steel_tempered"]
    },
    "cup": {
        "default": "ceramic_glazed",
        "options": ["ceramic_glazed", "ceramic_terracotta", "gold_polished", "steel_tempered"]
    },
    "mug": {
        "default": "ceramic_glazed",
        "options": ["ceramic_glazed", "ceramic_terracotta", "natural_wood"]
    },
    "coffee cup": {
        "default": "ceramic_glazed",
        "options": ["ceramic_glazed", "ceramic_terracotta"]
    },
    "apple": {
        "default": "organic_apple_red",
        "options": ["organic_apple_red", "organic_green", "gold_polished"]
    },
    "bicycle": {
        "default": "automotive_blue",
        "options": ["automotive_blue", "automotive_red", "aircraft_aluminum", "chrome_polished"]
    },
    "bench": {
        "default": "natural_wood",
        "options": ["natural_wood", "dark_walnut", "steel_tempered"]
    },
    "sword": {
        "default": "steel_tempered",
        "options": ["steel_tempered", "gold_polished", "chrome_polished"]
    },
    "bottle": {
        "default": "ceramic_glazed",
        "options": ["ceramic_glazed", "ceramic_terracotta", "gold_polished"]
    },
    "vase": {
        "default": "ceramic_glazed",
        "options": ["ceramic_glazed", "ceramic_terracotta", "gold_polished"]
    },
    "bowl": {
        "default": "ceramic_glazed",
        "options": ["ceramic_glazed", "natural_wood", "ceramic_terracotta"]
    },
    "hammer": {
        "default": "steel_tempered",
        "options": ["steel_tempered", "natural_wood"]
    },
    "guitar": {
        "default": "natural_wood",
        "options": ["natural_wood", "dark_walnut", "automotive_red"]
    },
    "tree": {
        "default": "organic_green",
        "options": ["organic_green", "natural_wood"]
    },
    "house": {
        "default": "ceramic_terracotta",
        "options": ["ceramic_terracotta", "natural_wood", "dark_walnut"]
    },
    "mushroom": {
        "default": "organic_apple_red",
        "options": ["organic_apple_red", "ceramic_terracotta"]
    },
}


class PBRMaterialLibrary:
    @classmethod
    def get_material(cls, name: str) -> PBRMaterialDef:
        return MATERIALS_DB.get(name, MATERIALS_DB["ceramic_glazed"])

    @classmethod
    def get_material_for_category(
        cls,
        category: str,
        style: str = "realistic",
        material_override: Optional[str] = None
    ) -> PBRMaterialDef:
        """
        Resolves semantic category, style preset, and material override into configured PBRMaterialDef.
        """
        cat_lower = (category or "").lower().strip()
        mat_key = material_override

        if not mat_key:
            cat_info = CATEGORY_MATERIAL_MAPPING.get(cat_lower, {})
            mat_key = cat_info.get("default", "ceramic_glazed")

        base_mat = cls.get_material(mat_key)

        # Apply style modifiers if non-default
        style_mod = STYLE_MODIFIERS.get(style.lower(), STYLE_MODIFIERS[VisualStyle.REALISTIC.value])

        mod_roughness = min(1.0, max(0.04, base_mat.roughness * style_mod.roughness_multiplier))
        mod_metallic = min(1.0, max(0.0, base_mat.metallic * style_mod.metallic_multiplier))

        # Adjust colors with style saturation/shift
        r, g, b = base_mat.base_color_rgb
        shift_r, shift_g, shift_b = style_mod.color_shift
        sat = style_mod.saturation_multiplier

        # Perceived luminance
        lum = 0.299 * r + 0.587 * g + 0.114 * b
        new_r = int(min(255, max(0, (lum + sat * (r - lum)) * shift_r)))
        new_g = int(min(255, max(0, (lum + sat * (g - lum)) * shift_g)))
        new_b = int(min(255, max(0, (lum + sat * (b - lum)) * shift_b)))

        return PBRMaterialDef(
            name=f"{base_mat.name}_{style}",
            display_name=f"{base_mat.display_name} ({style_mod.name})",
            base_color_rgb=(new_r, new_g, new_b),
            secondary_color_rgb=base_mat.secondary_color_rgb,
            roughness=mod_roughness,
            metallic=mod_metallic,
            pattern_type=base_mat.pattern_type,
            normal_detail_strength=base_mat.normal_detail_strength * style_mod.normal_strength
        )

    @classmethod
    def list_options_for_category(cls, category: str) -> List[Dict[str, str]]:
        cat_lower = (category or "").lower().strip()
        cat_info = CATEGORY_MATERIAL_MAPPING.get(cat_lower, {})
        options = cat_info.get("options", ["ceramic_glazed", "natural_wood", "steel_tempered", "chrome_polished"])
        return [
            {"id": opt, "name": MATERIALS_DB[opt].display_name}
            for opt in options if opt in MATERIALS_DB
        ]

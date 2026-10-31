"""
Deterministic Semantic Description and Reconstruction Hints Generator
Synthesizes verified classifier predictions, geometric tags, and stroke metrics
into natural language descriptions and downstream 3D modeling priors.
"""

from typing import Dict, Any, List


# Category taxonomies for structural priors
OBJECT_TAXONOMY = {
    "furniture": ["chair", "table", "bed", "couch", "bench"],
    "vehicle": ["car", "airplane", "bicycle", "bus", "helicopter", "canoe"],
    "tableware": ["cup", "wine_glass", "spoon", "fork", "knife"],
    "everyday_tool": ["axe", "hammer", "scissors", "flashlight", "sword"],
    "electronics": ["camera", "cell_phone", "alarm_clock", "piano", "guitar"],
    "flora_food": ["apple", "banana", "tree", "cactus", "mushroom", "cake"],
    "architecture": ["house", "castle", "bridge", "door"],
    "apparel": ["hat", "shoe", "eyeglasses", "crown"]
}

CATEGORY_STRUCTURES = {
    "chair": "seat_with_supporting_legs_and_backrest",
    "table": "planar_surface_with_vertical_supports",
    "bed": "horizontal_mattress_platform_with_headboard",
    "couch": "cushioned_seating_with_armrests_and_back",
    "bench": "elongated_seating_plank_with_legs",
    "car": "wheeled_chassis_with_cabin_and_windshield",
    "airplane": "aerodynamic_fuselage_with_wings_and_empennage",
    "bicycle": "two_wheeled_frame_with_handlebars_and_fork",
    "bus": "boxy_passenger_body_with_parallel_wheelsets",
    "helicopter": "cabin_with_main_rotor_and_tail_boom",
    "cup": "cylindrical_vessel_with_lateral_handle",
    "wine_glass": "stemmed_goblet_with_circular_base",
    "apple": "spherical_body_with_stem_indentation",
    "tree": "vertical_trunk_supporting_foliage_canopy",
    "sword": "longitudinal_blade_with_crossguard_and_hilt",
    "axe": "shaft_handle_with_asymmetric_cutting_wedge",
    "hammer": "impact_head_mounted_on_elongated_handle",
    "house": "walled_base_with_pitched_roof",
}


class SemanticDescriptionGenerator:
    """
    Generates deterministic natural language descriptions and 3D structural priors.
    """
    @staticmethod
    def infer_object_type(category: str) -> str:
        for taxonomy_type, cat_list in OBJECT_TAXONOMY.items():
            if category in cat_list:
                return taxonomy_type
        return "general_object"

    @classmethod
    def generate(
        cls,
        prediction_result: Dict[str, Any],
        geometric_tags: List[str],
        geometry_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        category = prediction_result.get("predicted_category", "object")
        confidence = prediction_result.get("top_confidence", 0.0)
        alternatives = prediction_result.get("alternative_categories", [])
        is_ambiguous = prediction_result.get("is_ambiguous", False)
        uncertainty_level = prediction_result.get("uncertainty_level", "low")

        # 1. Natural Language Description Composition
        modifiers = []
        if "predominantly_vertical" in geometric_tags:
            modifiers.append("predominantly vertical")
        elif "predominantly_horizontal" in geometric_tags:
            modifiers.append("predominantly horizontal")

        if "elongated" in geometric_tags:
            modifiers.append("elongated")
        elif "circular_structure" in geometric_tags:
            modifiers.append("circular")

        prefix = " ".join(modifiers)
        clean_cat = category.replace("_", " ")

        if is_ambiguous:
            alt_str = ", ".join([a.replace("_", " ") for a in alternatives[:2]])
            description_base = f"An ambiguous sketch resembling a {clean_cat} or possibly {alt_str}"
        else:
            article = "An" if prefix and prefix[0].lower() in "aeiou" else ("A" if prefix else "A")
            description_base = f"{article} {prefix} {clean_cat}".strip()
            if not prefix:
                description_base = f"A {clean_cat}"

        structural_clauses = []
        if "multiple_components" in geometric_tags:
            structural_clauses.append("multiple structural components")
        if "enclosed_region" in geometric_tags:
            structural_clauses.append("an enclosed region")
        if "complex_contour" in geometric_tags:
            structural_clauses.append("detailed contour geometry")
        elif "approximately_symmetric" in geometric_tags:
            structural_clauses.append("bilateral reflectional symmetry")

        if structural_clauses:
            full_description = f"{description_base} with " + " and ".join(structural_clauses) + "."
        else:
            full_description = f"{description_base} structure."

        # 2. Reconstruction Hints
        object_type = cls.infer_object_type(category)
        likely_structure = CATEGORY_STRUCTURES.get(category, f"{clean_cat}_geometry")
        symmetry_prior = "approximately_symmetric" in geometric_tags

        reconstruction_hints = {
            "object_type": object_type,
            "likely_structure": likely_structure,
            "symmetry_prior": symmetry_prior,
            "confidence_level": "low" if is_ambiguous else ("high" if confidence >= 0.70 else "moderate")
        }

        return {
            "object_category": category,
            "confidence": confidence,
            "alternative_categories": alternatives,
            "geometric_tags": geometric_tags,
            "semantic_description": full_description,
            "reconstruction_hints": reconstruction_hints
        }

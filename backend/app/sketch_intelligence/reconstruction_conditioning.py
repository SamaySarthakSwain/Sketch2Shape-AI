"""
Reconstruction Conditioning Interface for Downstream 3D Engines
Constructs a decoupled metadata payload containing semantic prompts, geometric constraints,
and uncertainty parameters consumable by InstantMesh or future text/multimodal 3D generators.
"""

from typing import Dict, Any, List


class ReconstructionConditioner:
    """
    Produces decoupled conditioning metadata for 3D reconstruction models.
    """
    @classmethod
    def build_conditioning_payload(
        cls,
        category: str,
        confidence: float,
        is_ambiguous: bool,
        geometric_tags: List[str],
        geometry_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        clean_name = category.replace("_", " ")

        # 1. Deterministic Semantic Prompt for text-conditioned or multimodal 3D models
        semantic_prompt = f"A single 3D {clean_name}, isolated, centered, complete object, clean geometry."

        # 2. Geometry Constraints
        symmetry_prior = "approximately_symmetric" in geometric_tags
        
        orientation = "neutral"
        if "predominantly_vertical" in geometric_tags:
            orientation = "vertical"
        elif "predominantly_horizontal" in geometric_tags:
            orientation = "horizontal"

        components = geometry_metrics.get("stroke_analysis", {}).get("connected_components_count", 1)

        geometry_constraints = {
            "symmetry_prior": symmetry_prior,
            "orientation": orientation,
            "component_count": int(components)
        }

        # 3. Uncertainty Envelope
        uncertainty = {
            "is_ambiguous": is_ambiguous,
            "top_prediction_confidence": round(float(confidence), 4)
        }

        return {
            "category": category,
            "semantic_prompt": semantic_prompt,
            "geometry_constraints": geometry_constraints,
            "uncertainty": uncertainty
        }

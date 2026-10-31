"""
Semantically-Aware Model Selector
Analyzes semantic category, confidence score, symmetry, and geometric tags
to dynamically route sketches to the optimal 3D reconstruction engine.
"""

from typing import Dict, Any, List, Optional, Tuple
from app.reconstruction.model_registry import model_registry


# Categories with natural rotational symmetry
ROTATIONAL_CATEGORIES = {
    "cup", "coffee_cup", "mug", "vase", "bowl", "bottle", "wine_bottle",
    "donut", "plate", "wine_glass", "candle", "bucket", "flower_pot"
}

# Categories requiring multi-view deep generative geometry
COMPLEX_3D_CATEGORIES = {
    "chair", "car", "airplane", "bicycle", "table", "guitar", "house",
    "tree", "bird", "fish", "clock", "bench", "bus", "truck", "helicopter",
    "couch", "bed", "motorcycle", "ship", "bridge", "camera", "piano"
}


class ModelSelector:
    """
    Intelligently selects the appropriate 3D reconstruction model based on
    semantic intelligence metadata and system resources.
    """

    @classmethod
    def select_model(
        cls,
        user_model: Optional[str] = None,
        category: Optional[str] = None,
        confidence: float = 0.0,
        geometric_tags: Optional[List[str]] = None,
        symmetry_scores: Optional[Dict[str, float]] = None,
        quality_preset: str = "balanced",
        allow_fallback: bool = True
    ) -> Tuple[str, str, Dict[str, Any]]:
        """
        Determines the optimal reconstruction engine.
        Returns:
            (selected_model_name, selection_reason, adapter_config_overrides)
        """
        tags = set(geometric_tags or [])
        sym = symmetry_scores or {}
        cat = (category or "").lower().replace(" ", "_")

        # 1. User Explicit Request
        if user_model:
            model = model_registry.get_model(user_model)
            if model and model.is_available():
                return user_model, f"User explicitly requested model '{user_model}'.", {}
            elif not allow_fallback:
                return user_model, f"Requested model '{user_model}' is unavailable and fallback disabled.", {}
            else:
                fallback_reason = f"Requested model '{user_model}' is unavailable on this hardware."

        # 2. Ultra-Fast / Zero-VRAM preset
        if quality_preset in ("ultra_fast", "procedural"):
            return "procedural", "Procedural engine selected for instant zero-VRAM reconstruction.", {"mode": "rotational"}

        # 3. Check rotational symmetry objects
        is_rotational_cat = cat in ROTATIONAL_CATEGORIES
        has_high_vertical_symmetry = sym.get("vertical", 0.0) >= 0.85

        if quality_preset == "fast" and (is_rotational_cat or (has_high_vertical_symmetry and "symmetric" in tags)):
            return (
                "procedural",
                f"Selected procedural rotational lathe reconstruction for symmetrical object '{cat or 'unknown'}' (symmetry={sym.get('vertical', 0):.2f}).",
                {"mode": "rotational"}
            )

        # 4. Check deep generative models
        instantmesh = model_registry.get_model("instantmesh")
        if instantmesh and instantmesh.is_available():
            reason = f"Selected InstantMesh deep generative engine for high-fidelity 3D reconstruction of '{cat or 'sketch'}'."
            config = {
                "diffusion_steps": 30 if quality_preset == "fast" else (45 if quality_preset == "balanced" else 60)
            }
            return "instantmesh", reason, config

        hunyuan = model_registry.get_model("hunyuan3d-2")
        if hunyuan and hunyuan.is_available():
            return "hunyuan3d-2", f"Selected Hunyuan3D-2 DiT engine for '{cat}'.", {}

        triposr = model_registry.get_model("triposr")
        if triposr and triposr.is_available():
            return "triposr", f"Selected TripoSR feed-forward engine for '{cat}'.", {}

        # 5. Robust Fallback
        return (
            "procedural",
            "Deep generative models unavailable or out of VRAM; safely falling back to procedural SDF engine.",
            {"mode": "extrusion"}
        )

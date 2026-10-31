"""
Provider Selector Module
Selects the best 3D reconstruction engine based on user preference,
configured API credentials, category semantics, and quality preset.
"""

from typing import Tuple, Optional, Dict, Any
from .provider_registry import provider_registry, ProviderRegistry
from .provider_config import ProviderConfig


class ProviderSelector:
    def __init__(self, registry: Optional[ProviderRegistry] = None):
        self.registry = registry or provider_registry

    def select_engine(
        self,
        user_preference: str,
        category: str,
        quality_preset: str = "balanced"
    ) -> Tuple[str, str, bool]:
        """
        Determines the execution target.
        Returns:
            engine_name: 'meshy' | 'tripo' | 'rodin' | 'instantmesh' | 'procedural'
            selection_reason: Human-readable explanation
            is_cloud: True if external API, False if local
        """
        pref = (user_preference or "auto").lower().strip()
        available_cloud = self.registry.list_available_providers()

        # 1. User explicitly requested a cloud provider
        if pref in ["meshy", "tripo", "rodin"]:
            p = self.registry.get_provider(pref)
            if p and p.is_available():
                return pref, f"User explicitly selected cloud provider '{pref}'", True
            else:
                reason = f"Cloud provider '{pref}' requested, but API credentials are not set. Falling back to local pipeline."
                # Fall through to local routing

        # 2. User explicitly requested a local provider
        if pref in ["instantmesh", "local_instantmesh"]:
            return "instantmesh", "User explicitly selected local InstantMesh neural triplane", False
        elif pref in ["procedural", "local_procedural"]:
            return "procedural", "User explicitly selected local procedural engine", False

        # 3. Auto mode with cloud provider configured:
        # If high quality is requested and a cloud provider is active, use it for premium fidelity
        if pref == "auto" and available_cloud and quality_preset == "high":
            # Priority: Meshy (best PBR texturing) -> Tripo (best geometry) -> Rodin
            for candidate in ["meshy", "tripo", "rodin"]:
                if candidate in available_cloud:
                    return candidate, f"Auto-selected cloud provider '{candidate}' for high-quality PBR asset generation", True

        # 4. Local execution route
        from ..category_templates import CategoryGeometryTemplates
        has_template = CategoryGeometryTemplates.is_category_supported(category)

        if has_template and quality_preset != "high":
            return "procedural", f"Local procedural parametric template routed for '{category}'", False
        elif quality_preset in ["fast", "ultra_fast"]:
            return "procedural", f"Local procedural fast preset routed for '{category}'", False
        else:
            return "instantmesh", f"Local InstantMesh neural triplane routed for '{category}'", False

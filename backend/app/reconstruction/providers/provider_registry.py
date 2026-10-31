"""
Provider Registry Module
Maintains singleton instances of external AI 3D generation providers.
"""

from typing import Dict, List, Optional, Any
from .base_provider import BaseProvider
from .provider_config import ProviderConfig
from .meshy_provider import MeshyProvider
from .tripo_provider import TripoProvider
from .rodin_provider import RodinProvider


class ProviderRegistry:
    def __init__(self, config: Optional[ProviderConfig] = None):
        self.config = config or ProviderConfig()
        self._providers: Dict[str, BaseProvider] = {
            "meshy": MeshyProvider(self.config),
            "tripo": TripoProvider(self.config),
            "rodin": RodinProvider(self.config),
        }

    def get_provider(self, name: str) -> Optional[BaseProvider]:
        return self._providers.get(name.lower().strip())

    def list_all_providers(self) -> List[str]:
        return list(self._providers.keys())

    def list_available_providers(self) -> List[str]:
        """Returns only providers that have valid credentials and are enabled."""
        return [name for name, p in self._providers.items() if p.is_available()]

    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        status = {}
        for name, p in self._providers.items():
            avail = p.is_available()
            status[name] = {
                "name": name,
                "is_available": avail,
                "has_credentials": self.config.is_provider_configured(name),
                "is_enabled": getattr(self.config, f"enable_{name}", False),
            }
        return status


# Singleton registry instance
provider_registry = ProviderRegistry()

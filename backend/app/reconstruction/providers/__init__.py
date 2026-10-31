"""
Reconstruction Providers Subsystem
Supports external premium AI 3D generation engines:
- Meshy API
- Tripo3D API
- Hyper3D Rodin API
Along with local engine fallback.
"""

from .provider_config import ProviderConfig, ProviderCredentials
from .provider_tasks import ProviderTaskResult, ProviderTaskStatus, ProviderTextureUrls
from .base_provider import BaseProvider
from .meshy_provider import MeshyProvider
from .tripo_provider import TripoProvider
from .rodin_provider import RodinProvider
from .provider_registry import ProviderRegistry, provider_registry
from .provider_selector import ProviderSelector

__all__ = [
    "ProviderConfig",
    "ProviderCredentials",
    "ProviderTaskResult",
    "ProviderTaskStatus",
    "ProviderTextureUrls",
    "BaseProvider",
    "MeshyProvider",
    "TripoProvider",
    "RodinProvider",
    "ProviderRegistry",
    "provider_registry",
    "ProviderSelector",
]

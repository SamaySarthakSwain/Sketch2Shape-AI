"""
Provider Configuration and Credentials Module
Manages external 3D generation provider API keys, endpoints, and timeouts.
Reads credentials strictly from backend environment variables:
- MESHY_API_KEY
- TRIPO_API_KEY
- RODIN_API_KEY
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class ProviderCredentials:
    meshy_api_key: Optional[str] = None
    tripo_api_key: Optional[str] = None
    rodin_api_key: Optional[str] = None

    @classmethod
    def from_env(cls) -> "ProviderCredentials":
        return cls(
            meshy_api_key=os.environ.get("MESHY_API_KEY", "").strip() or None,
            tripo_api_key=os.environ.get("TRIPO_API_KEY", "").strip() or None,
            rodin_api_key=os.environ.get("RODIN_API_KEY", "").strip() or None,
        )


@dataclass
class ProviderConfig:
    # Timeout & Polling limits
    poll_interval_seconds: float = 3.0
    timeout_seconds: float = 300.0  # 5 minutes
    max_retries: int = 3
    retry_backoff_seconds: float = 2.0

    # Provider enable toggles
    enable_meshy: bool = True
    enable_tripo: bool = True
    enable_rodin: bool = True

    # PBR refinement preferences
    enable_pbr_texturing: bool = True
    target_polycount: int = 25000
    preferred_provider: str = "auto"  # 'auto', 'meshy', 'tripo', 'rodin', 'local'

    # Credentials
    credentials: ProviderCredentials = field(default_factory=ProviderCredentials.from_env)

    def is_provider_configured(self, provider_name: str) -> bool:
        p = provider_name.lower().strip()
        if p == "meshy":
            return bool(self.enable_meshy and self.credentials.meshy_api_key)
        elif p == "tripo":
            return bool(self.enable_tripo and self.credentials.tripo_api_key)
        elif p == "rodin":
            return bool(self.enable_rodin and self.credentials.rodin_api_key)
        elif p in ["local", "instantmesh", "procedural"]:
            return True
        return False

    def get_configured_providers(self) -> list:
        configured = []
        if self.is_provider_configured("meshy"):
            configured.append("meshy")
        if self.is_provider_configured("tripo"):
            configured.append("tripo")
        if self.is_provider_configured("rodin"):
            configured.append("rodin")
        return configured

"""
Model Registry for Sketch2Shape 3D Reconstruction Engines
Central singleton registry managing model registration, discovery, capabilities,
and lifecycle management across all reconstruction adapters.
"""

from typing import Dict, List, Optional
from app.reconstruction.base_model import BaseReconstructionAdapter
from app.reconstruction.reconstruction_config import ModelInfo
from app.reconstruction.adapters.instantmesh_adapter import InstantMeshAdapter
from app.reconstruction.adapters.procedural_adapter import ProceduralAdapter
from app.reconstruction.adapters.hunyuan_adapter import HunyuanAdapter
from app.reconstruction.adapters.triposr_adapter import TripoSRAdapter
from app.reconstruction.adapters.trellis_adapter import TrellisAdapter


class ModelRegistry:
    """
    Singleton registry managing all available 3D reconstruction models.
    """
    _instance: Optional["ModelRegistry"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelRegistry, cls).__new__(cls)
            cls._instance._models: Dict[str, BaseReconstructionAdapter] = {}
            cls._instance._init_default_models()
        return cls._instance

    def _init_default_models(self):
        """Initializes default known model adapters."""
        self.register(TrellisAdapter())
        self.register(InstantMeshAdapter())
        self.register(ProceduralAdapter())
        self.register(HunyuanAdapter())
        self.register(TripoSRAdapter())

    def register(self, adapter: BaseReconstructionAdapter):
        """Registers a model adapter."""
        self._models[adapter.name.lower()] = adapter

    def get_model(self, name: str) -> Optional[BaseReconstructionAdapter]:
        """Retrieves an adapter by name (case-insensitive)."""
        return self._models.get(name.lower())

    def list_models(self) -> List[ModelInfo]:
        """Returns metadata info for all registered models."""
        return [adapter.get_model_info() for adapter in self._models.values()]

    def get_available_models(self) -> List[str]:
        """Returns names of models whose weights/dependencies are present."""
        return [name for name, adapter in self._models.items() if adapter.is_available()]

    def unload_all(self):
        """Unloads all loaded models to release GPU/system RAM."""
        for adapter in self._models.values():
            adapter.unload_model()


# Global accessor
model_registry = ModelRegistry()

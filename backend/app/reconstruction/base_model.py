"""
Model-Agnostic Abstract Base Class for 3D Reconstruction Adapters
All reconstruction engines (InstantMesh, Hunyuan3D, Stable Fast 3D, TripoSR)
must inherit from this interface to guarantee uniform lifecycle and I/O.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import os
import torch

from .reconstruction_config import ReconstructionRequest, ReconstructionResponse, ModelInfo


class BaseReconstructionAdapter(ABC):
    """
    Standard adapter interface for 3D reconstruction models.
    """
    def __init__(self, name: str, display_name: str, vram_required_gb: float, device: Optional[str] = None):
        self.name = name
        self.display_name = display_name
        self.vram_required_gb = vram_required_gb
        self.is_loaded = False
        if device is not None:
            self.device = torch.device(device)
        else:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    @abstractmethod
    def load_model(self) -> bool:
        """Loads neural checkpoints and allocates GPU/CPU memory."""
        pass

    @abstractmethod
    def unload_model(self) -> bool:
        """Unloads weights from VRAM and triggers garbage collection and CUDA cache emptying."""
        pass

    @abstractmethod
    def reconstruct(self, request: ReconstructionRequest) -> ReconstructionResponse:
        """Executes full 3D mesh reconstruction from an input sketch."""
        pass

    @abstractmethod
    def get_model_info(self) -> ModelInfo:
        """Returns metadata regarding capabilities, memory footprint, and availability."""
        pass

    def get_resource_usage(self) -> Dict[str, Any]:
        """Measures current GPU memory and device state."""
        usage = {
            "device": str(self.device),
            "is_loaded": self.is_loaded,
            "allocated_mb": 0.0,
            "reserved_mb": 0.0,
            "total_vram_gb": 0.0
        }
        if torch.cuda.is_available() and self.device.type == "cuda":
            usage["allocated_mb"] = round(torch.cuda.memory_allocated(self.device) / (1024**2), 2)
            usage["reserved_mb"] = round(torch.cuda.memory_reserved(self.device) / (1024**2), 2)
            usage["total_vram_gb"] = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2)
        return usage

    def validate_output(self, mesh_path: str) -> Dict[str, Any]:
        """Validates that the generated mesh file exists and is loadable."""
        from .mesh_validation import MeshValidator
        return MeshValidator.validate_file(mesh_path)

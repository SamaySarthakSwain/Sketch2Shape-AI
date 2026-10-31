"""
Base 3D Reconstruction Interface
Defines the standard contract for all reconstruction backends.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import trimesh
import numpy as np


class BaseReconstructionEngine(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def generate_mesh(
        self,
        stroke_mask: np.ndarray,
        depth_map: np.ndarray,
        metadata: Dict[str, Any],
        prompt: Optional[str] = None
    ) -> trimesh.Trimesh:
        """
        Reconstructs a 3D mesh from preprocessed 2D sketch features.
        Returns a trimesh.Trimesh object.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if required dependencies and models are loaded and ready."""
        pass

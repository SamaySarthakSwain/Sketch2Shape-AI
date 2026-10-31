"""
Data Models and Configuration Contracts for 3D Reconstruction Engine
Enforces consistent request, response, and quality presets across all model adapters.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ReconstructionRequest(BaseModel):
    image_path: str
    semantic_metadata: Dict[str, Any] = Field(default_factory=dict)
    output_dir: str = Field(default="outputs/reconstructions")
    quality_preset: str = Field(default="balanced")  # "fast", "balanced", "high", "ultra_fast"
    export_formats: List[str] = Field(default_factory=lambda: ["glb", "obj"])
    preferred_model: Optional[str] = None
    preprocess_first: bool = False

    def __init__(
        self,
        image_path: str,
        semantic_metadata: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        preferred_model: Optional[str] = None,
        model_name: Optional[str] = None,
        **data
    ):
        if metadata is not None and semantic_metadata is None:
            semantic_metadata = metadata
        if model_name is not None and preferred_model is None:
            preferred_model = model_name
        super().__init__(
            image_path=image_path,
            semantic_metadata=semantic_metadata or {},
            preferred_model=preferred_model,
            **data
        )

    @property
    def metadata(self) -> Dict[str, Any]:
        return self.semantic_metadata

    @property
    def model_name(self) -> Optional[str]:
        return self.preferred_model


class ReconstructionResponse(BaseModel):
    success: bool
    model_name: str
    mesh_path: Optional[str] = None
    texture_path: Optional[str] = None
    inference_time_seconds: float = 0.0
    vertices: int = 0
    faces: int = 0
    mesh_valid: bool = False
    formats: Dict[str, str] = Field(default_factory=dict)  # {"glb": "...", "obj": "..."}
    quality_report: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None

    @property
    def downloads(self) -> Dict[str, str]:
        return self.formats


class ModelInfo(BaseModel):
    name: str
    display_name: str
    category: str
    vram_required_gb: float
    supports_texture: bool
    supports_text_conditioning: bool
    is_available: bool
    status_message: str

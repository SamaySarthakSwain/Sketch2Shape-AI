"""
Pipeline Configuration Schema
Defines user inputs, adaptive model routing options, and quality constraints.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class PipelineConfig(BaseModel):
    image_path: Optional[str] = None
    image_b64: Optional[str] = None
    prompt: Optional[str] = None
    preferred_model: str = Field(default="auto", description="auto, instantmesh, procedural, triposr, meshy, tripo, rodin")
    quality_preset: str = Field(default="balanced", description="fast, balanced, high, ultra_fast")
    preprocess_first: bool = True
    auto_refine: bool = True
    refine_preset: str = Field(default="balanced", description="fast, balanced, high")
    export_formats: List[str] = Field(default=["glb", "obj", "stl", "3mf", "usdz", "gltf"])
    allow_fallback: bool = True
    min_quality_score: float = Field(default=50.0, description="Minimum overall score to accept primary candidate")
    timeout_seconds: float = Field(default=120.0, description="Maximum pipeline execution timeout")
    category_override: Optional[str] = None
    visual_style: str = Field(default="realistic", description="realistic, stylized, cartoon, low_poly, product_render, futuristic, metallic, matte, glossy")
    material_override: Optional[str] = Field(default=None, description="Specific material identifier from PBR material library")
    enable_pbr: bool = Field(default=True, description="Whether to bake full PBR textures into the 3D asset")
    enable_packaging: bool = Field(default=True, description="Whether to generate professional multi-format ZIP asset bundle")
    cloud_provider: Optional[str] = Field(default="auto", description="auto, meshy, tripo, rodin, local")
    metadata: Optional[Dict[str, Any]] = None
    color_palette: Optional[Dict[str, Any]] = None
    primary_color_rgb: Optional[List[int]] = None
    secondary_color_rgb: Optional[List[int]] = None

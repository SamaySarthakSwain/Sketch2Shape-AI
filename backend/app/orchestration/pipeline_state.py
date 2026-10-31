"""
Pipeline State & Execution Data Models
Defines typed states, chronological stage execution records, and pipeline job status.
"""

import time
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class PipelineStage(str, Enum):
    INITIALIZED = "initialized"
    VALIDATING_INPUT = "validating_input"
    OPENCV_PREPROCESSING = "opencv_preprocessing"
    SKETCH_INTELLIGENCE = "sketch_intelligence"
    MODEL_SELECTION = "model_selection"
    RECONSTRUCTING_3D = "reconstructing_3d"
    MESH_VALIDATION = "mesh_validation"
    GEOMETRY_ANALYSIS = "geometry_analysis"
    QUALITY_EVALUATION = "quality_evaluation"
    MESH_REFINEMENT = "mesh_refinement"
    PBR_TEXTURING = "pbr_texturing"
    EXPORTING_ASSETS = "exporting_assets"
    ASSET_PACKAGING = "asset_packaging"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StageExecutionRecord(BaseModel):
    stage: PipelineStage
    start_time: float
    end_time: Optional[float] = None
    duration_seconds: float = 0.0
    success: bool = False
    message: str = ""
    artifacts: Dict[str, str] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class PipelineJob(BaseModel):
    job_id: str
    created_at: float
    updated_at: float
    current_stage: PipelineStage
    status: str = "queued"  # queued, processing, completed, failed, cancelled
    config: Dict[str, Any] = Field(default_factory=dict)
    stage_history: List[StageExecutionRecord] = Field(default_factory=list)
    artifacts: Dict[str, Any] = Field(default_factory=dict)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    is_cancelled: bool = False
    peak_vram_mb: float = 0.0
    total_duration_seconds: float = 0.0

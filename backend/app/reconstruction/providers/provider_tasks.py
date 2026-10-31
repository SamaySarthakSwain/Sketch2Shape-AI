"""
Provider Task and Result Models
Standardized data contracts for external AI 3D generation tasks.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List
import time


class ProviderTaskStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


@dataclass
class ProviderTextureUrls:
    base_color: Optional[str] = None
    normal: Optional[str] = None
    roughness: Optional[str] = None
    metallic: Optional[str] = None
    ambient_occlusion: Optional[str] = None
    emissive: Optional[str] = None


@dataclass
class ProviderTaskResult:
    provider: str
    task_id: str
    status: ProviderTaskStatus
    progress_percent: float = 0.0
    download_url_glb: Optional[str] = None
    download_url_obj: Optional[str] = None
    download_url_fbx: Optional[str] = None
    download_url_usdz: Optional[str] = None
    textures: ProviderTextureUrls = field(default_factory=ProviderTextureUrls)
    local_glb_path: Optional[str] = None
    local_texture_dir: Optional[str] = None
    execution_time_seconds: float = 0.0
    credits_used: Optional[float] = None
    error_message: Optional[str] = None
    raw_response: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None

    def is_finished(self) -> bool:
        return self.status in [
            ProviderTaskStatus.SUCCEEDED,
            ProviderTaskStatus.FAILED,
            ProviderTaskStatus.CANCELLED,
            ProviderTaskStatus.TIMED_OUT,
        ]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "task_id": self.task_id,
            "status": self.status.value,
            "progress_percent": self.progress_percent,
            "download_url_glb": self.download_url_glb,
            "local_glb_path": self.local_glb_path,
            "execution_time_seconds": round(self.execution_time_seconds, 2),
            "credits_used": self.credits_used,
            "error_message": self.error_message,
            "has_pbr_textures": bool(self.textures.base_color or self.textures.normal),
        }

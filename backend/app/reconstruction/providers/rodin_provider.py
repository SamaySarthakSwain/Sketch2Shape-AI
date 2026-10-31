"""
Hyper3D Rodin Image-to-3D Provider Integration
Documentation: https://docs.hyper3d.ai/en
Supports:
- Image-to-3D with Rodin foundation model
- High-fidelity geometry reconstruction and texturing
- Async generation and asset retrieval
"""

import time
import requests
from typing import Optional, Dict, Any
from .base_provider import BaseProvider
from .provider_config import ProviderConfig
from .provider_tasks import ProviderTaskResult, ProviderTaskStatus, ProviderTextureUrls


class RodinProvider(BaseProvider):
    API_BASE = "https://api.hyper3d.ai/v1/generation"

    def __init__(self, config: Optional[ProviderConfig] = None):
        super().__init__("rodin", config)

    def is_available(self) -> bool:
        return bool(self.config.enable_rodin and self.config.credentials.rodin_api_key)

    def _get_headers(self) -> Dict[str, str]:
        key = self.config.credentials.rodin_api_key or ""
        return {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }

    def submit_task(
        self,
        image_path: str,
        prompt: Optional[str] = None,
        category: Optional[str] = None,
        style: Optional[str] = None,
        enable_pbr: bool = True
    ) -> ProviderTaskResult:
        if not self.is_available():
            return ProviderTaskResult(
                provider=self.name,
                task_id="",
                status=ProviderTaskStatus.FAILED,
                error_message="RODIN_API_KEY is not configured or Rodin is disabled."
            )

        try:
            image_b64 = self.encode_image_b64(image_path)
            payload = {
                "images": [image_b64],
                "prompt": prompt or f"3D model of a {category or 'object'}",
                "quality": "high",
                "format": "glb"
            }

            resp = requests.post(self.API_BASE, json=payload, headers=self._get_headers(), timeout=30)

            if resp.status_code == 401:
                return ProviderTaskResult(
                    provider=self.name,
                    task_id="",
                    status=ProviderTaskStatus.FAILED,
                    error_message="Authentication failed: Invalid RODIN_API_KEY."
                )
            elif resp.status_code == 429:
                return ProviderTaskResult(
                    provider=self.name,
                    task_id="",
                    status=ProviderTaskStatus.FAILED,
                    error_message="Rodin API rate limit exceeded."
                )

            resp.raise_for_status()
            data = resp.json()

            task_id = data.get("task_id") or data.get("id") or data.get("generation_id")
            if not task_id:
                return ProviderTaskResult(
                    provider=self.name,
                    task_id="",
                    status=ProviderTaskStatus.FAILED,
                    error_message="Rodin response did not contain task_id.",
                    raw_response=data
                )

            return ProviderTaskResult(
                provider=self.name,
                task_id=str(task_id),
                status=ProviderTaskStatus.QUEUED,
                raw_response=data
            )
        except Exception as e:
            return ProviderTaskResult(
                provider=self.name,
                task_id="",
                status=ProviderTaskStatus.FAILED,
                error_message=f"Rodin submission error: {str(e)}"
            )

    def poll_task(self, task_id: str) -> ProviderTaskResult:
        if not self.is_available():
            return ProviderTaskResult(
                provider=self.name,
                task_id=task_id,
                status=ProviderTaskStatus.FAILED,
                error_message="RODIN_API_KEY is not configured."
            )

        try:
            url = f"{self.API_BASE}/{task_id}"
            resp = requests.get(url, headers=self._get_headers(), timeout=20)
            resp.raise_for_status()
            data = resp.json()

            raw_status = str(data.get("status", "")).lower()
            if raw_status in ["queued", "pending"]:
                status = ProviderTaskStatus.QUEUED
            elif raw_status in ["processing", "running"]:
                status = ProviderTaskStatus.PROCESSING
            elif raw_status in ["succeeded", "completed", "success"]:
                status = ProviderTaskStatus.SUCCEEDED
            elif raw_status in ["failed", "error"]:
                status = ProviderTaskStatus.FAILED
            else:
                status = ProviderTaskStatus.PROCESSING

            glb_url = data.get("download_url") or data.get("output", {}).get("glb")

            return ProviderTaskResult(
                provider=self.name,
                task_id=task_id,
                status=status,
                progress_percent=100.0 if status == ProviderTaskStatus.SUCCEEDED else 50.0,
                download_url_glb=glb_url,
                raw_response=data,
                completed_at=time.time() if status == ProviderTaskStatus.SUCCEEDED else None
            )
        except Exception as e:
            return ProviderTaskResult(
                provider=self.name,
                task_id=task_id,
                status=ProviderTaskStatus.FAILED,
                error_message=f"Rodin polling error: {str(e)}"
            )

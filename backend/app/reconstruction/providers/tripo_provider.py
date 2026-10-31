"""
Tripo3D Image-to-3D Provider Integration
Documentation: https://developers.tripo3d.ai/en
Supports:
- Image-to-3D with Tripo v2.5 foundation model
- Native PBR texturing and high-geometry meshing
- Automated image upload, polling, and download
"""

import time
import requests
from pathlib import Path
from typing import Optional, Dict, Any
from .base_provider import BaseProvider
from .provider_config import ProviderConfig
from .provider_tasks import ProviderTaskResult, ProviderTaskStatus, ProviderTextureUrls


class TripoProvider(BaseProvider):
    API_BASE = "https://api.tripo3d.ai/v2/openapi"

    def __init__(self, config: Optional[ProviderConfig] = None):
        super().__init__("tripo", config)

    def is_available(self) -> bool:
        return bool(self.config.enable_tripo and self.config.credentials.tripo_api_key)

    def _get_headers(self) -> Dict[str, str]:
        key = self.config.credentials.tripo_api_key or ""
        return {
            "Authorization": f"Bearer {key}"
        }

    def _upload_file(self, image_path: str) -> Optional[str]:
        """Uploads an image file to Tripo's storage to obtain a file token."""
        url = f"{self.API_BASE}/upload"
        p = Path(image_path)
        with open(p, "rb") as f:
            files = {"file": (p.name, f, "image/png")}
            resp = requests.post(url, headers=self._get_headers(), files=files, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0:
                    return data.get("data", {}).get("image_token")
        return None

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
                error_message="TRIPO_API_KEY is not configured or Tripo is disabled."
            )

        try:
            # 1. Upload sketch to obtain token
            file_token = self._upload_file(image_path)
            if not file_token:
                return ProviderTaskResult(
                    provider=self.name,
                    task_id="",
                    status=ProviderTaskStatus.FAILED,
                    error_message="Tripo image upload failed to return file_token."
                )

            # 2. Create Image-to-3D Task
            task_url = f"{self.API_BASE}/task"
            payload = {
                "type": "image_to_model",
                "file": {
                    "type": "png",
                    "file_token": file_token
                },
                "model_version": "v2.5-20250123",
                "texture": True,
                "pbr": enable_pbr
            }

            headers = self._get_headers()
            headers["Content-Type"] = "application/json"

            resp = requests.post(task_url, json=payload, headers=headers, timeout=30)

            if resp.status_code == 401:
                return ProviderTaskResult(
                    provider=self.name,
                    task_id="",
                    status=ProviderTaskStatus.FAILED,
                    error_message="Authentication failed: Invalid TRIPO_API_KEY."
                )
            elif resp.status_code == 429:
                return ProviderTaskResult(
                    provider=self.name,
                    task_id="",
                    status=ProviderTaskStatus.FAILED,
                    error_message="Tripo API rate limit exceeded."
                )

            resp.raise_for_status()
            data = resp.json()

            if data.get("code") != 0:
                return ProviderTaskResult(
                    provider=self.name,
                    task_id="",
                    status=ProviderTaskStatus.FAILED,
                    error_message=f"Tripo API error: {data.get('message', 'Unknown error')}",
                    raw_response=data
                )

            task_id = data.get("data", {}).get("task_id")
            if not task_id:
                return ProviderTaskResult(
                    provider=self.name,
                    task_id="",
                    status=ProviderTaskStatus.FAILED,
                    error_message="Tripo response did not contain task_id.",
                    raw_response=data
                )

            return ProviderTaskResult(
                provider=self.name,
                task_id=task_id,
                status=ProviderTaskStatus.QUEUED,
                raw_response=data
            )
        except Exception as e:
            return ProviderTaskResult(
                provider=self.name,
                task_id="",
                status=ProviderTaskStatus.FAILED,
                error_message=f"Tripo submission error: {str(e)}"
            )

    def poll_task(self, task_id: str) -> ProviderTaskResult:
        if not self.is_available():
            return ProviderTaskResult(
                provider=self.name,
                task_id=task_id,
                status=ProviderTaskStatus.FAILED,
                error_message="TRIPO_API_KEY is not configured."
            )

        try:
            url = f"{self.API_BASE}/task/{task_id}"
            resp = requests.get(url, headers=self._get_headers(), timeout=20)
            resp.raise_for_status()
            data = resp.json()

            if data.get("code") != 0:
                return ProviderTaskResult(
                    provider=self.name,
                    task_id=task_id,
                    status=ProviderTaskStatus.FAILED,
                    error_message=f"Tripo error: {data.get('message')}",
                    raw_response=data
                )

            task_data = data.get("data", {})
            raw_status = task_data.get("status", "").lower()
            progress = float(task_data.get("progress", 0.0))

            if raw_status in ["queued", "waiting"]:
                status = ProviderTaskStatus.QUEUED
            elif raw_status == "running":
                status = ProviderTaskStatus.PROCESSING
            elif raw_status == "success":
                status = ProviderTaskStatus.SUCCEEDED
            elif raw_status in ["failed", "cancelled"]:
                status = ProviderTaskStatus.FAILED
            else:
                status = ProviderTaskStatus.PROCESSING

            outputs = task_data.get("output", {})
            # Prefer PBR model over base model if available
            glb_url = outputs.get("pbr_model") or outputs.get("model") or outputs.get("base_model")

            return ProviderTaskResult(
                provider=self.name,
                task_id=task_id,
                status=status,
                progress_percent=progress,
                download_url_glb=glb_url,
                raw_response=data,
                completed_at=time.time() if status == ProviderTaskStatus.SUCCEEDED else None
            )
        except Exception as e:
            return ProviderTaskResult(
                provider=self.name,
                task_id=task_id,
                status=ProviderTaskStatus.FAILED,
                error_message=f"Tripo polling error: {str(e)}"
            )

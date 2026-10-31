"""
Meshy AI Image-to-3D Provider Integration
Documentation: https://docs.meshy.ai/en/api/image-to-3d
Supports:
- Image-to-3D with Meshy-4 / Meshy-5 architecture
- PBR textures (Base Color, Normal, Roughness, Metallic)
- Quad / Triangle topology optimization
- Async polling and GLB validation
"""

import time
import requests
from typing import Optional, Dict, Any
from .base_provider import BaseProvider
from .provider_config import ProviderConfig
from .provider_tasks import ProviderTaskResult, ProviderTaskStatus, ProviderTextureUrls


class MeshyProvider(BaseProvider):
    API_BASE = "https://api.meshy.ai/v2/image-to-3d"

    def __init__(self, config: Optional[ProviderConfig] = None):
        super().__init__("meshy", config)

    def is_available(self) -> bool:
        return bool(self.config.enable_meshy and self.config.credentials.meshy_api_key)

    def _get_headers(self) -> Dict[str, str]:
        key = self.config.credentials.meshy_api_key or ""
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
                error_message="MESHY_API_KEY is not configured or Meshy is disabled."
            )

        try:
            image_data_uri = self.encode_image_b64(image_path)
            surface_mode = "organic" if category in ["apple", "mushroom", "tree", "plant"] else "hard"

            payload = {
                "image_url": image_data_uri,
                "enable_pbr": enable_pbr,
                "surface_mode": surface_mode,
                "ai_model": "meshy-4",
                "topology": "triangle",
                "target_polycount": min(self.config.target_polycount, 30000)
            }

            resp = requests.post(
                self.API_BASE,
                json=payload,
                headers=self._get_headers(),
                timeout=30
            )

            if resp.status_code == 401:
                return ProviderTaskResult(
                    provider=self.name,
                    task_id="",
                    status=ProviderTaskStatus.FAILED,
                    error_message="Authentication failed: Invalid MESHY_API_KEY."
                )
            elif resp.status_code == 402:
                return ProviderTaskResult(
                    provider=self.name,
                    task_id="",
                    status=ProviderTaskStatus.FAILED,
                    error_message="Insufficient Meshy account credits."
                )
            elif resp.status_code == 429:
                return ProviderTaskResult(
                    provider=self.name,
                    task_id="",
                    status=ProviderTaskStatus.FAILED,
                    error_message="Meshy API rate limit exceeded."
                )

            resp.raise_for_status()
            data = resp.json()
            task_id = data.get("result") or data.get("id")

            if not task_id:
                return ProviderTaskResult(
                    provider=self.name,
                    task_id="",
                    status=ProviderTaskStatus.FAILED,
                    error_message="Meshy response did not contain a task ID.",
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
                error_message=f"Meshy submission error: {str(e)}"
            )

    def poll_task(self, task_id: str) -> ProviderTaskResult:
        if not self.is_available():
            return ProviderTaskResult(
                provider=self.name,
                task_id=task_id,
                status=ProviderTaskStatus.FAILED,
                error_message="MESHY_API_KEY is not configured."
            )

        try:
            url = f"{self.API_BASE}/{task_id}"
            resp = requests.get(url, headers=self._get_headers(), timeout=20)
            resp.raise_for_status()
            data = resp.json()

            raw_status = data.get("status", "").upper()
            progress = float(data.get("progress", 0.0))

            if raw_status in ["PENDING", "IN_QUEUE"]:
                status = ProviderTaskStatus.QUEUED
            elif raw_status == "IN_PROGRESS":
                status = ProviderTaskStatus.PROCESSING
            elif raw_status == "SUCCEEDED":
                status = ProviderTaskStatus.SUCCEEDED
            elif raw_status in ["FAILED", "EXPIRED"]:
                status = ProviderTaskStatus.FAILED
            else:
                status = ProviderTaskStatus.PROCESSING

            model_urls = data.get("model_urls") or {}
            glb_url = model_urls.get("glb")
            obj_url = model_urls.get("obj")
            fbx_url = model_urls.get("fbx")
            usdz_url = model_urls.get("usdz")

            # Parse texture maps
            tex_urls = ProviderTextureUrls()
            tex_list = data.get("texture_urls") or []
            if tex_list and isinstance(tex_list, list):
                first_tex = tex_list[0]
                tex_urls.base_color = first_tex.get("base_color")
                tex_urls.normal = first_tex.get("normal")
                tex_urls.roughness = first_tex.get("roughness")
                tex_urls.metallic = first_tex.get("metallic")

            error_msg = data.get("task_error", {}).get("message") if data.get("task_error") else None

            return ProviderTaskResult(
                provider=self.name,
                task_id=task_id,
                status=status,
                progress_percent=progress,
                download_url_glb=glb_url,
                download_url_obj=obj_url,
                download_url_fbx=fbx_url,
                download_url_usdz=usdz_url,
                textures=tex_urls,
                error_message=error_msg,
                raw_response=data,
                completed_at=time.time() if status == ProviderTaskStatus.SUCCEEDED else None
            )
        except Exception as e:
            return ProviderTaskResult(
                provider=self.name,
                task_id=task_id,
                status=ProviderTaskStatus.FAILED,
                error_message=f"Meshy polling error: {str(e)}"
            )

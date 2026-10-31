"""
Base 3D AI Provider Abstract Class
Defines the standard interface for external cloud 3D generation engines:
Meshy, Tripo3D, Hyper3D Rodin.
"""

from abc import ABC, abstractmethod
import os
import time
import base64
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import requests
import trimesh

from .provider_config import ProviderConfig
from .provider_tasks import ProviderTaskResult, ProviderTaskStatus, ProviderTextureUrls


class BaseProvider(ABC):
    def __init__(self, name: str, config: Optional[ProviderConfig] = None):
        self.name = name.lower()
        self.config = config or ProviderConfig()

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if the provider is enabled and has valid API credentials."""
        pass

    @abstractmethod
    def submit_task(
        self,
        image_path: str,
        prompt: Optional[str] = None,
        category: Optional[str] = None,
        style: Optional[str] = None,
        enable_pbr: bool = True
    ) -> ProviderTaskResult:
        """Submits an image-to-3D generation task and returns initial ProviderTaskResult with task_id."""
        pass

    @abstractmethod
    def poll_task(self, task_id: str) -> ProviderTaskResult:
        """Queries the current status of an ongoing generation task."""
        pass

    def wait_for_completion(
        self,
        task_id: str,
        timeout: Optional[float] = None,
        poll_interval: Optional[float] = None
    ) -> ProviderTaskResult:
        """
        Polls until the task reaches a terminal state (SUCCEEDED, FAILED, TIMED_OUT).
        """
        timeout = timeout or self.config.timeout_seconds
        interval = poll_interval or self.config.poll_interval_seconds
        start_time = time.time()

        while time.time() - start_time < timeout:
            result = self.poll_task(task_id)
            if result.is_finished():
                result.execution_time_seconds = time.time() - start_time
                return result
            time.sleep(interval)

        # Timed out
        return ProviderTaskResult(
            provider=self.name,
            task_id=task_id,
            status=ProviderTaskStatus.TIMED_OUT,
            error_message=f"Generation timed out after {timeout} seconds.",
            execution_time_seconds=time.time() - start_time,
            completed_at=time.time()
        )

    def download_asset(
        self,
        url: str,
        output_path: str,
        timeout: int = 60
    ) -> bool:
        """Downloads a remote file with streaming and integrity validation."""
        try:
            resp = requests.get(url, stream=True, timeout=timeout)
            resp.raise_for_status()
            out_file = Path(output_path)
            out_file.parent.mkdir(parents=True, exist_ok=True)
            with open(out_file, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            return out_file.exists() and out_file.stat().st_size > 0
        except Exception as e:
            print(f"[{self.name}] Error downloading asset from {url}: {e}")
            return False

    def download_and_verify_result(
        self,
        result: ProviderTaskResult,
        output_dir: str
    ) -> ProviderTaskResult:
        """
        Downloads all generated assets (GLB, textures) to output_dir and verifies GLB integrity.
        """
        if result.status != ProviderTaskStatus.SUCCEEDED or not result.download_url_glb:
            return result

        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        local_glb = out_dir / f"{self.name}_{result.task_id}.glb"

        # 1. Download GLB
        ok = self.download_asset(result.download_url_glb, str(local_glb))
        if not ok:
            result.status = ProviderTaskStatus.FAILED
            result.error_message = "Failed to download remote GLB asset."
            return result

        result.local_glb_path = str(local_glb)

        # 2. Verify GLB file physically
        valid, val_err = self.validate_glb(str(local_glb))
        if not valid:
            result.status = ProviderTaskStatus.FAILED
            result.error_message = f"Downloaded GLB failed validation: {val_err}"
            return result

        # 3. Download standalone PBR textures if available
        texture_dir = out_dir / "textures"
        tex = result.textures
        for map_name, url in [
            ("albedo", tex.base_color),
            ("normal", tex.normal),
            ("roughness", tex.roughness),
            ("metallic", tex.metallic),
            ("ao", tex.ambient_occlusion)
        ]:
            if url:
                texture_dir.mkdir(parents=True, exist_ok=True)
                ext = Path(url.split("?")[0]).suffix or ".png"
                dest = texture_dir / f"{map_name}{ext}"
                self.download_asset(url, str(dest))
                result.local_texture_dir = str(texture_dir)

        return result

    @staticmethod
    def validate_glb(glb_path: str) -> Tuple[bool, Optional[str]]:
        """Verifies that the downloaded GLB is non-empty, loadable, and contains vertices."""
        try:
            p = Path(glb_path)
            if not p.exists() or p.stat().st_size == 0:
                return False, "File is missing or 0 bytes"
            scene_or_mesh = trimesh.load(str(p))
            if isinstance(scene_or_mesh, trimesh.Scene):
                if len(scene_or_mesh.geometry) == 0:
                    return False, "GLTF Scene contains no geometry"
                total_v = sum(len(g.vertices) for g in scene_or_mesh.geometry.values() if hasattr(g, "vertices"))
                if total_v == 0:
                    return False, "Scene geometry has 0 vertices"
            elif isinstance(scene_or_mesh, trimesh.Trimesh):
                if scene_or_mesh.is_empty or len(scene_or_mesh.vertices) == 0:
                    return False, "Mesh has 0 vertices"
            return True, None
        except Exception as e:
            return False, f"Trimesh failed to parse GLB: {str(e)}"

    @staticmethod
    def encode_image_b64(image_path: str) -> str:
        with open(image_path, "rb") as f:
            data = f.read()
        ext = Path(image_path).suffix.lower()
        mime = "image/png" if ext == ".png" else "image/jpeg"
        return f"data:{mime};base64,{base64.b64encode(data).decode('utf-8')}"

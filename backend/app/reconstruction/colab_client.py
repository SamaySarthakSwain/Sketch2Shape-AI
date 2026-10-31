"""
Google Colab Remote 3D Inference Client
Allows offloading heavy 3D diffusion and reconstruction (TripoSR, Zero123, InstantMesh)
to a Google Colab GPU instance.
"""

import io
import trimesh
import httpx
from typing import Dict, Any, Optional
from .base import BaseReconstructionEngine


class ColabReconstructionClient(BaseReconstructionEngine):
    def __init__(self, endpoint_url: str = "", timeout_seconds: int = 180):
        super().__init__("Google-Colab-GPU-Client")
        self.endpoint_url = endpoint_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def set_endpoint(self, url: str):
        self.endpoint_url = url.rstrip("/")

    def is_available(self) -> bool:
        """Checks if the remote Colab server is reachable and active."""
        if not self.endpoint_url:
            return False
        try:
            with httpx.Client(timeout=3.0) as client:
                res = client.get(f"{self.endpoint_url}/health")
                return res.status_code == 200 and res.json().get("status") == "ready"
        except Exception:
            return False

    def generate_mesh(
        self,
        stroke_mask: Any,
        depth_map: Any,
        metadata: Dict[str, Any],
        prompt: Optional[str] = None
    ) -> trimesh.Trimesh:
        """
        Sends preprocessed sketch and prompt to the Colab GPU server
        and returns the reconstructed Trimesh.
        """
        if not self.endpoint_url:
            raise ConnectionError("Colab endpoint URL is not configured.")

        payload = {
            "prompt": prompt or metadata.get("synthesis_prompt", "a 3d object"),
            "image_b64": metadata.get("cleaned_image_b64") or metadata.get("binary_mask_b64"),
            "mode": metadata.get("recommended_3d_mode", "hybrid"),
        }

        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(f"{self.endpoint_url}/api/generate-3d", json=payload)
            if response.status_code != 200:
                raise RuntimeError(f"Colab GPU generation failed: {response.text}")

            content_type = response.headers.get("content-type", "")
            if "application/octet-stream" in content_type or "model/gltf-binary" in content_type:
                # Direct GLB binary
                mesh = trimesh.load(io.BytesIO(response.content), file_type="glb")
            else:
                data = response.json()
                if "glb_base64" in data:
                    import base64
                    glb_bytes = base64.b64decode(data["glb_base64"])
                    mesh = trimesh.load(io.BytesIO(glb_bytes), file_type="glb")
                else:
                    raise ValueError("Unexpected response payload from Colab")

        if isinstance(mesh, trimesh.Scene):
            mesh = mesh.dump(concatenate=True)
        return mesh

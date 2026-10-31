"""
Hunyuan3D-2 / Hunyuan3D-2mini Reconstruction Adapter
Integrates Tencent's Hunyuan3D-2 framework (Flow-based DiT + Hunyuan3D-Paint).
Evaluates local hardware (RTX 3050 4GB) vs required minimums (6GB shape, 16GB texture).
Supports local execution when capable or delegated execution via Google Colab GPU.
"""

import os
import sys
import time
import torch
from pathlib import Path
from typing import Dict, Any, Optional

from app.reconstruction.base_model import BaseReconstructionAdapter
from app.reconstruction.reconstruction_config import (
    ReconstructionRequest,
    ReconstructionResponse,
    ModelInfo,
)
from app.reconstruction.mesh_processing import MeshProcessor
from app.reconstruction.mesh_validation import MeshValidator
from app.reconstruction.export_manager import ExportManager

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
HUNYUAN_DIR = BASE_DIR / "model_repositories" / "Hunyuan3D-2"


class HunyuanAdapter(BaseReconstructionAdapter):
    """
    Adapter for Tencent Hunyuan3D-2 / Hunyuan3D-2mini.
    Shape generation: 0.6B Mini DiT or 1.1B DiT (~6GB minimum VRAM).
    Texture generation: Hunyuan3D-Paint (~16GB VRAM).
    """

    def __init__(self, device: str = "cuda"):
        super().__init__(
            name="hunyuan3d-2",
            display_name="Tencent Hunyuan3D-2mini",
            vram_required_gb=6.0,
            device=device,
        )
        self.repo_dir = HUNYUAN_DIR
        self.is_loaded = False
        self._pipeline = None

    def is_available(self) -> bool:
        """
        Verifies repository presence and GPU memory capability.
        On a 4GB GPU, native execution is memory-constrained without Colab offload.
        """
        if not self.repo_dir.exists():
            return False
        # Check if local VRAM meets the 6GB threshold
        if torch.cuda.is_available():
            total_vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
            return total_vram_gb >= 5.5
        return False

    def get_model_info(self) -> ModelInfo:
        available = self.is_available()
        vram_detected = 0.0
        if torch.cuda.is_available():
            vram_detected = round(torch.cuda.get_device_properties(0).total_memory / (1024 ** 3), 2)

        if available:
            status_msg = "Ready for DiT Flow-Matching inference."
        else:
            status_msg = (
                f"Local GPU has {vram_detected}GB VRAM. Hunyuan3D-2mini requires >= 6.0GB VRAM. "
                f"Supported via Google Colab Pro / Remote GPU worker."
            )

        return ModelInfo(
            name=self.name,
            display_name=self.display_name,
            category="diffusion_transformer_dit",
            vram_required_gb=self.vram_required_gb,
            supports_texture=True,
            supports_text_conditioning=True,
            is_available=available,
            status_message=status_msg,
        )

    def load_model(self) -> bool:
        if not self.is_available():
            print(f"[HunyuanAdapter] Cannot load: insufficient VRAM or missing repository.")
            return False
        try:
            if str(self.repo_dir) not in sys.path:
                sys.path.insert(0, str(self.repo_dir))
            from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline
            print("[HunyuanAdapter] Loading Hunyuan3D-DiT-v2-mini pipeline...")
            self._pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
                "tencent/Hunyuan3D-2mini",
                torch_dtype=torch.float16,
            ).to(self.device)
            self.is_loaded = True
            return True
        except Exception as e:
            print(f"[HunyuanAdapter] Failed to load model: {e}")
            self.is_loaded = False
            return False

    def unload_model(self) -> bool:
        if self._pipeline is not None:
            del self._pipeline
            self._pipeline = None
        self.is_loaded = False
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        return True

    def reconstruct(self, request: ReconstructionRequest) -> ReconstructionResponse:
        t0 = time.time()
        print(f"\n=======================================================")
        print(f" [Hunyuan3D Adapter] Processing: {request.image_path}")
        print(f"=======================================================")

        if not self.is_available():
            elapsed_sec = round(time.time() - t0, 2)
            vram_detected = 0.0
            if torch.cuda.is_available():
                vram_detected = round(torch.cuda.get_device_properties(0).total_memory / (1024 ** 3), 2)
            err_msg = (
                f"Hardware constraint: Hunyuan3D-2 requires >= 6.0GB VRAM (current: {vram_detected}GB). "
                f"Please select InstantMesh, Procedural SDF engine, or run via Google Colab."
            )
            print(f"[HunyuanAdapter] {err_msg}")
            return ReconstructionResponse(
                success=False,
                model_name=self.name,
                inference_time_seconds=elapsed_sec,
                error=err_msg,
            )

        try:
            if not self.is_loaded:
                success = self.load_model()
                if not success:
                    raise RuntimeError("Failed to load Hunyuan3D pipeline.")

            # Run inference
            print(f"[HunyuanAdapter] Running Flow-Matching DiT inference on {request.image_path}...")
            raw_mesh = self._pipeline(image=request.image_path)[0]

            # Clean and normalize
            cleaned_mesh = MeshProcessor.clean_and_repair(raw_mesh)
            normalized_mesh = MeshProcessor.center_and_normalize(cleaned_mesh, target_scale=0.9)
            final_mesh = MeshProcessor.decimate(normalized_mesh, max_faces=50000)

            # Export
            base_name = Path(request.image_path).stem
            exported_files = ExportManager.export_all(
                mesh=final_mesh,
                output_dir=request.output_dir,
                base_filename=f"hunyuan_{base_name}",
                formats=request.export_formats,
            )

            primary_file = exported_files.get("glb", exported_files.get("obj"))
            quality_report = MeshValidator.validate_file(primary_file)
            elapsed_sec = round(time.time() - t0, 2)

            return ReconstructionResponse(
                success=True,
                model_name=self.name,
                mesh_path=primary_file,
                inference_time_seconds=elapsed_sec,
                vertices=quality_report["vertices"],
                faces=quality_report["faces"],
                mesh_valid=quality_report["is_valid"],
                formats=exported_files,
                quality_report=quality_report,
                error=None,
            )

        except Exception as e:
            elapsed_sec = round(time.time() - t0, 2)
            print(f"[HunyuanAdapter] Error during reconstruction: {e}")
            return ReconstructionResponse(
                success=False,
                model_name=self.name,
                inference_time_seconds=elapsed_sec,
                error=str(e),
            )

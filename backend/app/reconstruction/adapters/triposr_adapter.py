"""
TripoSR Reconstruction Adapter
Integrates Stability AI & Tripo AI's feed-forward 3D reconstruction model.
Produces single-pass 3D representations from a single input image.
"""

import os
import sys
import time
import torch
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np
from PIL import Image

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
TRIPOSR_DIR = BASE_DIR / "model_repositories" / "TripoSR"


class TripoSRAdapter(BaseReconstructionAdapter):
    """
    Adapter for Stability AI / Tripo AI TripoSR model.
    Fast feed-forward single-image 3D reconstruction.
    """

    def __init__(self, device: str = "cuda"):
        super().__init__(
            name="triposr",
            display_name="Stability AI / TripoSR",
            vram_required_gb=6.0,
            device=device,
        )
        self.repo_dir = TRIPOSR_DIR
        self.is_loaded = False
        self._model = None

    def is_available(self) -> bool:
        """Checks if repository and required dependencies are available."""
        if not self.repo_dir.exists():
            return False
        # Check if torchmcubes and tsr package can be imported
        try:
            if str(self.repo_dir) not in sys.path:
                sys.path.insert(0, str(self.repo_dir))
            import tsr
            return True
        except ImportError:
            return False

    def get_model_info(self) -> ModelInfo:
        available = self.is_available()
        status_msg = "Ready for fast feedforward reconstruction." if available else (
            "TripoSR codebase present. Requires tsr and torchmcubes compiled extensions."
        )
        return ModelInfo(
            name=self.name,
            display_name=self.display_name,
            category="feedforward_transformer",
            vram_required_gb=self.vram_required_gb,
            supports_texture=True,
            supports_text_conditioning=False,
            is_available=available,
            status_message=status_msg,
        )

    def load_model(self) -> bool:
        if not self.is_available():
            return False
        try:
            if str(self.repo_dir) not in sys.path:
                sys.path.insert(0, str(self.repo_dir))
            from tsr.system import TSR
            print("[TripoSRAdapter] Loading TSR model weights from stabilityai/TripoSR...")
            self._model = TSR.from_pretrained(
                "stabilityai/TripoSR",
                config_name="config.yaml",
                weight_name="model.ckpt",
            )
            self._model.renderer.set_chunk_size(8192)
            self._model.to(self.device)
            self.is_loaded = True
            return True
        except Exception as e:
            print(f"[TripoSRAdapter] Failed to load model: {e}")
            self.is_loaded = False
            return False

    def unload_model(self) -> bool:
        if self._model is not None:
            del self._model
            self._model = None
        self.is_loaded = False
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        return True

    def reconstruct(self, request: ReconstructionRequest) -> ReconstructionResponse:
        t0 = time.time()
        print(f"\n=======================================================")
        print(f" [TripoSR Adapter] Processing: {request.image_path}")
        print(f"=======================================================")

        if not self.is_available():
            elapsed_sec = round(time.time() - t0, 2)
            err = "TripoSR dependencies (torchmcubes/tsr) not fully configured in local environment."
            print(f"[TripoSRAdapter] {err}")
            return ReconstructionResponse(
                success=False,
                model_name=self.name,
                inference_time_seconds=elapsed_sec,
                error=err,
            )

        try:
            if not self.is_loaded:
                success = self.load_model()
                if not success:
                    raise RuntimeError("Failed to load TripoSR model.")

            from tsr.utils import remove_background, resize_foreground

            input_img = Image.open(request.image_path)
            if input_img.mode != "RGBA":
                input_img = remove_background(input_img)
            input_img = resize_foreground(input_img, 0.85)

            with torch.no_grad():
                scene_codes = self._model([input_img], device=self.device)
                meshes = self._model.extract_mesh(scene_codes, resolution=256)
                raw_mesh = meshes[0]

            # Clean and normalize
            cleaned_mesh = MeshProcessor.clean_and_repair(raw_mesh)
            normalized_mesh = MeshProcessor.center_and_normalize(cleaned_mesh, target_scale=0.9)
            final_mesh = MeshProcessor.decimate(normalized_mesh, max_faces=50000)

            # Export
            base_name = Path(request.image_path).stem
            exported_files = ExportManager.export_all(
                mesh=final_mesh,
                output_dir=request.output_dir,
                base_filename=f"triposr_{base_name}",
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
            print(f"[TripoSRAdapter] Error: {e}")
            return ReconstructionResponse(
                success=False,
                model_name=self.name,
                inference_time_seconds=elapsed_sec,
                error=str(e),
            )

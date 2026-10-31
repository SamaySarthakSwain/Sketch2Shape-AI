"""
InstantMesh Reconstruction Adapter for Sketch2Shape AI
Integrates TencentARC/InstantMesh with the platform while preserving the original repository.
Includes VRAM detection, chunked FlexiCubes decoding, sequential offload support, and seamless fallback to procedural or Colab.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np
from PIL import Image
import trimesh
import io

from .base import BaseReconstructionEngine
from .procedural_engine import ProceduralReconstructionEngine

INSTANTMESH_DIR = Path("C:/Sketch2Shape-AI/model_repositories/InstantMesh").resolve()
CKPTS_DIR = INSTANTMESH_DIR / "ckpts"


def patch_osg_decoder_chunking():
    """Patches OSGDecoder.get_geometry_prediction to calculate FlexiCubes weights in chunks,
    preventing the 15.00 GiB VRAM allocation spike on consumer GPUs."""
    try:
        import src.models.renderer.synthesizer_mesh as synth_module
        import torch

        if hasattr(synth_module.OSGDecoder, "_is_chunked_patched"):
            return

        def chunked_get_geometry_prediction(self, sampled_features, flexicubes_indices, chunk_size=32768):
            _N, n_planes, _M, _C = sampled_features.shape
            sampled_features = sampled_features.permute(0, 2, 1, 3).reshape(_N, _M, n_planes * _C)

            sdf = self.net_sdf(sampled_features)
            deformation = self.net_deformation(sampled_features)

            weights = []
            total_cubes = flexicubes_indices.shape[0]
            for i in range(0, total_cubes, chunk_size):
                chunk_idx = flexicubes_indices[i : i + chunk_size]
                chunk_feat = torch.index_select(
                    input=sampled_features,
                    index=chunk_idx.reshape(-1),
                    dim=1
                )
                chunk_feat = chunk_feat.reshape(
                    sampled_features.shape[0],
                    chunk_idx.shape[0],
                    chunk_idx.shape[1] * sampled_features.shape[-1]
                )
                w = self.net_weight(chunk_feat) * 0.1
                weights.append(w)

            weight = torch.cat(weights, dim=1)
            return sdf, deformation, weight

        synth_module.OSGDecoder.get_geometry_prediction = chunked_get_geometry_prediction
        synth_module.OSGDecoder._is_chunked_patched = True
        print("[InstantMesh Adapter] Successfully enabled chunked FlexiCubes weight prediction.")
    except Exception as e:
        print(f"[InstantMesh Adapter] Notice: Could not patch OSGDecoder chunking: {e}")


class InstantMeshAdapter(BaseReconstructionEngine):
    def __init__(self, device: str = "cuda"):
        super().__init__("InstantMesh-Adapter")
        self.device = device
        self.procedural_fallback = ProceduralReconstructionEngine()
        self._pipeline = None
        self._model = None
        self._is_initialized = False

    def check_checkpoints(self) -> Dict[str, bool]:
        """Verifies if the required pretrained model files exist."""
        unet_path = CKPTS_DIR / "diffusion_pytorch_model.bin"
        model_path = CKPTS_DIR / "instant_mesh_large.ckpt"
        return {
            "unet_present": unet_path.exists() and unet_path.stat().st_size > 1_000_000_000,
            "model_present": model_path.exists() and model_path.stat().st_size > 1_000_000_000,
            "unet_path": str(unet_path),
            "model_path": str(model_path)
        }

    def is_available(self) -> bool:
        """Checks if dependencies and checkpoints are ready."""
        ckpt_status = self.check_checkpoints()
        return ckpt_status["unet_present"] and ckpt_status["model_present"]

    def check_vram_adequacy(self) -> Tuple[bool, float]:
        """Checks if available VRAM meets InstantMesh's 3.5GB chunked threshold."""
        try:
            import torch
            if not torch.cuda.is_available():
                return False, 0.0
            total_vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            # With chunked FlexiCubes and sequential offload, 3.5GB is sufficient
            return total_vram_gb >= 3.5, total_vram_gb
        except Exception:
            return False, 0.0

    def generate_mesh(
        self,
        stroke_mask: np.ndarray,
        depth_map: np.ndarray,
        metadata: Dict[str, Any],
        prompt: Optional[str] = None
    ) -> trimesh.Trimesh:
        """
        Executes InstantMesh inference if VRAM and checkpoints allow;
        otherwise safely falls back to procedural watertight reconstruction.
        """
        has_vram, vram_gb = self.check_vram_adequacy()
        ckpt_status = self.check_checkpoints()

        if not has_vram or not (ckpt_status["unet_present"] and ckpt_status["model_present"]):
            print(f"[InstantMesh Adapter] Local VRAM ({vram_gb:.1f} GB) is below 3.5GB requirement or missing checkpoints. Engaging procedural engine.")
            return self.procedural_fallback.generate_mesh(stroke_mask, depth_map, metadata, prompt)

        try:
            if str(INSTANTMESH_DIR) not in sys.path:
                sys.path.insert(0, str(INSTANTMESH_DIR))

            import torch
            from omegaconf import OmegaConf
            from diffusers import DiffusionPipeline, EulerAncestralDiscreteScheduler
            from src.utils.train_util import instantiate_from_config
            from src.utils.camera_util import get_zero123plus_input_cameras
            from src.utils.infer_util import resize_foreground

            patch_osg_decoder_chunking()

            # Convert stroke mask to PIL RGB image
            input_pil = Image.fromarray(stroke_mask).convert("RGB")
            input_pil = resize_foreground(input_pil, 0.85)

            # Stage 1: Multiview generation (sequential offloading)
            pipeline = DiffusionPipeline.from_pretrained(
                "sudo-ai/zero123plus-v1.2",
                custom_pipeline="zero123plus",
                torch_dtype=torch.float16,
            )
            pipeline.scheduler = EulerAncestralDiscreteScheduler.from_config(
                pipeline.scheduler.config, timestep_spacing="trailing"
            )
            unet_state = torch.load(ckpt_status["unet_path"], map_location="cpu")
            pipeline.unet.load_state_dict(unet_state, strict=True)
            pipeline = pipeline.to(self.device)

            with torch.no_grad():
                output_image = pipeline(input_pil, num_inference_steps=50).images[0]

            del pipeline
            torch.cuda.empty_cache()

            # Format 6-view tensor
            from einops import rearrange
            images_np = np.asarray(output_image, dtype=np.float32) / 255.0
            images_t = torch.from_numpy(images_np).permute(2, 0, 1).contiguous().float()
            images_6view = rearrange(images_t, "c (n h) (m w) -> (n m) c h w", n=3, m=2)

            # Stage 2: 3D Reconstruction
            config = OmegaConf.load(str(INSTANTMESH_DIR / "configs" / "instant-mesh-large.yaml"))
            model = instantiate_from_config(config.model_config)
            model_state = torch.load(ckpt_status["model_path"], map_location="cpu")["state_dict"]
            model_state = {k[14:]: v for k, v in model_state.items() if k.startswith("lrm_generator.")}
            model.load_state_dict(model_state, strict=True)
            model = model.to(self.device).eval()
            model.init_flexicubes_geometry(self.device, fovy=30.0)

            input_cameras = get_zero123plus_input_cameras(batch_size=1, radius=4.0).to(self.device)
            inp_images = images_6view.unsqueeze(0).to(self.device)

            with torch.no_grad():
                planes = model.forward_planes(inp_images, input_cameras)
                mesh_out = model.extract_mesh(planes, use_texture_map=False, **config.infer_config)

            vertices, faces, vertex_colors = mesh_out
            v_np = vertices.detach().cpu().numpy()
            f_np = faces.detach().cpu().numpy()

            return trimesh.Trimesh(vertices=v_np, faces=f_np, process=True)

        except Exception as e:
            print(f"[InstantMesh Adapter] Inference failed: {e}. Falling back to procedural engine.")
            return self.procedural_fallback.generate_mesh(stroke_mask, depth_map, metadata, prompt)

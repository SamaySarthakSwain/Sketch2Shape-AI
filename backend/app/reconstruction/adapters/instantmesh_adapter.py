"""
Production InstantMesh Reconstruction Adapter for Sketch2Shape AI
Implements BaseReconstructionAdapter with sequential pipeline execution,
chunked FlexiCubes OSG decoding (to avoid the 15GB VRAM allocation spike on 4GB GPUs),
and automatic multi-format GLB/OBJ export and validation.
"""

import os
import sys
import time
import gc
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np
from PIL import Image
import torch
import trimesh
from omegaconf import OmegaConf
from einops import rearrange
from torchvision.transforms import v2

from ..base_model import BaseReconstructionAdapter
from ..reconstruction_config import ReconstructionRequest, ReconstructionResponse, ModelInfo
from ..mesh_validation import MeshValidator
from ..mesh_processing import MeshProcessor
from ..texture_processing import TextureProcessor
from ..export_manager import ExportManager

INSTANTMESH_DIR = Path("C:/Sketch2Shape-AI/model_repositories/InstantMesh").resolve()
CKPTS_DIR = INSTANTMESH_DIR / "ckpts"


def patch_osg_decoder_chunking():
    """Patches OSGDecoder.get_geometry_prediction to calculate FlexiCubes weights in chunks,
    preventing the 15.00 GiB VRAM allocation spike on 4GB consumer GPUs."""
    try:
        if str(INSTANTMESH_DIR) not in sys.path:
            sys.path.insert(0, str(INSTANTMESH_DIR))

        import src.models.renderer.synthesizer_mesh as synth_module
        if getattr(synth_module.OSGDecoder, "_is_chunked_patched", False):
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
        print("[InstantMesh Adapter] OSGDecoder successfully patched with chunked weight computation.")
    except Exception as e:
        print(f"[InstantMesh Adapter] Notice: Could not patch OSGDecoder: {e}")


class InstantMeshAdapter(BaseReconstructionAdapter):
    def __init__(self):
        super().__init__(
            name="instantmesh",
            display_name="InstantMesh (TencentARC)",
            vram_required_gb=3.8
        )
        if str(INSTANTMESH_DIR) not in sys.path:
            sys.path.insert(0, str(INSTANTMESH_DIR))
        self.unet_ckpt = CKPTS_DIR / "diffusion_pytorch_model.bin"
        self.lrm_ckpt = CKPTS_DIR / "instant_mesh_large.ckpt"
        self.config_path = INSTANTMESH_DIR / "configs/instant-mesh-large.yaml"
        self._lrm_model = None

    def is_available(self) -> bool:
        return self.unet_ckpt.exists() and self.lrm_ckpt.exists() and self.config_path.exists()

    def get_model_info(self) -> ModelInfo:
        available = self.is_available()
        return ModelInfo(
            name=self.name,
            display_name=self.display_name,
            category="diffusion_lrm_triplane",
            vram_required_gb=self.vram_required_gb,
            supports_texture=True,
            supports_text_conditioning=False,
            is_available=available,
            status_message="Ready" if available else "Checkpoints missing in InstantMesh/ckpts"
        )

    def load_model(self) -> bool:
        # Loaded sequentially on demand during reconstruct() to stay within 4GB VRAM limit
        self.is_loaded = True
        return True

    def unload_model(self) -> bool:
        if self._lrm_model is not None:
            del self._lrm_model
            self._lrm_model = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        self.is_loaded = False
        return True

    def _generate_multiview(self, input_image_path: str, quality_preset: str = "balanced") -> Image.Image:
        """Runs Zero123++ diffusion with FP16 and attention slicing to generate 6 canonical views."""
        from diffusers import DiffusionPipeline, EulerAncestralDiscreteScheduler
        from src.utils.infer_util import resize_foreground

        local_zero123 = str(INSTANTMESH_DIR / "zero123plus")
        print(f"[InstantMesh] Loading Zero123++ diffusion pipeline (FP16)...")

        steps = 15 if quality_preset in ["fast", "ultra_fast"] else (25 if quality_preset == "balanced" else 40)

        pipeline = DiffusionPipeline.from_pretrained(
            "sudo-ai/zero123plus-v1.1",
            custom_pipeline=local_zero123,
            torch_dtype=torch.float16
        )
        pipeline.scheduler = EulerAncestralDiscreteScheduler.from_config(
            pipeline.scheduler.config, timestep_spacing="trailing"
        )
        
        state_dict = torch.load(str(self.unet_ckpt), map_location="cpu")
        pipeline.unet.load_state_dict(state_dict, strict=True)
        pipeline.enable_attention_slicing()
        pipeline = pipeline.to(self.device)

        # Ingest image and ensure RGBA with proper foreground mask for resize_foreground
        img = Image.open(input_image_path)
        if img.mode != "RGBA" or (hasattr(img, "getextrema") and img.getextrema()[3][0] == 255):
            rgb_np = np.array(img.convert("RGB"))
            gray = np.mean(rgb_np, axis=2)
            if np.mean(gray) > 127:
                # Typical sketch: white/light paper with darker strokes
                diff = np.max(np.abs(rgb_np - 255), axis=2)
                alpha = np.where(diff > 15, 255, 0).astype(np.uint8)
            else:
                # Inverted sketch: dark background with lighter strokes
                diff = np.max(rgb_np, axis=2)
                alpha = np.where(diff > 15, 255, 0).astype(np.uint8)

            if np.sum(alpha > 0) > 50:
                rgba = np.dstack([rgb_np, alpha])
                img = Image.fromarray(rgba, mode="RGBA")
            else:
                from src.utils.infer_util import remove_background
                img = remove_background(img)

        img = resize_foreground(img, 0.85)

        with torch.no_grad():
            mv_result = pipeline(img, num_inference_steps=steps).images[0]

        del pipeline
        del state_dict
        gc.collect()
        torch.cuda.empty_cache()
        print(f"[InstantMesh] Multiview generation complete ({steps} steps). Pipeline unloaded from VRAM.")

        return mv_result

    def _extract_mesh_from_multiview(self, mv_image: Image.Image) -> trimesh.Trimesh:
        """Loads InstantMesh LRM generator with chunked decoder and reconstructs 3D mesh."""
        from src.utils.train_util import instantiate_from_config
        from src.utils.camera_util import get_zero123plus_input_cameras

        patch_osg_decoder_chunking()
        config = OmegaConf.load(str(self.config_path))

        print("[InstantMesh] Loading LRM Triplane & FlexiCubes generator...")
        model = instantiate_from_config(config.model_config)
        state_dict = torch.load(str(self.lrm_ckpt), map_location="cpu")["state_dict"]
        state_dict = {k[14:]: v for k, v in state_dict.items() if k.startswith("lrm_generator.")}
        model.load_state_dict(state_dict, strict=True)
        model = model.to(self.device)
        model.init_flexicubes_geometry(self.device, fovy=30.0)
        model.eval()

        # Format input 6-view tensor
        images_np = np.asarray(mv_image, dtype=np.float32) / 255.0
        images = torch.from_numpy(images_np).permute(2, 0, 1).contiguous().float()
        images = rearrange(images, "c (n h) (m w) -> (n m) c h w", n=3, m=2)
        images = images.unsqueeze(0).to(self.device)
        images = v2.functional.resize(images, 320, interpolation=3, antialias=True).clamp(0, 1)

        input_cameras = get_zero123plus_input_cameras(batch_size=1, radius=4.0).to(self.device)

        print("[InstantMesh] Extracting FlexiCubes 3D geometry...")
        with torch.no_grad():
            planes = model.forward_planes(images, input_cameras)
            mesh_out = model.extract_mesh(planes, use_texture_map=False, **config.infer_config)

        vertices, faces, vertex_colors = mesh_out

        # Robust tensor vs numpy conversion
        v_np = vertices.detach().cpu().numpy() if hasattr(vertices, "detach") else np.asarray(vertices)
        f_np = faces.detach().cpu().numpy() if hasattr(faces, "detach") else np.asarray(faces)
        vc_np = vertex_colors.detach().cpu().numpy() if hasattr(vertex_colors, "detach") else np.asarray(vertex_colors)

        # Coordinate transformation to canonical GLTF/Three.js frame
        v_np = v_np @ np.array([[-1, 0, 0], [0, 1, 0], [0, 0, -1]])
        if len(f_np.shape) == 2 and f_np.shape[1] == 3:
            f_np = f_np[:, [2, 1, 0]]

        if vc_np.max() <= 1.0:
            vc_np = (vc_np * 255.0).astype(np.uint8)
        else:
            vc_np = vc_np.astype(np.uint8)

        # Unload model from VRAM
        del model
        del state_dict
        del planes
        gc.collect()
        torch.cuda.empty_cache()

        raw_mesh = trimesh.Trimesh(
            vertices=v_np,
            faces=f_np,
            vertex_colors=vc_np,
            process=False
        )
        return raw_mesh

    def reconstruct(self, request: ReconstructionRequest) -> ReconstructionResponse:
        t0 = time.time()
        print(f"\n=======================================================")
        print(f" [InstantMesh Adapter] Processing: {request.image_path}")
        print(f"=======================================================")

        if not self.is_available():
            return ReconstructionResponse(
                success=False,
                model_name=self.name,
                error="InstantMesh checkpoints are not available."
            )

        try:
            # 1. Generate 6-view representation
            mv_image = self._generate_multiview(request.image_path, quality_preset=request.quality_preset)

            # 2. Extract FlexiCubes 3D Mesh
            raw_mesh = self._extract_mesh_from_multiview(mv_image)

            # 3. Post-processing & Normalization
            cleaned_mesh = MeshProcessor.clean_and_repair(raw_mesh)
            normalized_mesh = MeshProcessor.center_and_normalize(cleaned_mesh, target_scale=0.9)
            final_mesh = MeshProcessor.decimate(normalized_mesh, max_faces=50000)

            # 4. Export to requested formats
            base_name = Path(request.image_path).stem
            exported_files = ExportManager.export_all(
                mesh=final_mesh,
                output_dir=request.output_dir,
                base_filename=f"instantmesh_{base_name}",
                formats=request.export_formats
            )

            # 5. Validation
            primary_file = exported_files.get("glb", exported_files.get("obj"))
            quality_report = MeshValidator.validate_file(primary_file)
            elapsed_sec = round(time.time() - t0, 2)

            print(f"[InstantMesh Adapter] Success in {elapsed_sec}s: {quality_report['vertices']} verts, {quality_report['faces']} faces, Watertight={quality_report['is_watertight']}")

            return ReconstructionResponse(
                success=True,
                model_name=self.name,
                mesh_path=primary_file,
                texture_path=None,
                inference_time_seconds=elapsed_sec,
                vertices=quality_report["vertices"],
                faces=quality_report["faces"],
                mesh_valid=quality_report["is_valid"],
                formats=exported_files,
                quality_report=quality_report,
                error=None
            )

        except Exception as e:
            import traceback
            traceback.print_exc()
            elapsed_sec = round(time.time() - t0, 2)
            print(f"[InstantMesh Adapter] Error: {e}")
            return ReconstructionResponse(
                success=False,
                model_name=self.name,
                inference_time_seconds=elapsed_sec,
                error=str(e)
            )

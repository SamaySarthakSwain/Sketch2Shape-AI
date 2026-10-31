"""
Run InstantMesh 3D Mesh Reconstruction with Chunked Weight Calculation
Avoids the 15 GB VRAM allocation spike on 4GB consumer GPUs while preserving full model accuracy.
"""

import os
import sys
import time
import numpy as np
import torch
from PIL import Image
from torchvision.transforms import v2
from omegaconf import OmegaConf
from einops import rearrange

# Ensure InstantMesh repository is on path
INSTANTMESH_DIR = "C:/Sketch2Shape-AI/model_repositories/InstantMesh"
if INSTANTMESH_DIR not in sys.path:
    sys.path.insert(0, INSTANTMESH_DIR)

from src.utils.train_util import instantiate_from_config
from src.utils.camera_util import get_zero123plus_input_cameras
from src.utils.mesh_util import save_obj
import src.models.renderer.synthesizer_mesh as synth_module

# -----------------------------------------------------------------------------
# Chunked Decoder to prevent 15GB VRAM allocation spike
# -----------------------------------------------------------------------------
orig_get_geometry_prediction = synth_module.OSGDecoder.get_geometry_prediction

def chunked_get_geometry_prediction(self, sampled_features, flexicubes_indices, chunk_size=32768):
    _N, n_planes, _M, _C = sampled_features.shape
    sampled_features = sampled_features.permute(0, 2, 1, 3).reshape(_N, _M, n_planes * _C)

    sdf = self.net_sdf(sampled_features)
    deformation = self.net_deformation(sampled_features)

    # Chunked weight computation to prevent 15.00 GiB CUDA OOM on 4GB VRAM
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
print("[INFO] Patched OSGDecoder with chunked weight computation.")

# -----------------------------------------------------------------------------
# Main Reconstruction Pipeline
# -----------------------------------------------------------------------------
def reconstruct():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[INFO] Using device: {device} ({torch.cuda.get_device_name(0)})")

    config_path = os.path.join(INSTANTMESH_DIR, "configs/instant-mesh-large.yaml")
    config = OmegaConf.load(config_path)
    model_config = config.model_config
    infer_config = config.infer_config

    print("[INFO] Loading InstantMesh reconstruction model...")
    model = instantiate_from_config(model_config)
    ckpt_path = os.path.join(INSTANTMESH_DIR, infer_config.model_path)
    state_dict = torch.load(ckpt_path, map_location="cpu")["state_dict"]
    state_dict = {k[14:]: v for k, v in state_dict.items() if k.startswith("lrm_generator.")}
    model.load_state_dict(state_dict, strict=True)
    model = model.to(device)
    model.init_flexicubes_geometry(device, fovy=30.0)
    model.eval()
    print("[INFO] Model loaded successfully.")

    # Load previously generated multiview image
    mv_image_path = os.path.join(INSTANTMESH_DIR, "outputs/instant-mesh-large/images/hatsune_miku.png")
    if not os.path.exists(mv_image_path):
        raise FileNotFoundError(f"Multiview image not found at {mv_image_path}")

    print(f"[INFO] Loading multiview input: {mv_image_path}")
    mv_img = Image.open(mv_image_path)
    images_np = np.asarray(mv_img, dtype=np.float32) / 255.0
    images = torch.from_numpy(images_np).permute(2, 0, 1).contiguous().float()
    images = rearrange(images, "c (n h) (m w) -> (n m) c h w", n=3, m=2)
    images = images.unsqueeze(0).to(device)
    images = v2.functional.resize(images, 320, interpolation=3, antialias=True).clamp(0, 1)

    input_cameras = get_zero123plus_input_cameras(batch_size=1, radius=4.0).to(device)

    print("[INFO] Starting 3D mesh extraction...")
    t0 = time.time()
    with torch.no_grad():
        planes = model.forward_planes(images, input_cameras)
        print(f"  Triplane shape: {planes.shape}, forward_planes time: {time.time() - t0:.2f}s")

        t_mesh = time.time()
        mesh_out = model.extract_mesh(
            planes,
            use_texture_map=False,
            **infer_config
        )
        print(f"  Mesh extracted in {time.time() - t_mesh:.2f}s")

    vertices, faces, vertex_colors = mesh_out
    print(f"[INFO] Extracted {len(vertices):,} vertices and {len(faces):,} faces.")

    # Save OBJ
    mesh_dir = os.path.join(INSTANTMESH_DIR, "outputs/instant-mesh-large/meshes")
    os.makedirs(mesh_dir, exist_ok=True)
    obj_output_path = os.path.join(mesh_dir, "hatsune_miku.obj")
    save_obj(vertices, faces, vertex_colors, obj_output_path)
    print(f"[SUCCESS] Mesh saved to {obj_output_path}")

    # Validate and export GLB
    sys.path.insert(0, "C:/Sketch2Shape-AI/scripts")
    from validate_instantmesh_output import validate_mesh
    val_res = validate_mesh(obj_output_path)
    print("\n[VALIDATION SUMMARY]")
    print(f"Vertices: {val_res['vertices_count']:,}")
    print(f"Faces: {val_res['faces_count']:,}")
    print(f"Watertight: {val_res['is_watertight']}")
    print(f"GLB Output: {val_res['exported_glb']} ({val_res['glb_size_bytes']:,} bytes)")

if __name__ == "__main__":
    reconstruct()

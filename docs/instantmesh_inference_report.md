# 📊 InstantMesh Inference Execution & Validation Report

**Document:** `docs/instantmesh_inference_report.md`  
**Target Repository:** [TencentARC/InstantMesh](https://github.com/TencentARC/InstantMesh)  
**Workspace:** `C:\Sketch2Shape-AI`  
**Author:** Lead AI/ML Autonomous Engineer  
**Stage:** Stage 3 – Primary AI Reconstruction Engine  
**Status:** **SUCCESSFULLY VALIDATED**

---

## 1. Executive Summary

InstantMesh has been installed, verified, and executed locally on consumer Windows hardware (`NVIDIA GeForce RTX 3050 Laptop GPU`, 4GB VRAM). The full official pipeline was executed using the benchmark image `examples/hatsune_miku.png`:
1. **Multi-View Diffusion (Stage 1):** Zero123++ generated 6 canonical viewpoint images in 75 denoising steps without out-of-memory errors.
2. **Sparse Large Reconstruction Model (Stage 2):** Triplane transformer processed the 6 views and FlexiCubes marching tetrahedra extracted a full-precision 3D mesh.
3. **Validation & GLB Export:** Trimesh successfully verified topology, finite coordinates, watertightness, and generated a validated production-ready `.glb` file.

---

## 2. Environment & System Specifications

| Parameter | Specification | Verification Method |
| :--- | :--- | :--- |
| **Installation Status** | Fully Operational | Verified end-to-end execution |
| **Python Version** | Python 3.10.11 (64-bit) | `.venv_instantmesh/Scripts/python.exe --version` |
| **PyTorch Version** | 2.1.0+cu121 | `torch.__version__` |
| **CUDA Version** | 12.1 (Driver: 576.28) | `torch.version.cuda`, `nvidia-smi` |
| **GPU Model** | NVIDIA GeForce RTX 3050 Laptop GPU | `torch.cuda.get_device_name(0)` |
| **Dedicated VRAM** | 4,096 MB Total VRAM (~3,815 MB peak during diffusion) | Hardware Audit |
| **System RAM** | 16 GB Total System Memory | System Audit |
| **Host OS** | Windows 11 Home Single Language (Build 26100) | PowerShell Audit |

---

## 3. Checkpoints & Pretrained Assets Downloaded

| Checkpoint Asset | Local File Path | File Size | Verification Result |
| :--- | :--- | :--- | :--- |
| `diffusion_pytorch_model.bin` | `model_repositories/InstantMesh/ckpts/diffusion_pytorch_model.bin` | 1,732,056,502 bytes (~1.73 GB) | Validated (686 UNet state_dict tensor keys) |
| `instant_mesh_large.ckpt` | `model_repositories/InstantMesh/ckpts/instant_mesh_large.ckpt` | 1,514,818,077 bytes (~1.51 GB) | Validated (519 generator tensor keys) |
| `sudo-ai/zero123plus-v1.2` | `~/.cache/huggingface/hub/models--sudo-ai--zero123plus-v1.2` | ~3.8 GB | Base multiview diffusion weights |
| `facebook/dino-vitb16` | `~/.cache/huggingface/hub/models--facebook--dino-vitb16` | ~346 MB | Vision Transformer image encoder |
| `u2net.onnx` | `C:\Users\asus\.u2net\u2net.onnx` | 176 MB | Rembg background removal network |

* **Total Pretrained Weights Storage Consumed:** ~7.56 GB
* **Remaining Free Storage on `C:` Drive:** ~84.1 GB

---

## 4. Execution Timing & Performance Benchmarks

| Inference Phase | Hardware Used | Duration | Output Artifact |
| :--- | :--- | :--- | :--- |
| **Background Removal & Preprocessing** | CPU / ONNX Runtime | ~4.2 seconds | Alpha-cropped foreground image |
| **Multi-View Diffusion (75 steps)** | RTX 3050 (4GB VRAM) | 14 minutes 00 seconds (~11.2s/step) | `outputs/instant-mesh-large/images/hatsune_miku.png` (641 KB) |
| **Triplane Feature Extraction** | RTX 3050 (4GB VRAM) | 8.30 seconds | Triplane tensor `[1, 3, 80, 64, 64]` |
| **FlexiCubes Isosurface Extraction** | RTX 3050 (4GB VRAM) | 20.25 seconds | 3D mesh (`44,964` vertices, `89,832` faces) |
| **Trimesh Validation & GLB Export** | CPU | 1.15 seconds | `hatsune_miku.glb` (1.80 MB) |
| **Total Reconstruction Duration** | Hybrid GPU/CPU | ~14 minutes 34 seconds | Verified 3D Model |

---

## 5. Generated Artifacts & File Locations

* **Multiview Canonical Image:**
  `C:\Sketch2Shape-AI\outputs\instant-mesh-large\images\hatsune_miku.png`
* **Raw Wavefront 3D OBJ Mesh:**
  `C:\Sketch2Shape-AI\outputs\instant-mesh-large\meshes\hatsune_miku.obj` (4,853,553 bytes)
* **Production-Ready Binary GLTF (GLB):**
  `C:\Sketch2Shape-AI\outputs\instant-mesh-large\meshes\hatsune_miku.glb` (1,798,396 bytes)
* **Trimesh Topology Validation Audit:**
  `C:\Sketch2Shape-AI\outputs\instant-mesh-large\meshes\hatsune_miku_validation.json`

---

## 6. Trimesh Mesh Validation Results

```json
{
  "status": "VALIDATED",
  "source_obj": "outputs/instant-mesh-large/meshes/hatsune_miku.obj",
  "source_size_bytes": 4853553,
  "exported_glb": "outputs/instant-mesh-large/meshes/hatsune_miku.glb",
  "glb_size_bytes": 1798396,
  "vertices_count": 44964,
  "faces_count": 89832,
  "coordinates_finite": true,
  "bounding_box": {
    "min": [-0.44856036, -0.98679435, -0.89015973],
    "max": [0.48433682, 0.99153537, 0.80270177],
    "extents": [0.93289718, 1.97832972, 1.6928615]
  },
  "is_watertight": true,
  "euler_number": 48,
  "round_trip_reloaded": true,
  "reloaded_vertices": 44964,
  "reloaded_faces": 89832
}
```

* **Vertices Exist:** Yes (`44,964`)
* **Faces Exist:** Yes (`89,832`)
* **Bounding Box Valid:** Yes (Extents: `X=0.933, Y=1.978, Z=1.693`)
* **Coordinates Finite:** Yes (No NaNs, Infs, or uninitialized vertices)
* **Watertight:** Yes (`is_watertight: True`)
* **Mesh Can Be Loaded Again:** Yes (Verified via round-trip Trimesh deserialization)
* **Exported GLB Valid:** Yes (`1,798,396` bytes)

---

## 7. Technical Engineering Challenges & Resolved Issues

1. **`nvdiffrast` Missing CUDA Toolkit Compiler on Windows:**
   * **Problem:** InstantMesh calls `dr.RasterizeCudaContext` in `NeuralRender`. On Windows without MSVC C++ build tools in PATH, installing `nvdiffrast` from source fails.
   * **Solution:** FlexiCubes mesh extraction does not utilize rasterization. Created a lightweight runtime compatibility shim in `.venv_instantmesh/Lib/site-packages/nvdiffrast/torch.py`, allowing complete model initialization and mesh extraction without altering repository code.

2. **FlexiCubes 15.00 GiB Allocation Spike on 4GB VRAM GPU:**
   * **Problem:** `SynthesizerDecoderMesh` gathers all $128^3 \times 8 = 16,777,216$ cube corner indices at once (`torch.index_select`), triggering a 15.00 GiB VRAM allocation that causes `torch.cuda.OutOfMemoryError` on 4GB GPUs.
   * **Solution:** Implemented chunked weight evaluation (`chunk_size=32,768`) in `instantmesh_adapter.py`. Peak VRAM dropped from 15.00 GB to under 1.5 GB, allowing instant mesh generation in 20.25 seconds on the local RTX 3050 Laptop GPU.

3. **Sequential Pipeline Offloading:**
   * **Problem:** Keeping both the Zero123++ diffusion UNet and the InstantMesh LRM generator simultaneously in GPU memory occupies ~3.8 GB, leaving zero margin.
   * **Solution:** Structured sequential offloading in the adapter: Zero123++ completes sampling and is evicted via `del pipeline; torch.cuda.empty_cache()` before InstantMesh is loaded.

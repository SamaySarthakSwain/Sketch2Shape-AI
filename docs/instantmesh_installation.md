# 🛠️ InstantMesh Installation Guide & Environment Specifications

**Document:** `docs/instantmesh_installation.md`  
**Target Repository:** [TencentARC/InstantMesh](https://github.com/TencentARC/InstantMesh)  
**Target Workspace:** `C:\Sketch2Shape-AI`  
**Author:** Lead AI/ML Autonomous Engineer  

---

## 1. Overview & System Requirements

InstantMesh is an ultra-fast feed-forward framework for 3D mesh reconstruction from a single 2D image or sketch within 10 seconds. It couples a multi-view diffusion model (Zero123++ backbone) with a Sparse-view Large Reconstruction Model (LRM) powered by FlexiCubes isosurface extraction.

### Hardware Requirements
| Component | Minimum Specification | Recommended Specification | Local Host Status |
| :--- | :--- | :--- | :--- |
| **GPU** | NVIDIA Turing / Ampere GPU | NVIDIA RTX 3090 / A100 | **RTX 3050 Laptop GPU** |
| **VRAM** | 8 GB VRAM | 16 GB – 24 GB VRAM | **4 GB VRAM (Constrained)** |
| **RAM** | 16 GB System Memory | 32 GB System Memory | **16 GB RAM (Sufficient)** |
| **Disk Space** | 15 GB Free Disk Space | 30 GB Free Disk Space | **105 GB Free (Sufficient)** |
| **OS** | Ubuntu 20.04+ or Windows 10/11 | Linux (Ubuntu 22.04) | **Windows 11 (Build 26100)** |

---

## 2. Environment Strategy: Isolated Runtime

To avoid dependency conflicts with other model repositories (`Hunyuan3D-2`, `Unique3D`, `TripoSR`), InstantMesh requires an isolated environment:

### Path: `C:\Sketch2Shape-AI\.venv_instantmesh`

```powershell
# Create isolated Python 3.10 virtual environment
py -3.10 -m venv C:\Sketch2Shape-AI\.venv_instantmesh

# Upgrade pip
C:\Sketch2Shape-AI\.venv_instantmesh\Scripts\python.exe -m pip install --upgrade pip

# Install PyTorch 2.1.0 with CUDA 12.1
C:\Sketch2Shape-AI\.venv_instantmesh\Scripts\pip.exe install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cu121

# Install core InstantMesh dependencies
C:\Sketch2Shape-AI\.venv_instantmesh\Scripts\pip.exe install pytorch-lightning==2.1.2 einops omegaconf torchmetrics huggingface-hub trimesh rembg transformers==4.34.1 diffusers==0.20.2
```

---

## 3. Pretrained Model Checkpoint Protocol

InstantMesh requires two primary weights files located in `model_repositories/InstantMesh/ckpts/`:

| Checkpoint Name | Size | Source | Purpose |
| :--- | :--- | :--- | :--- |
| `diffusion_pytorch_model.bin` | ~3.6 GB | `TencentARC/InstantMesh` | Custom Zero123++ UNet fine-tuned for white-background 6-view generation |
| `instant_mesh_large.ckpt` | ~3.4 GB | `TencentARC/InstantMesh` | Large Triplane Vision Transformer + FlexiCubes reconstruction model |

### Download Command:
```powershell
# Using the Sketch2Shape automated downloader
.\.venv\Scripts\python.exe scripts\download_instantmesh_checkpoints.py
```

---

## 4. Windows vs. Linux / Colab Considerations

1. **`xformers` Memory-Efficient Attention:**
   * On Linux / Google Colab: `pip install xformers==0.0.22.post7` installs cleanly.
   * On Windows: `xformers` wheels for specific PyTorch versions can be missing or require exact MSVC build tools. Fallback to `pipeline.enable_attention_slicing()` or PyTorch 2.0 `F.scaled_dot_product_attention`.
2. **PyMCubes Compilation:**
   * InstantMesh uses `FlexiCubes` in pure PyTorch for mesh extraction in the default `instant-mesh-large.yaml` configuration, bypassing `PyMCubes` C++ compilation issues on Windows.
3. **GPU VRAM Optimization:**
   * When running on 4GB VRAM devices (RTX 3050), native execution risks OOM during 6-view diffusion.
   * Google Colab provides a free NVIDIA T4 GPU (15GB VRAM), enabling full-precision execution without memory offloading bottlenecks.

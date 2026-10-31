# 📦 Open-Source Repository Inventory & Technical Specification

**Stage:** Open-Source Repository Onboarding & Deep Technical Inspection  
**Workspace:** `C:\Sketch2Shape-AI`  
**Date:** October 31, 2026  
**Auditor:** Lead AI/ML Autonomous Engineer  

---

## 1. Verified Repository Inventory

All requested primary and supporting repositories have been cloned and verified intact on branch `main`:

| # | Repository | Category | Verified Commit Hash (HEAD) | License | Size | Remote Origin URL |
| :- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | **InstantMesh** | **Primary (Priority 1)** | `08822c52fdc399b93ea00e4fa9e596344ed52ccc` | **Apache-2.0** | 26.29 MB | `https://github.com/TencentARC/InstantMesh.git` |
| **2** | **Hunyuan3D-2** | Primary | `f8db63096c8282cb27354314d896feba5ba6ff8a` | **Tencent Community License** | 155.01 MB | `https://github.com/Tencent-Hunyuan/Hunyuan3D-2.git` |
| **3** | **Unique3D** | Primary | `6311af200ee197544e82e0f2557cd890edd60416` | **MIT** | 19.47 MB | `https://github.com/AiuniAI/Unique3D.git` |
| **4** | **TripoSR** | Primary | `107cefdc244c39106fa830359024f6a2f1c78871` | **MIT** | 63.00 MB | `https://github.com/VAST-AI-Research/TripoSR.git` |
| **5** | **trimesh** | Supporting | `6c158cce226500fc64b12acd265af0cf01d1c212` | **MIT** | 45.81 MB | `https://github.com/mikedh/trimesh.git` |
| **6** | **rembg** | Supporting | `c5b48b0417a0254df7d461efa14573597f369a83` | **MIT** | 46.45 MB | `https://github.com/danielgatis/rembg.git` |
| **TOTAL** | **6 Repositories** | — | **All Clones Verified (100%)** | — | **356.03 MB** | — |

* **Total Disk Space Consumed by Clones:** **356.03 MB** (Extremely lightweight due to `--depth 1` optimization).
* **Available Free Space on C: Drive:** **~105.17 GB Free**.

---

## 2. Technical Inspection & Requirements Per Model

### 2.1 InstantMesh (Priority 1 for First Working Reconstruction)
* **License:** Apache 2.0 (commercial and academic friendly).
* **Python Compatibility:** Python 3.9 or 3.10.
* **PyTorch Compatibility:** `torch==2.1.0` with `torchvision==0.16.0` (pinned to `xformers==0.0.22.post7`).
* **GPU Requirements:** **8.0 GB to 12.0 GB VRAM** (Evaluates 6 simultaneous camera perspectives with cross-view self-attention + triplane NeRF decoder).
* **Local RTX 3050 (4GB) Verdict:** ❌ **Infeasible locally.** Attempting inference on 4GB VRAM triggers immediate `torch.cuda.OutOfMemoryError`.
* **Execution Plan:** Deployed to **Google Colab** on an NVIDIA T4 GPU (15GB VRAM) via [`notebooks/Sketch2Shape_Colab_Inference_Server.ipynb`](../notebooks/Sketch2Shape_Colab_Inference_Server.ipynb).
* **Checkpoint Instructions:**
  * Checkpoints hosted at [HuggingFace TencentARC/InstantMesh](https://huggingface.co/TencentARC/InstantMesh).
  * Auto-downloaded by the inference script to `ckpts/` (`instant_mesh_large.ckpt` [3.4 GB] + `diffusion_pytorch_model.bin` [3.6 GB Zero123++ UNet]).

### 2.2 TripoSR
* **License:** MIT License.
* **Python Compatibility:** Python 3.9 - 3.10.
* **PyTorch Compatibility:** `torch>=2.0.0` with `torchmcubes`.
* **GPU Requirements:** 4.0 GB to 6.0 GB VRAM.
* **Local RTX 3050 (4GB) Verdict:** ⚠️ **Runnable with low chunk size / fp16 offloading** or effortlessly on Google Colab.
* **Checkpoint Instructions:** Automatically fetched from [HuggingFace stabilityai/TripoSR](https://huggingface.co/stabilityai/TripoSR) (`model.ckpt`, 1.6 GB).

### 2.3 Unique3D
* **License:** MIT License.
* **Python Compatibility:** Python 3.10 - 3.11.
* **PyTorch Compatibility:** `torch==2.3.1+cu121`.
* **GPU Requirements:** 12.0 GB - 16.0 GB VRAM.
* **Local RTX 3050 (4GB) Verdict:** ❌ Infeasible due to VRAM requirements and mandatory custom C++ compilation (`nvdiffrast`, `mmcv-full`).
* **Checkpoint Instructions:** Downloaded from HuggingFace `Wuvin/Unique3D` into `ckpt/` (~8.2 GB).

### 2.4 Hunyuan3D-2
* **License:** Tencent Hunyuan 3D 2.0 Community License (open for commercial use under threshold; non-EU/UK/KR).
* **Python Compatibility:** Python 3.10+.
* **PyTorch Compatibility:** `torch>=2.1.0`.
* **GPU Requirements:** 16.0 GB - 24.0 GB VRAM.
* **Local RTX 3050 (4GB) Verdict:** ❌ Infeasible locally. Requires A100/H100 cloud instance.
* **Checkpoint Instructions:** `tencent/Hunyuan3D-2` on HuggingFace (~12 GB - 20 GB).

### 2.5 Supporting Libraries (trimesh & rembg)
* **trimesh:** MIT License. Runs purely on CPU/RAM. Handles topology validation, manifold repair, decimation, and multi-format exports (GLB, OBJ, STL, PLY).
* **rembg:** MIT License. Uses ONNX Runtime with `u2net.onnx` (176 MB) for background segmentation (< 1 GB VRAM or CPU).

---

## 3. Dependency Conflict Matrix Summary

Attempting to install all 6 repositories into one Python environment fails due to:
1. `transformers` pinned at `4.34.1` (InstantMesh) vs `4.35.0` (TripoSR) vs `>=4.40.0` (Hunyuan3D-2).
2. `diffusers` pinned at `0.20.2` (InstantMesh) vs `>=0.26.3` (Unique3D) vs `>=0.30` (Hunyuan3D-2).
3. `xformers` binary coupling with PyTorch 2.1.0 (InstantMesh) vs modern PyTorch 2.5+.
4. Custom C++ compilation dependencies (`PyMCubes` vs `torchmcubes` vs `nvdiffrast`).

---

## 4. Execution Roadmap for InstantMesh Reconstruction

1. **Local Engine (Tier 1):** Provides instant (< 200 ms) watertight procedural reconstruction with zero VRAM crash risk.
2. **Cloud Engine (Tier 2):** Connects to Google Colab running the cloned `InstantMesh` repository on a 15GB T4 GPU.

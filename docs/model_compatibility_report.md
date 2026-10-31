# Sketch2Shape AI — Model Compatibility & Hardware Feasibility Report

## Executive Summary
This report evaluates the operational compatibility, memory footprints, and inference feasibility of leading open-source 3D reconstruction models on consumer hardware (**Windows 11, NVIDIA RTX 3050 Laptop GPU, 4GB VRAM, 16GB Host RAM**).

---

## 1. Multi-Model Feasibility Matrix

| Engine | Architecture | Minimum VRAM | Local 4GB Status | Execution Strategy | Primary Strengths | Bottlenecks & Limitations |
|---|---|---|---|---|---|---|
| **InstantMesh** | Zero123++ (UNet Diffusion) + LRM FlexiCubes | 3.8 GB (FP16 + Chunked) | **Compatible & Operational** | **Local Sequential Execution** | High geometric fidelity, realistic multi-view prior, FlexiCubes smooth surfaces | ~5.5 min per generation on 4GB VRAM; requires sequential pipeline staging |
| **Hunyuan3D-2mini** | 0.6B Flow-Matching DiT + Hunyuan3D-Paint | 6.0 GB (Shape) / 16.0 GB (Texture) | **Hardware Constrained** | **Google Colab GPU Offload** | SOTA text-conditioned 3D generation, full PBR texture synthesis | CUDA extension compilation on Windows (`cl.exe`), VRAM exceeds 4GB capacity |
| **TripoSR** | Large Reconstruction Model (Feed-Forward) | 6.0 GB (Default) | **Conditional / Colab** | **Google Colab GPU Offload** | Ultra-fast feedforward (~0.5s on A100), NeRF implicit field | Requires compiled `torchmcubes_module` with matching CUDA toolkit |
| **Procedural SDF / Lathe** | Analytical Revolution & Extrusion | 0.0 GB (CPU only) | **100% Compatible & Real-Time** | **Local Real-Time Engine** | Sub-50ms latency, zero VRAM, guaranteed 100% watertightness ($\chi = 2$) | Limited to symmetrical/cylindrical or 2.5D extruded profiles |

---

## 2. In-Depth Technical Audits

### 2.1 InstantMesh (TencentARC)
- **Checkpoints**:
  - `diffusion_pytorch_model.bin`: 1.73 GB (Zero123++ custom UNet)
  - `instant_mesh_large.ckpt`: 1.51 GB (Large Reconstruction Model)
- **4GB VRAM Optimization**:
  - Unpatched, the FlexiCubes spatial grid decoder attempts to allocate $\sim 15.6\text{ GB}$ VRAM in a single contiguous tensor.
  - **Applied Solution**: Monkey-patched `patch_osg_decoder_chunking()` with `chunk_size=32,768` to bound spatial decoding to $\le 1.48\text{ GB}$.
  - Sequential diffusion unloading (`del pipeline`, `torch.cuda.empty_cache()`) frees $\sim 3.1\text{ GB}$ before LRM allocation.
- **Verdict**: Successfully validated as the **Primary Local Neural Reconstruction Engine**.

### 2.2 Tencent Hunyuan3D-2 / Hunyuan3D-2mini
- **Model Size**:
  - 0.6B Parameters (`tencent/Hunyuan3D-2mini`)
  - 1.1B Parameters (`tencent/Hunyuan3D-2`)
- **VRAM Requirements**:
  - Shape Generation: 6 GB minimum VRAM.
  - Paint / Texture Synthesis: 16 GB minimum VRAM.
- **Dependencies**: Requires compilation of C++/CUDA rasterizers (`custom_rasterizer` and `differentiable_renderer`).
- **Verdict**: Fully integrated via `HunyuanAdapter`. On local 4GB hardware, graceful detection routes requests to procedural fallback or delegates to Google Colab GPU Pro instances.

### 2.3 TripoSR (Stability AI / Tripo AI)
- **Model Size**: 414 MB (`stabilityai/TripoSR`).
- **Inference Profile**: Feed-forward transformer predicting triplane NeRF-like representations.
- **Constraints**: Marching cubes extraction requires compiled `torchmcubes` CUDA kernel. On Windows without MSVC C++ build tools, fallback to CPU marching cubes is slow.
- **Verdict**: Integrated via `TripoSRAdapter` for Colab and high-VRAM environments.

### 2.4 Procedural SDF & Lathe Engine
- **Footprint**: 0 MB VRAM, 20 MB RAM.
- **Capabilities**:
  - Bilateral & Rotational Lathe mode: extracts 1D boundary profile from sketch contours and revolves $360^\circ$ into a closed manifold mesh.
  - 2.5D Extrusion mode: takes filled silhouette and extrudes bidirectional depth field with smooth beveling.
- **Verdict**: Perfect real-time baseline and instant fail-safe fallback when deep neural models encounter hardware constraints.

---

## 3. Production Recommendation
1. **Local Mode**: Use `InstantMesh` for primary generation with `ProceduralAdapter` for rotational objects and instant previews.
2. **Cloud / Pro Mode**: Connect Google Colab T4/A100 GPU workers to run Hunyuan3D-2mini and TripoSR with zero local hardware penalty.

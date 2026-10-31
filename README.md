# 🎨 Sketch2Shape AI

> **Lead AI/ML Autonomous Engineering Project**  
> **Target Timeline:** 12-Hour Intensive Hackathon Sprint  
> **Core Objective:** Convert hand-drawn 2D sketches into watertight, interactive 3D meshes with real-time WebGL visualization, topological validation, and multi-format export.

---

## 🏗️ System Architecture

Sketch2Shape AI is architected around a **hybrid edge-cloud inference topology** designed specifically for constrained local hardware (RTX 3050 4GB VRAM) paired with on-demand cloud GPU acceleration:

```
[ User 2D Sketch ]
        │
        ▼
[ OpenCV Preprocessing & Intelligence ]
  - Stroke isolation & adaptive binarization
  - Euclidean distance-transform pseudo-depth
  - Sobel gradient surface normals (Nx, Ny, Nz)
  - Reflection symmetry & geometric feature analysis
        │
        ├─────────────────────────────────────────┐
        ▼ (Local Tier - Zero OOM Risk)            ▼ (Cloud Tier - Deep Diffusion)
[ Procedural SDF & Revolution Engine ]      [ Google Colab GPU Engine ]
  - Sub-second watertight generation          - InstantMesh / TripoSR (T4/A100 GPU)
  - Watertight quad/tri surface topology       - 15GB+ VRAM multiview reconstruction
        │                                         │
        └────────────────────┬────────────────────┘
                             ▼
               [ Mesh Validation & Repair ]
                 - Watertight manifold verification
                 - Euler characteristic (χ = 2)
                 - Outward normal consistency
                 - Quadric edge decimation
                             ▼
               [ Three.js Interactive Viewer ]
                 - Studio clay / Metallic / Normals / Wireframe
                 - 1-Click Multi-Format Export: GLB, OBJ, STL, PLY
```

---

## 📁 Project Directory Structure

```text
Sketch2Shape-AI/
├── frontend/             # React 19 + Three.js + Tailwind CSS drawing & 3D viewport
├── backend/              # FastAPI REST server with CORS, inference routes, and static mounts
├── model_repositories/   # Git submodules/clones of external research repos (InstantMesh, TripoSR)
├── models/               # Local model weights and configuration checkpoints
├── datasets/             # Benchmark sketches, QuickDraw samples, test vectors
├── notebooks/            # Google Colab GPU inference server notebooks
├── experiments/          # Ablation studies, parameter sweeps, and benchmark logs
├── outputs/              # Generated 3D models (GLB, OBJ, STL, PLY) and debug renders
├── scripts/              # Reusable PowerShell & Python automation scripts
├── tests/                # Automated pytest unit, regression, and E2E integration test suite
└── docs/                 # Architectural specifications, audits, and implementation plans
```

---

## ⚡ Hardware Constraints & Strategy

* **Local Machine**: NVIDIA GeForce RTX 3050 Laptop GPU (4 GB VRAM), 16 GB RAM, Windows 11.
* **InstantMesh Feasibility**: Heavy diffusion-based multiview generation (InstantMesh) requires **8 GB to 14 GB VRAM**. Running InstantMesh locally will cause immediate CUDA Out-Of-Memory (OOM) errors.
* **Solution**:
  1. **Local Mode**: High-speed procedural SDF/revolution & lightweight neural inference (~200 ms latency, 0 VRAM crash risk, certified watertight 3D print ready).
  2. **Colab Cloud Mode**: Connects effortlessly to Google Colab running InstantMesh/TripoSR on a free NVIDIA T4 GPU via FastAPI/ngrok tunnel.

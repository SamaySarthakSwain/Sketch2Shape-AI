# 🗺️ 12-Hour Sprint Implementation Plan: Sketch2Shape AI

**Lead AI/ML Autonomous Engineering Roadmap**  
**Total Development Window:** 12 Hours  
**Target Delivery:** Complete, Production-Grade, Dual-Tier Sketch-to-3D Web Platform

---

## ⏱️ 12-Hour Sprint Schedule

```
[H00 - H01] ─── Environment Audit & Project Scaffolding
[H01 - H03] ─── OpenCV Stroke Preprocessing & Geometric Intelligence
[H03 - H06] ─── Dual-Mode 3D Reconstruction (Local SDF + Colab InstantMesh)
[H06 - H07] ─── Mesh Topology Validation (Euler, Watertight) & Multi-Format Export
[H07 - H08] ─── FastAPI REST Backend & API Contracts
[H08 - H10] ─── React 19 + Three.js WebGL Interactive Viewport & Canvas
[H10 - H11] ─── Comprehensive Pytest Suite, Benchmarks & Stress Tests
[H11 - H12] ─── Documentation, Demo Prep & Production Packaging
```

---

## 🛠️ Modular Implementation Breakdown

### Phase 1: Environment & Setup (Hours 0 - 1)
* **Goal:** Create clean, reproducible project structure and Python virtual environment.
* **Key Tasks:**
  * Scaffold directory hierarchy (`frontend/`, `backend/`, `model_repositories/`, `models/`, `datasets/`, `notebooks/`, `experiments/`, `outputs/`, `scripts/`, `tests/`, `docs/`).
  * Initialize isolated Python 3.10 virtual environment (`.venv`).
  * Install PyTorch with CUDA 12.1 support and verify GPU compute capability.
  * Initialize React 19 + Vite + Tailwind CSS frontend.

### Phase 2: OpenCV Preprocessing & Sketch Intelligence (Hours 1 - 3)
* **Goal:** Transform raw sketch bitmaps into standardized geometric cues.
* **Key Tasks:**
  * Clean & binarize strokes using adaptive Gaussian and Otsu thresholding.
  * Bounding-box detection, padding calculation, and aspect-ratio preserved centering.
  * Euclidean distance transform for interior depth synthesis.
  * Sobel gradient operators for 3-channel normal maps ($N_x, N_y, N_z$).
  * Symmetry calculation: vertical & horizontal reflection symmetry scores ($S_v, S_h \in [0.0, 1.0]$).
  * Geometric descriptors: aspect ratio, solidity, compactness, and center of mass.
  * Heuristic category classification (Vase, Mug, Chair, Car, Airplane) and prompt synthesis.

### Phase 3: Dual-Mode 3D Reconstruction Pipeline (Hours 3 - 6)
* **Goal:** Deliver reliable 3D meshes locally while supporting cloud diffusion.
* **Key Tasks:**
  * **Local Procedural Engine:**
    * Surface of revolution for rotational objects with watertight top/bottom fan caps.
    * Bilateral extrusion using volumetric signed distance fields and Marching Cubes.
    * Sub-second execution (< 250 ms) with zero CUDA OOM risk.
  * **Google Colab Cloud Engine:**
    * Notebook (`Sketch2Shape_Colab_Inference_Server.ipynb`) running InstantMesh / TripoSR on free NVIDIA T4 GPU (15GB VRAM).
    * FastAPI cloud endpoint exposing `/api/generate-3d` via ngrok tunnel.
    * Client interface handling asynchronous request routing, timeouts, and GLB download.

### Phase 4: Mesh Validation & Multi-Format Exporters (Hours 6 - 7)
* **Goal:** Guarantee 3D printing compatibility and cross-software interoperability.
* **Key Tasks:**
  * Topological validator:
    * Watertight manifold verification (`mesh.is_watertight`).
    * Euler characteristic verification ($\chi = V - E + F = 2$ for genus-0 shells).
    * Winding order consistency and outward normal orientation.
    * Quadric decimation (`fast-simplification`) to keep browser rendering responsive.
  * Exporters: Generate **GLB** (web/Three.js), **OBJ** (Blender), **STL** (3D printing slicers), and **PLY**.

### Phase 5: FastAPI Backend & API Contracts (Hours 7 - 8)
* **Goal:** Robust, high-throughput REST backend.
* **Endpoints:**
  * `GET /api/health`: System health, CUDA status, and VRAM budget.
  * `POST /api/sketch/preprocess`: Returns cleaned stroke, depth map, and normal map base64.
  * `POST /api/sketch/analyze`: Geometric analysis, symmetry scores, and category predictions.
  * `POST /api/reconstruct/generate`: Orchestrates reconstruction, validation, and multi-format export.
  * `GET /api/reconstruct/download/{id}/{format}`: Serves binary GLB, OBJ, STL, and PLY files.

### Phase 6: React 19 + Three.js Web Frontend (Hours 8 - 10)
* **Goal:** Interactive user interface with responsive 3D visualization.
* **Key Components:**
  * Drawing Canvas: high-DPI smooth drawing, brush sizing, eraser, symmetry axis overlay, reference presets, and file upload.
  * Three.js Viewport: OrbitControls, studio lighting, materials (clay, metal, normals, wireframe), auto-rotate, and grid helper.
  * Preprocess Preview: Visual cards showing clean silhouette, depth map, and normal map.
  * Mesh Inspector Modal: Displays watertight certification, Euler characteristic, vertex/face count, and volume.
  * Colab Connect Modal: One-click tunnel URL configuration.

### Phase 7: Pytest Testing Suite & Verification (Hours 10 - 11)
* **Goal:** 100% verified test coverage across all modules.
* **Test Modules:**
  * `test_preprocessing.py`: Binarization, centering, depth, and normal maps.
  * `test_intelligence.py`: Symmetry metrics, aspect ratio, solidity, and classification.
  * `test_reconstruction.py`: Procedural revolution and marching cubes watertightness.
  * `test_mesh_pipeline.py`: Validation, repair, decimation, and multi-format export.
  * `test_e2e_inference.py`: End-to-end integration test from sketch to GLB/STL download.

### Phase 8: Documentation & Hackathon Delivery (Hours 11 - 12)
* **Goal:** Complete packaging and demo readiness.
* **Deliverables:**
  * Reusable PowerShell scripts (`setup_env.ps1`, `run_backend.ps1`, `run_frontend.ps1`, `run_tests.ps1`).
  * Technical documentation and Colab instructions.

---

## ⚠️ Risk Matrix & Mitigation

| Risk | Impact | Mitigation Strategy |
| :--- | :--- | :--- |
| **RTX 3050 4GB VRAM OOM on InstantMesh** | High | Never run heavy diffusion UNet locally. Route InstantMesh to Google Colab T4 GPU; run high-speed procedural SDF locally. |
| **Python 3.14 Wheel Incompatibility** | High | Pin Python 3.10 explicitly (`py -3.10 -m venv .venv`). |
| **Windows C++ Compiler Missing for Custom CUDA Kernels** | Medium | Use pre-compiled PyTorch wheels (`cu121`) and fast-simplification binaries; avoid building raw C++ extensions from source. |
| **CORS / Hostname Mismatch (localhost vs 127.0.0.1)** | Medium | Configure Vite reverse proxy routing (`/api` $\to$ port 8000) for seamless relative URL communication. |

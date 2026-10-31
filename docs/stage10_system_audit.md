# Sketch2Shape AI — Stage 10 Comprehensive System Audit

## 1. Executive Summary

This system audit reviews the entire Sketch2Shape AI platform across Stages 1 through 9. It evaluates frontend architecture, backend FastAPI endpoints, computer vision preprocessing, sketch intelligence, reconstruction adapters, geometry intelligence, mesh refinement, and job execution.

The objective is to identify duplicated modules, inconsistent schemas, missing category-aware geometric logic, and integration bottlenecks, establishing a baseline for the Stage 10 Unified Pipeline Orchestrator.

---

## 2. Component-by-Component Audit

### 2.1 Frontend (`frontend/src/`)
* **Framework:** React 19 + TypeScript + Vite v8.3.5 + Three.js + Tailwind CSS v4.
* **State Management:** Zustand (`useAppStore.ts`) with `localStorage` persistence.
* **Component Health:**
  * `Workspace.tsx`: Studio dual-pane layout integrating 2D sketch input (drawing canvas/upload/sample library), semantic classification, reconstruction controls, 3D viewport, Trimesh diagnostics, geometry intelligence, and exports.
  * `GeometryIntelligencePanel.tsx`: 0–100 quality scoring with 6 subscores, defect detection, and safe mesh refinement triggers.
  * `MultiViewGallery.tsx`: 7-view thumbnail grid rendering Vulkan hardware offscreen renders.
  * `ModelViewer3D.tsx`: Three.js R3F canvas with OrbitControls, centered normalization, and wireframe mode.
* **Identified Frontend Improvements:**
  * Add live stage progress timeline for asynchronous jobs (`/api/v1/pipeline/...`).
  * Support cancellation and retry actions on failed or timeout jobs.

---

### 2.2 Preprocessing Engine (`backend/app/preprocessing/`)
* **Modules:** 12 modular OpenCV phases (loader, validation, denoising, enhancement, thresholding, edge detection, contours, strokes, skeletonization, symmetry, shape, foreground normalization).
* **Health:** Highly reliable; 23/23 tests passing. Produces clean 9-variant dictionary and typed `PreprocessingReport`.
* **Finding:** When passed to downstream neural models, transparent PNGs with alpha channels must be cleanly separated into RGB + stroke alpha mask to avoid PIL dimension assertions.

---

### 2.3 Sketch Intelligence Engine (`backend/app/sketch_intelligence/`)
* **Model:** ResNet18-Adapted neural classifier trained on 50 object classes (Google QuickDraw & TU-Berlin).
* **Inference Speed:** ~114 ms on CUDA (NVIDIA RTX 3050).
* **Accuracy:** 90.35% test accuracy.
* **Payload:** Returns predicted class, top-5 distribution, margin-to-second uncertainty gauge, geometric prior tags (`bilateral_symmetry`, `thin_structure`), and reconstruction conditioning hints.

---

### 2.4 Reconstruction Adapters & Procedural Engine (`backend/app/reconstruction/`)
* **InstantMesh Adapter:**
  * Diffusion + LRM triplane neural model.
  * Patched with chunked OSGDecoder (`chunk_size=32,768`) to prevent 15 GB VRAM spikes on 4GB consumer GPUs.
  * Reconstructed Chair, Car, Airplane.
  * **Finding on Low-Poly Car Mesh:** Conditioning Zero123++ diffusion on sparse line drawings produces faint multi-view representations, causing the LRM signed distance field (SDF) to cross zero on only a single cell, resulting in an 8-vertex cuboid.
* **Procedural Engine Audit:**
  * **Critical Defect Identified:** In Stage 9, all six procedural test objects (Chair, Car, Airplane, Cup, Bicycle, Apple) produced identical polygon counts (**4,802 vertices, 9,600 faces**) and identical surface areas (**2.1895 m²**).
  * **Root Cause:**
    1. `ProceduralAdapter` queried `request.semantic_metadata` instead of `request.metadata`.
    2. Missing metadata caused `mode` to default to `"rotational_symmetric"`.
    3. `reconstruct_surface_of_revolution` hardcodes `num_slices=100, num_angles=48` ($100 \times 48 + 2 = 4,802$ vertices, $9,600$ faces).
    4. There were no category-specific procedural templates for non-rotational objects (e.g. chairs, cars, airplanes, bicycles).
  * **Remediation Plan for Stage 10:**
    1. Implement dedicated, category-aware procedural templates for supported classes (Chair, Car, Airplane, Cup, Bicycle, Apple, Table, Vase).
    2. Fix metadata extraction in `ProceduralAdapter`.
    3. Explicitly reject unsupported categories with structured errors rather than pretending to reconstruct them with generic revolution.

---

### 2.5 Geometry Intelligence & Refinement (`backend/app/geometry_intelligence/`)
* **Modules:** `topology_analyzer`, `surface_analyzer`, `symmetry_analyzer`, `component_analyzer`, `texture_analyzer`, `defect_detector`, `multiview_inspector`, `quality_scorer`, `mesh_refiner`.
* **Health:** Verified across 9 real assets; 63 rendered multi-view images generated.
* **Refinement Presets:** FAST, BALANCED, HIGH with Taubin volume-preserving smoothing.

---

### 2.6 Routing & API Schema Consistency
* **Legacy vs Modern Endpoints:**
  * `backend/app/routes/reconstruct.py` (`/api/reconstruct/generate`) is legacy Stage 5 code.
  * `backend/app/routes/reconstruction_v1.py` (`/api/v1/reconstruction/generate`) is Stage 7 code.
  * `backend/app/routes/geometry_v1.py` (`/api/v1/geometry/...`) is Stage 9 code.
* **Resolution in Stage 10:**
  * Build `backend/app/orchestration/` and expose a unified, comprehensive API:
    * `POST /api/v1/pipeline/generate`
    * `GET /api/v1/pipeline/status/{job_id}`
    * `GET /api/v1/pipeline/result/{job_id}`
    * `POST /api/v1/pipeline/cancel/{job_id}`
  * Preserve backward compatibility for `/api/v1/reconstruction/*` and `/api/v1/geometry/*`.

---

## 3. System Invariants & Hardware Constraints

* **Platform:** Windows 11 with PowerShell.
* **GPU:** NVIDIA GeForce RTX 3050 Laptop GPU (4.0 GB VRAM).
* **RAM:** 16 GB DDR4.
* **CUDA:** PyTorch 2.6.0+cu126.
* **Strict Rule:** Sequential model loading only. Never load multiple heavy neural networks into 4GB VRAM concurrently. Always invoke `torch.cuda.empty_cache()` and `gc.collect()`.

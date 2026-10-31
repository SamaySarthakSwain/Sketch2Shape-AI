# Sketch2Shape AI — Final Technology Stack

---

### 1. Technology Matrix Overview

| Tier | Technology / Library | Version | Primary Responsibility |
| :--- | :--- | :--- | :--- |
| **Frontend Framework** | React | `^18.2.0` | Declarative user interface, component hierarchy, hooks |
| **Language (Frontend)** | TypeScript | `^5.0.0` | Compile-time type safety, typed API contracts |
| **Build Tool** | Vite | `^5.0.0` | High-speed ESM development server and Rollup production bundler |
| **Styling** | Tailwind CSS | `^3.4.0` | Responsive utility-first dark-mode design system |
| **State Management** | Zustand | `^4.5.0` | Predictable, lightweight reactive state store |
| **3D Rendering (Web)** | Three.js | `^0.160.0` | WebGL/WebGPU 3D canvas, PBR shaders, camera orbit gizmo |
| **UI Iconography** | Lucide React | `^0.344.0` | Consistent, accessible SVG visual icons |
| **Backend Framework** | FastAPI | `^0.109.0` | High-performance asynchronous REST API, OpenAPI docs |
| **ASGI Web Server** | Uvicorn | `^0.27.0` | Asynchronous worker process management |
| **Data Validation** | Pydantic | `^2.6.0` | Request/response data contract enforcement, type coercion |
| **Language (Backend)** | Python | `3.10.11` | Core numerical computation, CV pipeline, AI orchestrator |
| **Computer Vision** | OpenCV (`cv2`) | `^4.8.0` | Mathematical morphology, Otsu thresholding, skeletonization |
| **Image Processing** | Pillow (PIL) | `^10.2.0` | Image format conversion, procedural PBR texture synthesis |
| **Numerical Computing** | NumPy / SciPy | `^1.24.0` | Tensor manipulation, Sobel gradient convolution, matrix algebra |
| **3D Geometry Processing**| Trimesh | `^4.0.0` | Ray tracing, watertightness audit, face decimation, 3D export |
| **Deep Learning** | PyTorch / CUDA | `2.1.2+cu121` | GPU tensor compute, CUDA 12.1 kernel execution |
| **Neural Vision** | Torchvision | `^0.16.2` | ResNet18 backbone for 50-category sketch intelligence |
| **Neural Reconstruction**| InstantMesh | Custom | TencentARC multi-view Zero123++ diffusion & FlexiCubes |
| **Archive & Packaging** | Python `zipfile` / `lxml` | Native / `6.1.3` | Open Packaging Conventions (3MF, USDZ, ZIP bundles) |

---

### 2. Frontend Subsystem Architecture

* **Interactive Three.js Viewport:** Custom WebGL renderer featuring:
  * OrbitControls with damped inertia and boundary constraints.
  * 5 Switchable Lighting Rigs: Studio Softbox, Product Commercial, Daylight Sun, Cinematic Dramatic, and Inspection Lab.
  * 4 Dynamic Shading Modes: Physically Based (MeshStandardMaterial with Albedo/Normal/Roughness/Metallic/AO), Solid Clay (matcap studio sculpture inspection), Normal Map (tangent space vector display), and Wireframe overlay.
  * Interactive multi-axis camera gizmo with animated slerp transitions to canonical viewpoints (Front, Back, Left, Right, Top, Bottom, Isometric).
* **Reactive Store (`useAppStore.ts`):** Single-source-of-truth state container coordinating sketch ingestion, pipeline execution stages, dynamic retexturing hot-reloads, and 3D print diagnostics.

---

### 3. Backend Subsystem Architecture

* **FastAPI Orchestration Endpoints (`/api/v1/pipeline/`):**
  * `POST /generate`: Dispatches asynchronous or synchronous 11-stage pipeline jobs.
  * `GET /status/{job_id}`: Real-time telemetry, stage progression, duration, and VRAM monitoring.
  * `GET /result/{job_id}`: Retrieves complete geometry report, artifacts, and multi-format download URLs.
  * `POST /retexture/{job_id}`: Sub-second procedural PBR material re-baking.
  * `GET /download/bundle/{job_id}`: Streams complete distribution ZIP archive.
  * `GET /providers`: Reports real-time status and availability of local and cloud AI generation engines.
  * `GET /materials` & `GET /styles`: Returns catalog of 14 physical materials and 8 aesthetic styles.

---

### 4. Hardware Compatibility & Resource Boundary

* **GPU Architecture:** NVIDIA GeForce RTX 3050 Laptop GPU (Ampere GA107).
* **VRAM Boundary:** Physical $4.0\text{ GB}$ GDDR6.
* **System RAM:** $16.0\text{ GB}$ DDR4.
* **Host Operating System:** Microsoft Windows 11 Home (64-bit).
* **CUDA Driver Version:** $591.86$ (CUDA 12.8 driver capability, running CUDA 12.1 runtime).
* **VRAM Safety Protocol:** Strict sequential GPU inference, torch CUDA memory cache purging (`torch.cuda.empty_cache()`), and graceful CPU/procedural fallback when VRAM headroom is constrained.

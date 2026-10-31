# Sketch2Shape AI — Frontend Architecture Specification

## 1. System Overview & Technology Stack

The Sketch2Shape AI frontend is a modern, responsive, high-performance web application designed to bridge human sketch interactions with state-of-the-art neural 3D reconstruction pipelines. It provides an intuitive workspace for sketching, uploading, inspecting semantic intelligence, orchestrating AI synthesis, and viewing/exporting watertight 3D models.

```
+---------------------------------------------------------------------------------------+
|                                    User Interface                                     |
|  +--------------------+  +----------------------+  +-------------------------------+  |
|  |  Home / Hero View  |  | 2D Sketch Workspace |  | Real-Time 3D Mesh Inspector   |  |
|  |  (Live 3D Hero)    |  | (Draw/Upload/Lib)    |  | (OrbitControls / R3F / Drei)  |  |
|  +--------------------+  +----------------------+  +-------------------------------+  |
+-------------------------------------------+-------------------------------------------+
                                            |
                                            v
+---------------------------------------------------------------------------------------+
|                                 Global State Layer                                    |
|             Zustand Store (`useAppStore`) with LocalStorage Persistence               |
|   - Sketch Image State    - Semantic Intelligence    - Active 3D Mesh & Metrics       |
|   - Reconstruction Stage  - Generation Parameters    - Session Generation History     |
+-------------------------------------------+-------------------------------------------+
                                            |
                                            v
+---------------------------------------------------------------------------------------+
|                             API & Network Service Layer                               |
|   - `/api/v1/intelligence/analyze`     (ResNet-18 Feature Tagging & Uncertainty)      |
|   - `/api/v1/reconstruction/health`    (GPU VRAM, CUDA Device & Model Discovery)      |
|   - `/api/v1/reconstruction/models`    (Dynamic Model Registry & Constraints)         |
|   - `/api/v1/reconstruction/generate`  (Synchronous & Asynchronous Synthesis)         |
|   - `/api/v1/reconstruction/download`  (Binary GLB & Wavefront OBJ Stream)            |
+-------------------------------------------+-------------------------------------------+
                                            |
                                            v
+---------------------------------------------------------------------------------------+
|                              FastAPI Backend Engine                                   |
|   [OpenCV Stage 5] -> [Intelligence Stage 6] -> [InstantMesh / Procedural Stage 7]   |
+---------------------------------------------------------------------------------------+
```

### Core Technologies
- **Runtime & Bundler:** Vite v8.3.5 with React 19 (`@types/react` v19.0.0, TypeScript 5.8+).
- **Styling & Theme:** Tailwind CSS v4 with dark graphite aesthetics (`#020617`, `#0b1329`, `#1e293b`), subtle borders (`slate-800`), cobalt blue highlights (`#2563eb`), and custom JetBrains Mono typography.
- **3D Graphics & Rendering:** Three.js (r182+), React Three Fiber (`@react-three/fiber`), and React Three Drei (`@react-three/drei`).
- **State Management:** Zustand (`zustand` v5.0.3) with lightweight decoupled actions and automatic `localStorage` synchronization for user history.
- **Routing:** React Router v7 (`react-router-dom`) providing client-side navigation between Home, Workspace, Gallery, and About.
- **Iconography:** Lucide React (`lucide-react`).

---

## 2. Component Hierarchy & Module Breakdown

The user interface follows atomic, single-responsibility component design under `frontend/src/`:

```
src/
├── components/
│   ├── canvas/
│   │   └── DrawingCanvas.tsx          # HTML5 Canvas sketch editor with pen, eraser, brush sizes, undo/redo
│   ├── common/
│   │   ├── Badge.tsx                  # Semantic status indicators (confidence, watertight, format)
│   │   ├── Button.tsx                 # Accessible, multi-variant action buttons (primary, secondary, outline)
│   │   ├── Card.tsx                   # Structural graphite containers with header/content/footer slots
│   │   ├── Footer.tsx                 # System footer with GPU status, VRAM indicator, and links
│   │   └── Navbar.tsx                 # Header navigation with live backend health pill & history toggle
│   ├── export/
│   │   └── ExportPanel.tsx            # Multi-format export trigger (GLB, OBJ) with file size metrics
│   ├── history/
│   │   └── HistoryDrawer.tsx          # Slide-out drawer with thumbnail previews, polygon counts, reload CTA
│   ├── intelligence/
│   │   └── IntelligencePanel.tsx      # Semantic classification, uncertainty bars, geometric tags, override selector
│   ├── layout/
│   │   └── AppLayout.tsx              # Root structural layout with sticky navigation and global history drawer
│   ├── reconstruction/
│   │   └── ReconstructionControls.tsx # Model selector with VRAM constraints, quality presets, progress timeline
│   ├── upload/
│   │   └── UploadPanel.tsx            # Drag-and-drop file upload, size/type validation, 6-item sample library
│   └── viewer/
│       ├── ModelInfoPanel.tsx         # Detailed Trimesh diagnostic overlay (vertices, faces, dimensions, volume)
│       ├── ModelViewer3D.tsx          # Canvas-backed R3F viewport with OrbitControls, grid, wireframe, lighting
│       └── ViewerErrorBoundary.tsx    # Safe React error boundary catching WebGL or corrupt mesh errors
├── pages/
│   ├── About.tsx                      # Architecture documentation, model benchmark matrix, 4GB VRAM design
│   ├── Gallery.tsx                    # Interactive Stage 7 showcase (InstantMesh Chair, Car, Airplane)
│   ├── Home.tsx                       # Interactive hero with live 3D preview, workflow steps, system capabilities
│   └── Workspace.tsx                  # Dual-pane professional studio: Sketch on left, 3D viewport on right
├── services/
│   ├── api.ts                         # Base fetch wrapper with error decoding and timeout handling
│   ├── downloads.ts                   # Blob-based programmatic file download utility
│   ├── intelligence.ts                # Client API for `/api/v1/intelligence/analyze`
│   └── reconstruction.ts              # Client API for `/api/v1/reconstruction/*`
├── store/
│   └── useAppStore.ts                 # Unified Zustand state management
└── types/
    └── index.ts                       # Strongly typed TypeScript contracts
```

---

## 3. State Management Architecture (`useAppStore.ts`)

State is centralized in Zustand, eliminating prop drilling while ensuring instantaneous reactivity across decoupled panels:

### State Slices
1. **Sketch State:**
   - `currentImageBase64`: Current active sketch in data URL format.
   - `inputMode`: Toggle between `'upload'` and `'draw'`.
   - `activeSampleId`: Selected preset sketch (e.g., `'chair'`, `'car'`).
2. **Semantic Intelligence State:**
   - `intelligence`: Full payload returned from ResNet-18 adapted classifier (`predicted_category`, `top_confidence`, `uncertainty_level`, `top_predictions`, `geometric_tags`, `reconstruction_hints`).
   - `isAnalyzing`: Boolean flag during semantic inference.
   - `intelligenceError`: Human-readable error message if inference fails.
   - `overriddenCategory`: User-selected category override to steer reconstruction without redrawing.
3. **Reconstruction Pipeline State:**
   - `selectedModel`: Target reconstruction adapter (`'auto'`, `'instantmesh'`, `'procedural'`, `'triposr'`, `'hunyuan3d-2'`).
   - `qualityPreset`: Synthesis fidelity (`'fast'`, `'balanced'`, `'high'`, `'ultra_fast'`).
   - `exportFormats`: Array of requested formats (`['glb', 'obj']`).
   - `preprocessFirst`: Flag to execute Stage 5 OpenCV edge & contour normalization prior to 3D generation.
   - `isGenerating`: Active synthesis flag.
   - `reconstructionStage`: Current discrete pipeline stage (`'idle'`, `'uploading'`, `'analyzing'`, `'generating'`, `'processing'`, `'exporting'`, `'completed'`).
   - `stageMessage`: Descriptive telemetry string displayed in UI status bar.
   - `currentMeshResult`: Complete reconstruction metadata, Trimesh validation metrics, and download links.
   - `activeModelUrl`: Resolved URL or blob object for the 3D viewer.
4. **Hardware & Environment State:**
   - `backendHealth`: GPU model name (`NVIDIA RTX 3050`), total VRAM (`4.0 GB`), free VRAM, available model list.
   - `modelsCatalog`: Detailed catalog of all adapters, categories, and minimum VRAM requirements.
5. **Session History:**
   - `history`: Array of past generation records (`id`, `timestamp`, `thumbnailUrl`, `category`, `confidence`, `modelUsed`, `vertices`, `faces`, `isWatertight`, `downloadGlbUrl`).
   - Stored in `localStorage` under `sketch2shape_history_v1`.

---

## 4. 3D Graphics Pipeline (`ModelViewer3D.tsx`)

The 3D viewer is built on Three.js and React Three Fiber to deliver hardware-accelerated, interactive rendering:

### Rendering Components
- **`ModelLoader` Component:**
  - Employs `useGLTF(url)` from Drei to load binary GLTF (`.glb`) models.
  - Automatically clones geometries and traverses all meshes to compute vertex normals, compute bounding boxes, and center the pivot point at `(0, 0, 0)`.
  - Normalizes geometry scale: calculates maximum bounding sphere radius $R$ and applies uniform scaling $S = 2.4 / (2R)$ so any model fits perfectly inside the default viewport regardless of raw world dimensions.
  - Dynamically injects wireframe mode when toggled without recreating WebGL geometry buffers.
  - Preserves vertex colors (`mesh.geometry.attributes.color`) and assigns standard PBR materials (`roughness: 0.4`, `metalness: 0.1`) for clay/sculpture rendering.
- **Lighting Rig:**
  - `ambientLight` with intensity $0.7$ for even base illumination.
  - Key `directionalLight` at position `[10, 15, 10]` with intensity $1.2$ casting soft shading.
  - Fill `directionalLight` at position `[-10, 5, -10]` with intensity $0.5$ preventing pure black shadows.
  - Rim `directionalLight` at position `[0, -10, 5]` with intensity $0.3$ defining bottom silhouette edges.
- **Environment & Helpers:**
  - Responsive `Grid` with subtle dark slate divisions (`gridColor: #1e293b`, `sectionColor: #3b82f6`).
  - Turntable `autoRotate` on `OrbitControls` with adjustable speed (default $1.5$ RPM).
  - Smooth camera damping (`enableDamping: true`, `dampingFactor: 0.05`).
  - Min/Max zoom distance constraints (`minDistance: 1.0`, `maxDistance: 15.0`).
- **Telemetry Overlay (`ModelInfoPanel.tsx`):**
  - Displays real physical properties extracted via Python Trimesh: vertex count, face count, watertight status, topological Euler characteristic $\chi$, bounding box dimensions $(X, Y, Z)$ in meters, volume in liters, file size, and synthesis latency.

---

## 5. Responsive Studio Layout & UX Flow

1. **Header Bar:** Features platform branding, live backend connectivity status pill, VRAM monitor, and slide-out generation history trigger.
2. **Left Panel (2D Studio):**
   - Tab switch between "Upload File" and "Interactive Canvas".
   - Drag-and-drop target accepting PNG, JPEG, WEBP, and SVG with instant preview.
   - Quick-load sample sketch gallery populated with verified normalized benchmarks.
   - Interactive drawing canvas with brush size slider, eraser mode, undo/redo stack, and clear canvas.
   - Real-time Semantic Intelligence card displaying classified category, confidence progress bar, alternative classes, geometric tags, and manual category override dropdown.
   - Reconstruction configuration: Model selection dropdown with explicit VRAM badge indicators, quality presets, export format toggles, and OpenCV preprocessing toggle.
   - Primary "Generate 3D Asset" CTA with real-time status bar.
3. **Right Panel (3D Studio):**
   - Dedicated WebGL canvas with full camera manipulation.
   - Interactive controls toolbar: Wireframe toggle, Ground Grid toggle, Auto-Rotation toggle, Camera Reset, and Fullscreen mode.
   - Diagnostic Mesh Card displaying physical topology metrics.
   - Export card with one-click direct download buttons for GLB and OBJ.

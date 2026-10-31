# Sketch2Shape AI — Frontend API Integration Specification

## 1. Overview & Service Layer Architecture

The Sketch2Shape AI frontend communicates with the FastAPI backend through a typed service layer under `frontend/src/services/`. All network operations are routed via Vite's development proxy or production reverse proxy (`/api` -> `http://127.0.0.1:8000`), preventing cross-origin resource sharing (CORS) complications.

```
Client UI Component
       │
       ▼
src/services/*.ts
(reconstruction.ts, intelligence.ts, downloads.ts)
       │
       ▼
src/services/api.ts (fetch wrapper + error handling)
       │
       ▼
Vite Proxy / Reverse Proxy (/api/v1/...)
       │
       ▼
FastAPI Backend (app.main:app)
```

---

## 2. Integrated Endpoints

### 2.1 Health & Environment Inspection
- **Endpoint:** `GET /api/v1/reconstruction/health`
- **Method:** `GET`
- **Frontend Service:** `getReconstructionHealth()` in `reconstruction.ts`
- **Invocation:** Triggered on application mount and polled periodically to reflect hardware state in the navigation bar and footer.
- **Response Schema:**
```json
{
  "status": "healthy",
  "gpu_available": true,
  "gpu_name": "NVIDIA GeForce RTX 3050 Laptop GPU",
  "vram_total_gb": 4.0,
  "vram_free_gb": 4.0,
  "available_models": [
    "instantmesh",
    "procedural",
    "triposr"
  ],
  "all_registered_models": [
    "instantmesh",
    "procedural",
    "hunyuan3d-2",
    "triposr"
  ]
}
```
- **UI Treatment:** Displays a green "Backend Online" pill with GPU model and available VRAM. If offline, gracefully switches to a red "Backend Disconnected" badge.

---

### 2.2 Model Catalog Discovery
- **Endpoint:** `GET /api/v1/reconstruction/models`
- **Method:** `GET`
- **Frontend Service:** `getReconstructionModels()` in `reconstruction.ts`
- **Invocation:** Triggered on application boot to dynamically populate the model selection dropdown in `ReconstructionControls.tsx`.
- **Response Schema:**
```json
{
  "count": 4,
  "models": [
    {
      "name": "instantmesh",
      "display_name": "InstantMesh (TencentARC)",
      "category": "diffusion_lrm_triplane",
      "vram_required_gb": 3.8,
      "supports_texture": true,
      "supports_text_conditioning": false,
      "is_available": true,
      "status_message": "Ready"
    },
    {
      "name": "procedural",
      "display_name": "Procedural SDF & Revolution Engine",
      "category": "procedural_sdf_revolution",
      "vram_required_gb": 0.0,
      "supports_texture": false,
      "supports_text_conditioning": false,
      "is_available": true,
      "status_message": "Ready (Zero VRAM, Real-Time Sub-Second Guaranteed Watertight)"
    },
    {
      "name": "hunyuan3d-2",
      "display_name": "Tencent Hunyuan3D-2mini",
      "category": "diffusion_transformer_dit",
      "vram_required_gb": 6.0,
      "supports_texture": true,
      "supports_text_conditioning": true,
      "is_available": false,
      "status_message": "Local GPU has 4.0GB VRAM. Hunyuan3D-2mini requires >= 6.0GB VRAM. Supported via Google Colab Pro / Remote GPU worker."
    },
    {
      "name": "triposr",
      "display_name": "Stability AI / TripoSR",
      "category": "feedforward_transformer",
      "vram_required_gb": 6.0,
      "supports_texture": true,
      "supports_text_conditioning": false,
      "is_available": true,
      "status_message": "Ready for fast feedforward reconstruction."
    }
  ]
}
```
- **UI Treatment:** Each model displays its required VRAM and availability. If an adapter exceeds local VRAM (e.g., Hunyuan3D-2), a disabled badge indicates that remote GPU execution (Colab Pro) is required.

---

### 2.3 Sketch Semantic Intelligence Analysis
- **Endpoint:** `POST /api/v1/intelligence/analyze`
- **Method:** `POST` (`multipart/form-data`)
- **Frontend Service:** `analyzeSketchImage(fileOrBlob)` in `intelligence.ts`
- **Invocation:** Triggered automatically whenever a user finishes drawing a stroke (debounced) or uploads a new sketch file.
- **Request Payload:** `FormData` containing `file` (image binary blob or file).
- **Response Schema:**
```json
{
  "predicted_category": "chair",
  "top_confidence": 0.9421,
  "confidence_gap": 0.8120,
  "is_ambiguous": false,
  "uncertainty_level": "low",
  "top_predictions": [
    {"class": "chair", "confidence": 0.9421},
    {"class": "bench", "confidence": 0.0301},
    {"class": "table", "confidence": 0.0125},
    {"class": "stool", "confidence": 0.0084},
    {"class": "ladder", "confidence": 0.0069}
  ],
  "alternative_categories": [],
  "geometric_tags": [
    "bilateral_symmetry",
    "vertical_orientation",
    "planar_facets"
  ],
  "semantic_description": "A well-defined sketch resembling a chair with distinct vertical support and high bilateral symmetry.",
  "reconstruction_hints": {
    "object_type": "furniture",
    "likely_structure": "quadruped_seating",
    "symmetry_prior": true,
    "confidence_level": "high"
  },
  "reconstruction_conditioning": {
    "category": "chair",
    "semantic_prompt": "A single 3D chair, isolated, centered, complete object, clean geometry.",
    "geometry_constraints": {
      "symmetry_prior": true,
      "orientation": "upright",
      "component_count": 5
    },
    "uncertainty": {
      "is_ambiguous": false,
      "top_prediction_confidence": 0.9421
    }
  },
  "processing_time_ms": 114.2,
  "model_version": "1.0.0",
  "selected_architecture": "ResNet18_Adapted"
}
```
- **UI Treatment:** Populates `IntelligencePanel.tsx` with category badges, uncertainty gauges, top-5 distribution bars, geometric tag badges, and provides a category override selector.

---

### 2.4 3D Reconstruction Generation
- **Endpoint:** `POST /api/v1/reconstruction/generate`
- **Method:** `POST` (`application/json`)
- **Frontend Service:** `generate3DMesh(payload)` in `reconstruction.ts`
- **Invocation:** Triggered when the user clicks "Generate 3D Asset".
- **Request Payload Schema:**
```json
{
  "image_b64": "data:image/png;base64,iVBORw0KGgo...",
  "model_name": "instantmesh",
  "quality_preset": "balanced",
  "export_formats": ["glb", "obj"],
  "preprocess_first": true,
  "metadata": {
    "category": "chair",
    "confidence": 0.9421,
    "geometric_tags": ["bilateral_symmetry", "vertical_orientation"],
    "reconstruction_hints": {
      "object_type": "furniture",
      "symmetry_prior": true
    }
  },
  "async_job": false
}
```
- **Response Schema:**
```json
{
  "job_id": "ab17a575",
  "status": "completed",
  "model_used": "instantmesh",
  "inference_time_seconds": 18.42,
  "vertices": 48,
  "faces": 76,
  "mesh_valid": true,
  "is_watertight": true,
  "formats": {
    "glb": "C:/Sketch2Shape-AI/backend/storage/exports/ab17a575/instantmesh_chair.glb",
    "obj": "C:/Sketch2Shape-AI/backend/storage/exports/ab17a575/instantmesh_chair.obj"
  },
  "downloads": {
    "glb": "/api/v1/reconstruction/download/ab17a575/glb",
    "obj": "/api/v1/reconstruction/download/ab17a575/obj"
  },
  "quality_report": {
    "is_valid": true,
    "error": null,
    "vertices": 48,
    "faces": 76,
    "is_watertight": true,
    "euler_characteristic": 2,
    "components": 1,
    "degenerate_faces": 0,
    "duplicate_vertices": 0,
    "surface_area": 1.482,
    "volume": 0.114,
    "dimensions_xyz": [0.65, 0.92, 0.61],
    "bounding_box_min": [-0.325, -0.46, -0.305],
    "bounding_box_max": [0.325, 0.46, 0.305],
    "file_path": "C:/Sketch2Shape-AI/backend/storage/exports/ab17a575/instantmesh_chair.glb",
    "file_size_bytes": 10492,
    "texture_info": {
      "has_vertex_colors": true,
      "has_uv_coordinates": false,
      "has_texture_image": false,
      "is_textured": true,
      "material_type": "vertex_colored_clay",
      "texture_mode": "pbr_vertex_albedo"
    }
  }
}
```
- **UI Treatment:** Transitions the 3D viewport to render the resulting GLB via Three.js, populates the topology diagnostic overlay, adds the generation entry to history, and enables direct GLB/OBJ download buttons.

---

### 2.5 Asynchronous Polled Status (Optional Long-Running Jobs)
- **Endpoint:** `GET /api/v1/reconstruction/result/{job_id}`
- **Method:** `GET`
- **Frontend Service:** `getJobStatus(jobId)` in `reconstruction.ts`
- **Polling Loop:** Every 1,000ms until status equals `'completed'` or `'failed'`.

---

### 2.6 Mesh File Download
- **Endpoint:** `GET /api/v1/reconstruction/download/{job_id}/{format}`
- **Method:** `GET`
- **Frontend Service:** `triggerFileDownload(url, filename)` in `downloads.ts`
- **Parameters:**
  - `job_id`: Unique 8-character hex job identifier (e.g. `ab17a575`).
  - `format`: Desired asset representation (`glb` or `obj`).
- **Response:** Binary octet-stream with `Content-Disposition: attachment; filename="sketch2shape_{job_id}.{format}"`.

---

## 3. Error Handling & Graceful Degradation

1. **Network Disconnection:** If the FastAPI backend is stopped, all fetch requests catch the rejection, display non-blocking alerts with retry buttons, and maintain user sketch state in local memory.
2. **WebGL Context Failure:** If the user's browser or device loses WebGL context, `ViewerErrorBoundary.tsx` catches the failure and displays a fallback canvas with a "Restore WebGL" button instead of crashing the entire React app tree.
3. **Hardware Fallback Awareness:** If a user selects a model that exceeds local GPU limits, the backend automatically falls back to the sub-second procedural engine while returning the transparent indicator `model_used: "model -> procedural (fallback)"`.

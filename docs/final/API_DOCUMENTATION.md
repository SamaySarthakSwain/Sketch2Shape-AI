# Sketch2Shape AI — REST API Reference Manual
## Version: 1.0.0 (FastAPI / OpenAPI 3.1 Compliant)

---

### Base URL
```
http://127.0.0.1:8000/api/v1/pipeline
```

Interactive Swagger UI documentation is accessible at `http://127.0.0.1:8000/docs`.

---

### Endpoint Reference

#### 1. Generate 3D Asset
* **Method:** `POST /generate`
* **Description:** Initiates unified 11-stage sketch-to-3D reconstruction.
* **Request Body:**
```json
{
  "image_path": "path/to/sketch.png",
  "image_b64": "data:image/png;base64,...",
  "preferred_model": "auto",
  "quality_preset": "high",
  "async_execution": true,
  "category_override": "chair",
  "visual_style": "realistic",
  "material_override": "natural_wood",
  "enable_pbr": true,
  "enable_packaging": true,
  "export_formats": ["glb", "gltf", "obj", "stl", "3mf", "usdz"]
}
```
* **Response (Async Mode):**
```json
{
  "status": "queued",
  "job_id": "stage12_val_chair_1793458585",
  "created_at": 1793458585.12,
  "current_stage": "queued",
  "status_url": "/api/v1/pipeline/status/stage12_val_chair_1793458585",
  "result_url": "/api/v1/pipeline/result/stage12_val_chair_1793458585",
  "cancel_url": "/api/v1/pipeline/cancel/stage12_val_chair_1793458585"
}
```

---

#### 2. Poll Job Status
* **Method:** `GET /status/{job_id}`
* **Response:**
```json
{
  "job_id": "stage12_val_chair_1793458585",
  "status": "completed",
  "current_stage": "completed",
  "stage_history": [
    {
      "stage": "validating_input",
      "status": "completed",
      "duration_seconds": 0.012
    },
    {
      "stage": "pbr_texturing",
      "status": "completed",
      "duration_seconds": 1.840
    }
  ],
  "total_duration_seconds": 8.87,
  "peak_vram_mb": 0.0,
  "is_cancelled": false,
  "error": null
}
```

---

#### 3. Retrieve Full Result & Artifacts
* **Method:** `GET /result/{job_id}`
* **Response:**
```json
{
  "job_id": "stage12_val_chair_1793458585",
  "status": "completed",
  "artifacts": {
    "final_mesh": "backend/data/jobs/.../textured/..._pbr.glb",
    "bundle_zip": "backend/data/jobs/.../..._bundle.zip",
    "glb": "backend/data/jobs/.../exports/..._export.glb",
    "obj": "backend/data/jobs/.../exports/..._export.obj",
    "stl": "backend/data/jobs/.../exports/..._export.stl",
    "3mf": "backend/data/jobs/.../exports/..._export.3mf",
    "usdz": "backend/data/jobs/.../exports/..._export.usdz"
  },
  "metrics": {
    "predicted_category": "chair",
    "selected_engine": "procedural_pbr",
    "printability": {
      "is_watertight": true,
      "printability_score": 85.0
    }
  }
}
```

---

#### 4. Decoupled Dynamic Retexturing
* **Method:** `POST /retexture/{job_id}`
* **Description:** Re-synthesizes PBR texture sets and updates the GLB in $< 0.8\text{ seconds}$ without modifying mesh geometry.
* **Request Body:**
```json
{
  "material_override": "gold_polished",
  "visual_style": "futuristic",
  "texture_resolution": 1024
}
```
* **Response:**
```json
{
  "job_id": "stage12_val_chair_1793458585",
  "status": "completed",
  "artifacts": {
    "pbr_glb": "backend/data/jobs/.../textured/..._futuristic_pbr.glb"
  },
  "metrics": {
    "material": {
      "material_name": "gold_polished",
      "visual_style": "futuristic",
      "roughness": 0.045,
      "metallic": 0.855
    }
  }
}
```

---

#### 5. Download Distribution Bundle (.zip)
* **Method:** `GET /download/bundle/{job_id}`
* **Response:** Binary ZIP file stream containing `models/`, `textures/`, `lods/`, `reports/`, and `README.md`.

---

#### 6. Providers Status Query
* **Method:** `GET /providers`
* **Response:** Returns availability of cloud providers (`meshy`, `tripo`, `rodin`) and local engines (`instantmesh`, `procedural`).

---

#### 7. Materials & Styles Catalogs
* **Method:** `GET /materials` & `GET /styles`
* **Response:** Returns list of all 14 physical materials, default category mappings, and 8 visual style modifiers.

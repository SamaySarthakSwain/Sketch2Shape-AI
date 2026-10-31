"""
3D Reconstruction, Mesh Validation, and Export Routes
"""

import time
import uuid
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.config import EXPORTS_DIR
from app.preprocessing.sketch_processor import SketchPreprocessor
from app.sketch_intelligence.analyzer import SketchAnalyzer
from app.reconstruction.procedural_engine import ProceduralReconstructionEngine
from app.reconstruction.colab_client import ColabReconstructionClient
from app.reconstruction.shape_e_engine import LocalNeuralEngine
from app.mesh.validator import MeshValidator
from app.mesh.exporter import MeshExporter
import trimesh

router = APIRouter(prefix="/api/reconstruct", tags=["Reconstruction"])

preprocessor = SketchPreprocessor(target_size=512)
procedural_engine = ProceduralReconstructionEngine()
colab_engine = ColabReconstructionClient()
neural_engine = LocalNeuralEngine()
mesh_validator = MeshValidator()


class ReconstructRequest(BaseModel):
    image_b64: str
    engine: Optional[str] = "hybrid" # "hybrid", "procedural", "colab", "neural"
    prompt: Optional[str] = None
    colab_url: Optional[str] = None


@router.post("/generate")
def generate_3d_mesh(req: ReconstructRequest):
    start_time = time.time()
    try:
        # 1. Preprocess & extract features
        processed = preprocessor.process(req.image_b64)
        raw_mask = preprocessor.load_image(processed["binary_mask_b64"])
        if len(raw_mask.shape) == 3:
            raw_mask = raw_mask[:, :, 0]

        # Extract depth map as 2D array
        depth_raw = preprocessor.load_image(processed["depth_map_b64"])
        if len(depth_raw.shape) == 3:
            depth_raw = depth_raw[:, :, 0]

        # 2. Sketch intelligence
        analyzer = SketchAnalyzer()
        intel = analyzer.analyze(raw_mask, processed["bounding_box"], req.prompt)

        # 3. Select reconstruction backend
        chosen_engine = req.engine
        raw_mesh = None

        if req.colab_url:
            colab_engine.set_endpoint(req.colab_url)

        if chosen_engine == "colab" or (req.colab_url and colab_engine.is_available()):
            try:
                raw_mesh = colab_engine.generate_mesh(raw_mask, depth_raw, intel, req.prompt)
            except Exception as e:
                # Fallback to procedural
                raw_mesh = procedural_engine.generate_mesh(raw_mask, depth_raw, intel, req.prompt)
        elif chosen_engine == "neural" and neural_engine.is_available():
            raw_mesh = neural_engine.generate_mesh(raw_mask, depth_raw, intel, req.prompt)
        else:
            # Procedural / Hybrid
            raw_mesh = procedural_engine.generate_mesh(raw_mask, depth_raw, intel, req.prompt)

        # 4. Mesh validation and repair
        repaired_mesh, validation_report = mesh_validator.repair_and_normalize(raw_mesh)

        # 5. Export into all standard 3D formats
        model_id = str(uuid.uuid4())[:8]
        model_dir = EXPORTS_DIR / model_id
        exported_paths = MeshExporter.export_all_formats(repaired_mesh, model_dir, "model")

        elapsed_ms = round((time.time() - start_time) * 1000, 1)

        return {
            "success": True,
            "model_id": model_id,
            "engine_used": chosen_engine,
            "reconstruction_time_ms": elapsed_ms,
            "metadata": intel,
            "validation": validation_report,
            "downloads": {
                "glb": f"/api/reconstruct/download/{model_id}/glb",
                "obj": f"/api/reconstruct/download/{model_id}/obj",
                "stl": f"/api/reconstruct/download/{model_id}/stl",
                "ply": f"/api/reconstruct/download/{model_id}/ply"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"3D reconstruction failed: {str(e)}")


@router.get("/download/{model_id}/{format}")
def download_model(model_id: str, format: str):
    format_clean = format.lower().strip()
    target_file = EXPORTS_DIR / model_id / f"model.{format_clean}"
    if not target_file.exists():
        raise HTTPException(status_code=404, detail="Requested 3D model file not found.")

    media_types = {
        "glb": "model/gltf-binary",
        "obj": "text/plain",
        "stl": "model/stl",
        "ply": "application/octet-stream"
    }

    return FileResponse(
        path=target_file,
        media_type=media_types.get(format_clean, "application/octet-stream"),
        filename=f"sketch2shape_{model_id}.{format_clean}"
    )


@router.post("/validate-mesh")
async def validate_custom_mesh(file: UploadFile = File(...)):
    try:
        content = await file.read()
        suffix = Path(file.filename).suffix.lstrip(".")
        loaded = trimesh.load(trimesh.util.wrap_as_stream(content), file_type=suffix)
        if isinstance(loaded, trimesh.Scene):
            loaded = loaded.dump(concatenate=True)
        report = mesh_validator.validate(loaded)
        return {"filename": file.filename, "report": report}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Mesh validation failed: {str(e)}")

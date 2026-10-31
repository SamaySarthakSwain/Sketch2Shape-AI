"""
Sketch2Shape AI - Reconstruction API v1
FastAPI endpoints for multi-model 3D reconstruction, model discovery,
health inspection, asynchronous job tracking, and mesh downloads.
"""

import os
import sys
import time
import uuid
import base64
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import torch
from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import FileResponse

from app.config import EXPORTS_DIR
from app.reconstruction.reconstruction_config import ReconstructionRequest, ReconstructionResponse
from app.reconstruction.model_registry import model_registry
from app.reconstruction.reconstruction_pipeline import reconstruction_pipeline

router = APIRouter(prefix="/api/v1/reconstruction", tags=["Reconstruction V1"])

# In-memory job store for async / polled reconstructions
JOB_STORE: Dict[str, Dict[str, Any]] = {}


class GenerateRequest(BaseModel):
    image_path: Optional[str] = None
    image_b64: Optional[str] = None
    model_name: Optional[str] = None
    quality_preset: str = Field(default="balanced", description="fast, balanced, high, or ultra_fast")
    export_formats: List[str] = Field(default=["glb", "obj"])
    preprocess_first: bool = True
    metadata: Optional[Dict[str, Any]] = None
    async_job: bool = False


@router.get("/health")
def reconstruction_health():
    """Health check inspects GPU availability, free VRAM, and registered models."""
    gpu_available = torch.cuda.is_available()
    gpu_name = torch.cuda.get_device_name(0) if gpu_available else "CPU"
    vram_total_gb = 0.0
    vram_free_gb = 0.0
    if gpu_available:
        props = torch.cuda.get_device_properties(0)
        vram_total_gb = round(props.total_memory / (1024 ** 3), 2)
        vram_reserved = torch.cuda.memory_reserved(0) / (1024 ** 3)
        vram_free_gb = round(vram_total_gb - vram_reserved, 2)

    available_models = model_registry.get_available_models()
    return {
        "status": "healthy",
        "gpu_available": gpu_available,
        "gpu_name": gpu_name,
        "vram_total_gb": vram_total_gb,
        "vram_free_gb": vram_free_gb,
        "available_models": available_models,
        "all_registered_models": [m.name for m in model_registry.list_models()]
    }


@router.get("/models")
def list_reconstruction_models():
    """Returns detailed metadata and status for all registered reconstruction adapters."""
    models_info = model_registry.list_models()
    return {
        "count": len(models_info),
        "models": [m.dict() for m in models_info]
    }


def _run_reconstruction_job(job_id: str, request: ReconstructionRequest):
    JOB_STORE[job_id]["status"] = "processing"
    try:
        response = reconstruction_pipeline.execute(request)
        if response.success:
            JOB_STORE[job_id]["status"] = "completed"
            JOB_STORE[job_id]["result"] = response.dict()
        else:
            JOB_STORE[job_id]["status"] = "failed"
            JOB_STORE[job_id]["error"] = response.error
    except Exception as e:
        JOB_STORE[job_id]["status"] = "failed"
        JOB_STORE[job_id]["error"] = str(e)


@router.post("/generate")
def generate_reconstruction(
    payload: GenerateRequest,
    background_tasks: BackgroundTasks
):
    """
    Submits a 2D sketch for 3D reconstruction.
    Supports either synchronous generation or asynchronous job tracking.
    """
    job_id = str(uuid.uuid4())[:8]
    job_dir = EXPORTS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    # Resolve input image
    image_file_path = None
    if payload.image_path and Path(payload.image_path).exists():
        image_file_path = payload.image_path
    elif payload.image_b64:
        # Decode base64
        b64_data = payload.image_b64
        if "," in b64_data:
            b64_data = b64_data.split(",", 1)[1]
        raw_bytes = base64.b64decode(b64_data)
        saved_img_path = job_dir / "input_sketch.png"
        with open(saved_img_path, "wb") as f:
            f.write(raw_bytes)
        image_file_path = str(saved_img_path)
    else:
        raise HTTPException(status_code=400, detail="Either 'image_path' or 'image_b64' must be provided.")

    rec_request = ReconstructionRequest(
        image_path=image_file_path,
        output_dir=str(job_dir),
        model_name=payload.model_name,
        quality_preset=payload.quality_preset,
        export_formats=payload.export_formats,
        metadata=payload.metadata,
        preprocess_first=payload.preprocess_first
    )

    JOB_STORE[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "created_at": time.time(),
        "result": None,
        "error": None
    }

    if payload.async_job:
        background_tasks.add_task(_run_reconstruction_job, job_id, rec_request)
        return {
            "job_id": job_id,
            "status": "queued",
            "message": "Reconstruction started asynchronously. Poll /api/v1/reconstruction/result/{job_id}."
        }
    else:
        _run_reconstruction_job(job_id, rec_request)
        job_data = JOB_STORE[job_id]
        if job_data["status"] == "failed":
            raise HTTPException(status_code=500, detail=job_data.get("error", "Reconstruction failed."))

        result = job_data["result"]
        # Add direct API download links
        downloads = {}
        for fmt, fpath in (result.get("formats") or {}).items():
            downloads[fmt] = f"/api/v1/reconstruction/download/{job_id}/{fmt}"

        return {
            "job_id": job_id,
            "status": "completed",
            "model_used": result.get("model_name"),
            "inference_time_seconds": result.get("inference_time_seconds"),
            "vertices": result.get("vertices"),
            "faces": result.get("faces"),
            "mesh_valid": result.get("mesh_valid"),
            "is_watertight": result.get("quality_report", {}).get("is_watertight", False),
            "formats": result.get("formats"),
            "downloads": downloads,
            "quality_report": result.get("quality_report")
        }


@router.get("/result/{job_id}")
def get_job_result(job_id: str):
    """Retrieves the status and result for an asynchronous reconstruction job."""
    if job_id not in JOB_STORE:
        raise HTTPException(status_code=404, detail=f"Job ID '{job_id}' not found.")
    return JOB_STORE[job_id]


@router.get("/download/{job_id}/{format}")
def download_asset(job_id: str, format: str):
    """Downloads an exported 3D asset file (glb, obj, mtl)."""
    fmt = format.lower().strip()
    job_dir = EXPORTS_DIR / job_id
    if not job_dir.exists():
        raise HTTPException(status_code=404, detail="Job directory not found.")

    # Search for matching file
    matching_files = list(job_dir.glob(f"*.{fmt}"))
    if not matching_files:
        raise HTTPException(status_code=404, detail=f"No .{fmt} file found for job {job_id}.")

    target_file = matching_files[0]
    media_types = {
        "glb": "model/gltf-binary",
        "obj": "text/plain",
        "mtl": "text/plain",
        "stl": "model/stl"
    }

    return FileResponse(
        path=target_file,
        media_type=media_types.get(fmt, "application/octet-stream"),
        filename=target_file.name
    )

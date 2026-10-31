"""
Health and System Status Route
Reports hardware status, GPU VRAM, CUDA capabilities, and connected engines.
"""

from fastapi import APIRouter
import sys
import os

router = APIRouter(prefix="/api/health", tags=["Health"])

@router.get("")
def get_health_status():
    gpu_info = {
        "cuda_available": False,
        "device_count": 0,
        "device_name": "N/A",
        "vram_total_mb": 0,
        "vram_allocated_mb": 0
    }

    try:
        import torch
        if torch.cuda.is_available():
            gpu_info["cuda_available"] = True
            gpu_info["device_count"] = torch.cuda.device_count()
            gpu_info["device_name"] = torch.cuda.get_device_name(0)
            gpu_info["vram_total_mb"] = round(torch.cuda.get_device_properties(0).total_memory / (1024 * 1024), 1)
            gpu_info["vram_allocated_mb"] = round(torch.cuda.memory_allocated(0) / (1024 * 1024), 1)
    except Exception:
        pass

    return {
        "status": "healthy",
        "version": "1.0.0",
        "python_version": sys.version.split()[0],
        "gpu": gpu_info,
        "local_procedural_engine": True,
        "colab_client_configured": bool(os.getenv("SKETCH2SHAPE_COLAB_URL"))
    }

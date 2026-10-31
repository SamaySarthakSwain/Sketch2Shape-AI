"""
FastAPI Routes for Sketch Intelligence & Semantic Recognition
Provides /api/v1/intelligence/analyze and /api/v1/intelligence/health endpoints.
"""

import time
import base64
from typing import Optional
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from pydantic import BaseModel

from app.sketch_intelligence.classifier import SketchIntelligenceEngine

router = APIRouter(prefix="/api/v1/intelligence", tags=["intelligence"])

# Global singleton engine instance
engine: Optional[SketchIntelligenceEngine] = None


def get_engine() -> SketchIntelligenceEngine:
    global engine
    if engine is None:
        engine = SketchIntelligenceEngine()
    return engine


class AnalyzeRequest(BaseModel):
    image_base64: Optional[str] = None
    bypass_preprocessing: bool = False


@router.get("/health")
async def health_check():
    """
    Health check endpoint returning model readiness, hardware device, and version info.
    """
    eng = get_engine()
    return {
        "status": "healthy",
        "model_loaded": eng.is_loaded,
        "device": str(eng.device),
        "num_classes": len(eng.class_names),
        "model_version": eng.config.get("model_version", "1.0.0"),
        "model_architecture": eng.config.get("selected_architecture", "Unknown")
    }


@router.post("/analyze")
async def analyze_sketch(
    file: Optional[UploadFile] = File(None),
    image_base64: Optional[str] = Form(None),
    bypass_preprocessing: bool = Form(False)
):
    """
    Analyzes an input sketch image (via multipart file or base64), runs semantic
    classification, uncertainty estimation, geometric tagging, and produces
    3D reconstruction conditioning payloads.
    """
    eng = get_engine()

    image_bytes = None
    if file is not None:
        image_bytes = await file.read()
    elif image_base64 is not None:
        if "," in image_base64:
            image_base64 = image_base64.split(",")[1]
        try:
            image_bytes = base64.b64decode(image_base64)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 encoding: {e}")
    else:
        raise HTTPException(status_code=400, detail="Must provide either multipart file or image_base64.")

    try:
        results = eng.analyze(image_bytes, bypass_preprocessing=bypass_preprocessing)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

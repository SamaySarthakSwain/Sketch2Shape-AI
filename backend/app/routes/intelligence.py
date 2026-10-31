"""
FastAPI Routes for Sketch Intelligence & Semantic Recognition
Provides /api/v1/intelligence/analyze and /api/v1/intelligence/health endpoints.
"""

import time
import base64
from typing import Optional
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Request
from pydantic import BaseModel

from app.sketch_intelligence.classifier import SketchIntelligenceEngine
from app.sketch_intelligence.gemini_vision_analyzer import gemini_vision_analyzer

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


class AnalyzePromptRequest(BaseModel):
    prompt: str


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
async def analyze_sketch(request: Request):
    """
    Analyzes an input sketch image (via JSON payload, multipart file, or base64 form field),
    runs semantic classification, uncertainty estimation, geometric tagging, and produces
    3D reconstruction conditioning payloads.
    """
    content_type = request.headers.get("content-type", "")
    image_bytes = None
    bypass = False

    if "application/json" in content_type:
        try:
            body = await request.json()
            raw_b64 = body.get("image_base64")
            bypass = bool(body.get("bypass_preprocessing", False))
            if raw_b64:
                if "," in raw_b64:
                    raw_b64 = raw_b64.split(",")[1]
                image_bytes = base64.b64decode(raw_b64)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse JSON body: {e}")
    else:
        try:
            form = await request.form()
            bypass_str = form.get("bypass_preprocessing", "false")
            bypass = str(bypass_str).lower() in ("true", "1")
            if "file" in form and hasattr(form["file"], "read"):
                image_bytes = await form["file"].read()
            elif "image_base64" in form:
                raw_b64 = str(form["image_base64"])
                if "," in raw_b64:
                    raw_b64 = raw_b64.split(",")[1]
                image_bytes = base64.b64decode(raw_b64)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse form data: {e}")

    if not image_bytes:
        raise HTTPException(status_code=400, detail="Must provide either JSON payload, multipart file, or image_base64.")

    eng = get_engine()
    try:
        results = eng.analyze(image_bytes, bypass_preprocessing=bypass)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/analyze-prompt")
async def analyze_prompt(req: AnalyzePromptRequest):
    """
    Analyzes a text prompt for Text-to-3D generation using Gemini / OpenAI:
    predicts the object class, visual properties, and extracts the color palette.
    """
    if not req.prompt or not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt string cannot be empty.")

    try:
        results = gemini_vision_analyzer.analyze_prompt(req.prompt.strip())
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prompt analysis failed: {str(e)}")

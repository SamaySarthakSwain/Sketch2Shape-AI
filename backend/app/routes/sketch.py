"""
Sketch Preprocessing and Intelligence Routes
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.preprocessing.sketch_processor import SketchPreprocessor
from app.sketch_intelligence.analyzer import SketchAnalyzer

router = APIRouter(prefix="/api/sketch", tags=["Sketch Processing"])

preprocessor = SketchPreprocessor(target_size=512)
analyzer = SketchAnalyzer()


class PreprocessRequest(BaseModel):
    image_b64: str
    target_size: Optional[int] = 512
    user_hint: Optional[str] = None


class AnalyzeRequest(BaseModel):
    binary_mask_b64: str
    bounding_box: list[int]
    user_hint: Optional[str] = None


@router.post("/preprocess")
def preprocess_sketch(req: PreprocessRequest):
    try:
        results = preprocessor.process(req.image_b64)
        # Automatically run intelligence analysis
        raw_mask = preprocessor.load_image(results["binary_mask_b64"])
        if len(raw_mask.shape) == 3:
            raw_mask = raw_mask[:, :, 0]

        intel = analyzer.analyze(
            binary_mask=raw_mask,
            bbox=results["bounding_box"],
            user_hint=req.user_hint
        )

        return {
            **results,
            "intelligence": intel
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Sketch preprocessing failed: {str(e)}")


@router.post("/analyze")
def analyze_sketch(req: AnalyzeRequest):
    try:
        raw_mask = preprocessor.load_image(req.binary_mask_b64)
        if len(raw_mask.shape) == 3:
            raw_mask = raw_mask[:, :, 0]

        intel = analyzer.analyze(
            binary_mask=raw_mask,
            bbox=req.bounding_box,
            user_hint=req.user_hint
        )
        return intel
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Sketch analysis failed: {str(e)}")

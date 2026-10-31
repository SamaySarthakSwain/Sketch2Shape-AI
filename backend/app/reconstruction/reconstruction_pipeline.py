"""
Master 3D Reconstruction Pipeline
Orchestrates:
1. Input ingestion and optional OpenCV preprocessing (Stage 5)
2. Semantic intelligence & feature extraction (Stage 6)
3. Semantically aware model selection (Stage 7 Phase 5)
4. AI 3D Reconstruction (InstantMesh / Procedural / Hunyuan / TripoSR)
5. Robust fallback handling
6. Geometric & topological mesh validation (Trimesh)
7. Texture analysis & multi-format export (GLB / OBJ)
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
import numpy as np
from PIL import Image

from app.reconstruction.reconstruction_config import (
    ReconstructionRequest,
    ReconstructionResponse,
    ModelInfo,
)
from app.reconstruction.model_registry import model_registry
from app.reconstruction.model_selector import ModelSelector
from app.reconstruction.mesh_validation import MeshValidator
from app.reconstruction.texture_processing import TextureProcessor
from app.reconstruction.export_manager import ExportManager


class ReconstructionPipeline:
    """
    Coordinated end-to-end 3D reconstruction pipeline.
    """

    def __init__(self):
        self._intelligence_engine = None
        self._preprocessing_pipeline = None

    def _get_intelligence_engine(self):
        if self._intelligence_engine is None:
            try:
                from app.sketch_intelligence.classifier import SketchIntelligenceEngine
                self._intelligence_engine = SketchIntelligenceEngine()
            except Exception as e:
                print(f"[ReconstructionPipeline] Intelligence engine unavailable: {e}")
                self._intelligence_engine = None
        return self._intelligence_engine

    def _get_preprocessing_pipeline(self):
        if self._preprocessing_pipeline is None:
            try:
                from app.preprocessing.preprocessing_pipeline import SketchPreprocessingPipeline
                self._preprocessing_pipeline = SketchPreprocessingPipeline()
            except Exception as e:
                print(f"[ReconstructionPipeline] Preprocessing pipeline unavailable: {e}")
                self._preprocessing_pipeline = None
        return self._preprocessing_pipeline

    def execute(self, request: ReconstructionRequest) -> ReconstructionResponse:
        """
        Executes end-to-end reconstruction from request specification.
        """
        t0 = time.time()
        print(f"\n=======================================================")
        print(f" [Sketch2Shape Pipeline] Ingesting: {request.image_path}")
        print(f"=======================================================")

        active_image_path = request.image_path
        semantic_metadata: Dict[str, Any] = request.metadata or {}

        # 1. Optional OpenCV Preprocessing
        if request.preprocess_first:
            prep = self._get_preprocessing_pipeline()
            if prep is not None:
                try:
                    print("[ReconstructionPipeline] Running OpenCV preprocessing...")
                    variants, report = prep.process(request.image_path)
                    prep_dir = Path(request.output_dir) / "preprocessed"
                    prep_dir.mkdir(parents=True, exist_ok=True)
                    stem = Path(request.image_path).stem
                    save_path = prep_dir / f"{stem}_preprocessed.png"
                    norm = variants.get("normalized")
                    if isinstance(norm, np.ndarray):
                        Image.fromarray(norm).save(str(save_path))
                    elif hasattr(norm, "save"):
                        norm.save(str(save_path))
                    else:
                        Image.open(request.image_path).save(str(save_path))
                    active_image_path = str(save_path)
                    print(f"[ReconstructionPipeline] Preprocessed image saved to {active_image_path}")
                except Exception as e:
                    print(f"[ReconstructionPipeline] Preprocessing warning: {e}. Using raw image.")

        # 2. Sketch Intelligence Analysis (if metadata not already supplied)
        category = semantic_metadata.get("category")
        confidence = float(semantic_metadata.get("confidence", 0.0))
        geometric_tags = semantic_metadata.get("geometric_tags", [])
        symmetry_scores = semantic_metadata.get("symmetry_scores", {})

        if not category:
            intel = self._get_intelligence_engine()
            if intel is not None:
                try:
                    print("[ReconstructionPipeline] Extracting sketch semantic intelligence...")
                    intel_result = intel.analyze(active_image_path)
                    category = intel_result.get("predicted_category", "unknown")
                    confidence = intel_result.get("top_prediction_confidence", intel_result.get("top_confidence", 0.0))
                    geometric_tags = intel_result.get("geometric_tags", [])
                    symmetry_scores = intel_result.get("symmetry", {})
                    semantic_metadata["category"] = category
                    semantic_metadata["confidence"] = confidence
                    semantic_metadata["geometric_tags"] = geometric_tags
                    semantic_metadata["symmetry_scores"] = symmetry_scores
                    print(f"[ReconstructionPipeline] Detected category: '{category}' (conf: {confidence:.2f})")
                except Exception as e:
                    print(f"[ReconstructionPipeline] Intelligence warning: {e}")

        # 3. Model Selection
        selected_model_name, selection_reason, config_overrides = ModelSelector.select_model(
            user_model=request.model_name,
            category=category,
            confidence=confidence,
            geometric_tags=geometric_tags,
            symmetry_scores=symmetry_scores,
            quality_preset=request.quality_preset,
            allow_fallback=True,
        )
        print(f"[ReconstructionPipeline] Selected Model: {selected_model_name} | Reason: {selection_reason}")

        adapter = model_registry.get_model(selected_model_name)
        if adapter is None or not adapter.is_available():
            print(f"[ReconstructionPipeline] Selected model '{selected_model_name}' unavailable. Using procedural fallback.")
            adapter = model_registry.get_model("procedural")
            selected_model_name = "procedural"

        # 4. Model Execution
        updated_request = ReconstructionRequest(
            image_path=active_image_path,
            output_dir=request.output_dir,
            model_name=selected_model_name,
            quality_preset=request.quality_preset,
            export_formats=request.export_formats,
            metadata=semantic_metadata,
            preprocess_first=False,  # Already preprocessed
        )

        response = adapter.reconstruct(updated_request)

        # 5. Fallback Handling
        if not response.success and selected_model_name != "procedural":
            print(f"[ReconstructionPipeline] Model {selected_model_name} failed: {response.error}. Triggering procedural fallback...")
            fallback_adapter = model_registry.get_model("procedural")
            if fallback_adapter:
                response = fallback_adapter.reconstruct(updated_request)
                response.model_name = f"{selected_model_name} -> procedural (fallback)"

        # 6. Texture Analysis
        if response.success and response.mesh_path:
            try:
                tex_info = TextureProcessor.inspect_texture(response.mesh_path)
                response.quality_report["texture_info"] = tex_info
            except Exception as e:
                print(f"[ReconstructionPipeline] Texture analysis warning: {e}")

        return response


# Global pipeline instance
reconstruction_pipeline = ReconstructionPipeline()

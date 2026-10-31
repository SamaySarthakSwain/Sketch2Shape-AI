"""
Unified Sketch Intelligence Classifier & Reasoning Engine
Coordinates model inference, uncertainty estimation, geometric tagging,
and semantic conditioning into a high-level API.
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
import numpy as np
import cv2
import torch
import torch.nn.functional as F
from PIL import Image

# Ensure backend modules are accessible
CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from .models import get_model
from .geometry_tags import GeometricFeatureTagger
from .uncertainty import UncertaintyEstimator
from .semantic_generator import SemanticDescriptionGenerator
from .reconstruction_conditioning import ReconstructionConditioner
from .gemini_vision_analyzer import gemini_vision_analyzer

from preprocessing.preprocessing_pipeline import SketchPreprocessingPipeline
from preprocessing.image_loader import ImageLoader


class SketchIntelligenceEngine:
    """
    High-level engine for sketch semantic classification, uncertainty quantification,
    and geometric prior extraction.
    """
    def __init__(
        self,
        models_dir: Optional[Union[str, Path]] = None,
        device: Optional[str] = None
    ):
        if models_dir is None:
            models_dir = Path(r"C:\Sketch2Shape-AI\models\sketch_intelligence")
        self.models_dir = Path(models_dir)

        # Device selection
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        # Internal components
        self.tagger = GeometricFeatureTagger()
        self.uncertainty_estimator = UncertaintyEstimator()
        self.preprocessing_pipeline = SketchPreprocessingPipeline(target_size=512)

        self.model = None
        self.config = {}
        self.class_mapping = {}
        self.class_names = []

        self._load_model_artifacts()

    def _load_model_artifacts(self):
        config_path = self.models_dir / "model_config.json"
        mapping_path = self.models_dir / "class_mapping.json"
        weights_path = self.models_dir / "best_model.pth"

        if not (config_path.exists() and mapping_path.exists() and weights_path.exists()):
            print(f"[WARN] Sketch intelligence model artifacts not fully present in {self.models_dir}")
            return

        with open(config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)

        with open(mapping_path, "r", encoding="utf-8") as f:
            self.class_mapping = json.load(f)

        self.class_names = self.class_mapping.get("target_categories", [])
        num_classes = len(self.class_names)
        arch_name = self.config.get("selected_architecture", "ResNet18_Adapted")

        # Instantiate model
        self.model = get_model(arch_name, num_classes=num_classes, in_channels=1)
        state_dict = torch.load(weights_path, map_location=self.device)
        self.model.load_state_dict(state_dict)
        self.model.to(self.device)
        self.model.eval()

        print(f"[INFO] Loaded {arch_name} on {self.device} ({num_classes} classes).")

    @property
    def is_loaded(self) -> bool:
        return self.model is not None

    def preprocess_image_tensor(self, image_input: Union[str, bytes, Path, Image.Image, np.ndarray]) -> Tuple[torch.Tensor, Any, Dict[str, Any]]:
        """
        Runs Stage 5 preprocessing, extracts 12-phase geometric metrics,
        and prepares 1x1x128x128 normalized input tensor for the neural network.
        """
        # Run full Stage 5 Preprocessing
        variants, stage5_report = self.preprocessing_pipeline.process(image_input)

        # We take the binary mask (255 = stroke, 0 = bg) from Stage 5
        binary_mask = variants["binary_image"]
        
        # Resize to canonical 128x128 for classifier
        resized_128 = cv2.resize(binary_mask, (128, 128), interpolation=cv2.INTER_AREA)

        # Convert to PyTorch float32 tensor in [0.0, 1.0]
        tensor = torch.from_numpy(resized_128).float().unsqueeze(0).unsqueeze(0) / 255.0
        tensor = tensor.to(self.device)

        return tensor, stage5_report, variants

    def analyze(
        self,
        image_input: Union[str, bytes, Path, Image.Image, np.ndarray],
        bypass_preprocessing: bool = False
    ) -> Dict[str, Any]:
        """
        End-to-end sketch intelligence analysis.
        """
        t0 = time.perf_counter()

        if not self.is_loaded:
            self._load_model_artifacts()
            if not self.is_loaded:
                raise RuntimeError("Sketch Intelligence model is not loaded.")

        if bypass_preprocessing:
            # Direct raw image mode
            bgr, alpha = ImageLoader.load(image_input)
            gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
            # Polarity inversion: if background is bright, invert so stroke is 255
            if np.mean(gray) > 127:
                gray = 255 - gray
            resized_128 = cv2.resize(gray, (128, 128), interpolation=cv2.INTER_AREA)
            tensor = torch.from_numpy(resized_128).float().unsqueeze(0).unsqueeze(0).to(self.device) / 255.0
            
            # Dummy geometry for raw bypass mode
            geometric_tags = ["unprocessed_raw_sketch"]
            geometry_metrics = {}
            stage5_report = None
        else:
            # Stage 5 Preprocessing
            tensor, stage5_report, variants = self.preprocess_image_tensor(image_input)
            geometric_tags = self.tagger.extract_tags(stage5_report)
            geometry_metrics = {
                "symmetry": stage5_report.symmetry,
                "shape_analysis": stage5_report.shape_analysis,
                "stroke_analysis": stage5_report.stroke_analysis,
                "metadata": stage5_report.metadata
            }

        # Model Inference (Local ResNet)
        with torch.no_grad():
            logits = self.model(tensor)
            probs = F.softmax(logits, dim=1).squeeze(0).cpu().numpy()

        # Uncertainty Estimation
        uncertainty_info = self.uncertainty_estimator.evaluate_predictions(probs, self.class_names)

        # Advanced Multimodal Vision & Color Analysis (Google Gemini / OpenAI Vision)
        ai_vision_info = {}
        try:
            ai_vision_info = gemini_vision_analyzer.analyze_sketch(image_input)
        except Exception as e:
            print(f"[SketchIntelligenceEngine] AI vision warning: {e}")

        # If Gemini returned a verified canonical category, synthesize with local model
        final_category = uncertainty_info["predicted_category"]
        predicted_object_name = uncertainty_info["predicted_category"].replace("_", " ").title()

        if ai_vision_info and ai_vision_info.get("success"):
            ai_cat = ai_vision_info.get("category")
            if ai_cat and ai_cat != "object":
                final_category = ai_cat
            if ai_vision_info.get("predicted_object"):
                predicted_object_name = str(ai_vision_info.get("predicted_object")).strip().title()

        # Color extraction attributes
        is_colorful = bool(ai_vision_info.get("is_colorful", False))
        primary_color_rgb = ai_vision_info.get("primary_color_rgb", [30, 30, 35])
        primary_color_hex = ai_vision_info.get("primary_color_hex", "#1E1E23")
        secondary_color_rgb = ai_vision_info.get("secondary_color_rgb", [240, 240, 245])
        secondary_color_hex = ai_vision_info.get("secondary_color_hex", "#F0F0F5")
        dominant_colors = ai_vision_info.get("dominant_colors", [])

        # Semantic Description & Hints
        semantic_info = SemanticDescriptionGenerator.generate(
            prediction_result={
                **uncertainty_info,
                "predicted_category": final_category
            },
            geometric_tags=geometric_tags,
            geometry_metrics=geometry_metrics
        )

        # Append visual color description if colorful
        desc = semantic_info["semantic_description"]
        if is_colorful and primary_color_hex:
            desc += f" Dominant color palette: {primary_color_hex} with accent {secondary_color_hex}."

        # Reconstruction Conditioning Payload
        conditioning = ReconstructionConditioner.build_conditioning_payload(
            category=final_category,
            confidence=ai_vision_info.get("confidence", uncertainty_info["top_confidence"]),
            is_ambiguous=uncertainty_info["is_ambiguous"],
            geometric_tags=geometric_tags,
            geometry_metrics=geometry_metrics
        )
        conditioning["is_colorful"] = is_colorful
        conditioning["primary_color_rgb"] = primary_color_rgb
        conditioning["primary_color_hex"] = primary_color_hex
        conditioning["secondary_color_rgb"] = secondary_color_rgb
        conditioning["secondary_color_hex"] = secondary_color_hex

        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)

        return {
            "predicted_category": final_category,
            "predicted_object": predicted_object_name,
            "top_confidence": float(ai_vision_info.get("confidence", uncertainty_info["top_confidence"])),
            "confidence_gap": uncertainty_info["confidence_gap"],
            "is_ambiguous": uncertainty_info["is_ambiguous"],
            "uncertainty_level": uncertainty_info["uncertainty_level"],
            "top_predictions": uncertainty_info["top_predictions"],
            "alternative_categories": uncertainty_info["alternative_categories"],
            "geometric_tags": geometric_tags,
            "semantic_description": desc,
            "reconstruction_hints": semantic_info["reconstruction_hints"],
            "reconstruction_conditioning": conditioning,
            "is_colorful": is_colorful,
            "primary_color_rgb": primary_color_rgb,
            "primary_color_hex": primary_color_hex,
            "secondary_color_rgb": secondary_color_rgb,
            "secondary_color_hex": secondary_color_hex,
            "dominant_colors": dominant_colors,
            "ai_vision_model": ai_vision_info.get("ai_model_used", "local_resnet"),
            "prompt_3d": ai_vision_info.get("prompt_3d", ""),
            "processing_time_ms": elapsed_ms,
            "model_version": self.config.get("model_version", "1.0.0"),
            "selected_architecture": self.config.get("selected_architecture", "Unknown"),
            "stage5_geometry": geometry_metrics if not bypass_preprocessing else None
        }

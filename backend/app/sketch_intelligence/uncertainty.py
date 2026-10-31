"""
Uncertainty Estimation and Ambiguity Detection for Sketch Intelligence
Evaluates prediction entropy, confidence gap between rank-1 and rank-2 candidates,
and identifies ambiguous or multi-modal sketch inputs.
"""

from typing import List, Dict, Any, Tuple
import numpy as np


class UncertaintyEstimator:
    """
    Evaluates epistemic uncertainty and distribution sharpness.
    Softmax confidence is treated as uncalibrated score unless temperature-scaled.
    Ambiguity is detected using the confidence gap: Delta = p_top1 - p_top2.
    """
    def __init__(
        self,
        min_confidence_threshold: float = 0.40,
        min_gap_threshold: float = 0.15,
        high_confidence_threshold: float = 0.70,
        high_gap_threshold: float = 0.30
    ):
        self.min_confidence = min_confidence_threshold
        self.min_gap = min_gap_threshold
        self.high_conf = high_confidence_threshold
        self.high_gap = high_gap_threshold

    def evaluate_predictions(
        self,
        probabilities: np.ndarray,
        class_names: List[str]
    ) -> Dict[str, Any]:
        """
        Takes raw softmax probabilities of shape (num_classes,) and returns structured uncertainty metrics.
        """
        # Sort descending
        top5_indices = np.argsort(probabilities)[::-1][:5]
        top5_preds = [
            {"class": class_names[idx], "confidence": round(float(probabilities[idx]), 4)}
            for idx in top5_indices
        ]

        p1 = top5_preds[0]["confidence"]
        p2 = top5_preds[1]["confidence"] if len(top5_preds) > 1 else 0.0
        confidence_gap = round(p1 - p2, 4)

        # Ambiguity classification
        is_ambiguous = False
        uncertainty_level = "low"

        if p1 < self.min_confidence or confidence_gap < self.min_gap:
            is_ambiguous = True
            uncertainty_level = "high"
        elif p1 < self.high_conf or confidence_gap < self.high_gap:
            uncertainty_level = "moderate"
            # If the gap is narrow, consider ambiguous
            if confidence_gap < self.min_gap * 1.5:
                is_ambiguous = True
        else:
            is_ambiguous = False
            uncertainty_level = "low"

        # Alternative plausible categories
        alternatives = [
            pred["class"] for pred in top5_preds[1:]
            if pred["confidence"] >= max(0.08, p1 * 0.25)
        ]

        return {
            "top_predictions": top5_preds,
            "predicted_category": top5_preds[0]["class"],
            "top_confidence": p1,
            "confidence_gap": confidence_gap,
            "is_ambiguous": is_ambiguous,
            "uncertainty_level": uncertainty_level,
            "alternative_categories": alternatives,
            "is_calibrated": False,
            "calibration_note": "Softmax confidence scores represent uncalibrated class likelihoods; epistemic ambiguity is regulated by the inter-class confidence gap."
        }

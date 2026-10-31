"""
Image Enhancement and Illumination Correction Module
Implements CLAHE, Gamma correction, Adaptive Contrast Stretch, and Morphological Illumination Equalization.
"""

from typing import Tuple, Dict, Any, Optional
import numpy as np
import cv2

from .schemas import EnhancementMetrics


class ImageEnhancer:
    def __init__(
        self,
        clahe_clip_limit: float = 2.0,
        clahe_grid_size: Tuple[int, int] = (8, 8),
        gamma: float = 1.0,
        enable_illumination_correction: bool = True
    ):
        self.clahe_clip_limit = clahe_clip_limit
        self.clahe_grid_size = clahe_grid_size
        self.gamma = gamma
        self.enable_illumination_correction = enable_illumination_correction
        self._clahe = cv2.createCLAHE(clipLimit=clahe_clip_limit, tileGridSize=clahe_grid_size)

    def analyze_histogram(self, gray: np.ndarray) -> Dict[str, float]:
        mean_val = float(np.mean(gray))
        std_val = float(np.std(gray))
        min_val = float(np.min(gray))
        max_val = float(np.max(gray))
        dyn_range = max_val - min_val
        return {
            "mean": round(mean_val, 2),
            "std": round(std_val, 2),
            "min": round(min_val, 2),
            "max": round(max_val, 2),
            "dynamic_range": round(dyn_range, 2)
        }

    def correct_background_illumination(self, gray: np.ndarray, kernel_size: int = 51) -> np.ndarray:
        """
        Estimates uneven paper/canvas illumination using a large morphological closing kernel,
        then normalizes foreground strokes against the estimated background plane.
        """
        # Ensure odd kernel size
        k = kernel_size if kernel_size % 2 == 1 else kernel_size + 1
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
        
        # Background estimation via morphological closing
        background = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
        
        # Division normalization: (gray / background) * 255
        with np.errstate(divide='ignore', invalid='ignore'):
            normalized = (gray.astype(np.float32) / np.maximum(background.astype(np.float32), 1.0)) * 255.0
            normalized = np.clip(normalized, 0, 255).astype(np.uint8)
        
        return normalized

    def apply_gamma(self, gray: np.ndarray, gamma: float) -> np.ndarray:
        if abs(gamma - 1.0) < 1e-3:
            return gray.copy()
        inv_gamma = 1.0 / max(gamma, 1e-4)
        table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
        return cv2.LUT(gray, table)

    def apply_clahe(self, gray: np.ndarray) -> np.ndarray:
        return self._clahe.apply(gray)

    def enhance(self, gray: np.ndarray, auto_select: bool = True) -> Tuple[np.ndarray, EnhancementMetrics]:
        stats_before = self.analyze_histogram(gray)
        processed = gray.copy()
        illum_applied = False

        if auto_select:
            # Check if illumination is uneven (high std on bright paper)
            if self.enable_illumination_correction and stats_before["std"] > 25.0:
                processed = self.correct_background_illumination(processed)
                illum_applied = True

            # Check if contrast is low (std < 40), then apply CLAHE
            if stats_before["std"] < 45.0 or stats_before["dynamic_range"] < 180:
                processed = self.apply_clahe(processed)

            # Check if image is overly dark or bright
            effective_gamma = self.gamma
            if stats_before["mean"] < 80:  # Dark canvas
                effective_gamma = 1.3
                processed = self.apply_gamma(processed, effective_gamma)
            elif stats_before["mean"] > 220:  # Very faint strokes on bright white
                effective_gamma = 0.8
                processed = self.apply_gamma(processed, effective_gamma)
        else:
            if self.enable_illumination_correction:
                processed = self.correct_background_illumination(processed)
                illum_applied = True
            processed = self.apply_clahe(processed)
            processed = self.apply_gamma(processed, self.gamma)

        stats_after = self.analyze_histogram(processed)

        metrics = EnhancementMetrics(
            mean_luminance_before=stats_before["mean"],
            mean_luminance_after=stats_after["mean"],
            contrast_std_before=stats_before["std"],
            contrast_std_after=stats_after["std"],
            dynamic_range=stats_after["dynamic_range"],
            gamma_applied=self.gamma,
            illumination_corrected=illum_applied
        )

        return processed, metrics

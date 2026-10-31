"""
Adaptive Thresholding and Mathematical Morphology Module
Implements Global, Otsu, Adaptive Gaussian, and Adaptive Mean thresholding with morphological refinement.
Guarantees standard binary convention: 255 = foreground stroke, 0 = background.
"""

from typing import Tuple, Dict, Any, Optional
import numpy as np
import cv2


class SketchThresholder:
    def __init__(
        self,
        adaptive_block_size: int = 15,
        adaptive_c: float = 8.0,
        morph_kernel_size: int = 3
    ):
        self.adaptive_block_size = adaptive_block_size if adaptive_block_size % 2 == 1 else adaptive_block_size + 1
        self.adaptive_c = adaptive_c
        self.morph_kernel_size = morph_kernel_size
        self._kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (morph_kernel_size, morph_kernel_size))

    @staticmethod
    def detect_and_invert_polarity(gray: np.ndarray, thresh: np.ndarray) -> np.ndarray:
        """
        Determines whether the drawing is dark-on-light (paper sketch) or light-on-dark (canvas brush).
        Ensures output binary mask has 255 for stroke, 0 for background.
        """
        # Count border pixels to estimate background intensity
        h, w = thresh.shape[:2]
        border_pixels = np.concatenate([
            thresh[0, :], thresh[-1, :], thresh[:, 0], thresh[:, -1]
        ])
        # If the majority of border pixels are 255, then 255 is background -> invert!
        if np.mean(border_pixels) > 127:
            return cv2.bitwise_not(thresh)
        return thresh

    def global_threshold(self, gray: np.ndarray, thresh_val: int = 127) -> np.ndarray:
        _, b = cv2.threshold(gray, thresh_val, 255, cv2.THRESH_BINARY_INV)
        return b

    def otsu_threshold(self, gray: np.ndarray) -> np.ndarray:
        _, b = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        return b

    def adaptive_gaussian(self, gray: np.ndarray) -> np.ndarray:
        b = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            self.adaptive_block_size,
            self.adaptive_c
        )
        return b

    def adaptive_mean(self, gray: np.ndarray) -> np.ndarray:
        b = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_MEAN_C,
            cv2.THRESH_BINARY_INV,
            self.adaptive_block_size,
            self.adaptive_c
        )
        return b

    # Mathematical Morphology
    def opening(self, mask: np.ndarray) -> np.ndarray:
        return cv2.morphologyEx(mask, cv2.MORPH_OPEN, self._kernel)

    def closing(self, mask: np.ndarray) -> np.ndarray:
        return cv2.morphologyEx(mask, cv2.MORPH_CLOSE, self._kernel)

    def dilate(self, mask: np.ndarray, iterations: int = 1) -> np.ndarray:
        return cv2.dilate(mask, self._kernel, iterations=iterations)

    def erode(self, mask: np.ndarray, iterations: int = 1) -> np.ndarray:
        return cv2.erode(mask, self._kernel, iterations=iterations)

    def binarize(
        self,
        gray: np.ndarray,
        method: str = "adaptive_gaussian",
        apply_morphology: bool = True
    ) -> np.ndarray:
        """
        Binarizes a grayscale sketch using the chosen method.
        Preserves fine line continuity and prevents destroying internal structures.
        """
        method_lower = method.lower()
        if method_lower == "otsu":
            raw_binary = self.otsu_threshold(gray)
        elif method_lower == "adaptive_mean":
            raw_binary = self.adaptive_mean(gray)
        elif method_lower == "global":
            raw_binary = self.global_threshold(gray)
        else:  # default adaptive_gaussian
            raw_binary = self.adaptive_gaussian(gray)

        # Standardize polarity
        binary = self.detect_and_invert_polarity(gray, raw_binary)

        if apply_morphology:
            # Gentle closing bridges hairline stroke breaks without filling loops
            kernel_small = cv2.getStructuringElement(cv2.MORPH_CROSS, (2, 2))
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel_small)

        return binary

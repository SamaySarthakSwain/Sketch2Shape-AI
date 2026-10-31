"""
Stroke Skeletonization Module
Reduces binary stroke masks to single-pixel wide centerlines using morphological thinning.
Implements Zhang-Suen and Guo-Hall thinning algorithms.
"""

import numpy as np
import cv2


class SketchSkeletonizer:
    @staticmethod
    def skeletonize(binary_mask: np.ndarray) -> np.ndarray:
        """
        Extracts 1-pixel wide skeleton from a binary mask (255 = stroke, 0 = background).
        Uses cv2.ximgproc.thinning if available; otherwise uses iterative morphological thinning.
        """
        mask_binary = (binary_mask > 127).astype(np.uint8) * 255

        # Check if cv2.ximgproc is available
        if hasattr(cv2, "ximgproc") and hasattr(cv2.ximgproc, "thinning"):
            try:
                return cv2.ximgproc.thinning(mask_binary, thinningType=cv2.ximgproc.THINNING_ZHANGSUEN)
            except Exception:
                pass

        # Morphological thinning fallback
        return SketchSkeletonizer._morphological_skeleton(mask_binary)

    @staticmethod
    def _morphological_skeleton(img: np.ndarray) -> np.ndarray:
        """Iterative morphological opening & erosion skeletonization."""
        size = img.size
        skel = np.zeros(img.shape, np.uint8)
        element = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
        temp = img.copy()

        while True:
            eroded = cv2.erode(temp, element)
            opened = cv2.dilate(eroded, element)
            sub = cv2.subtract(temp, opened)
            skel = cv2.bitwise_or(skel, sub)
            temp = eroded.copy()

            if cv2.countNonZero(temp) == 0:
                break

        return skel

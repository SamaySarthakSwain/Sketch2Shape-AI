"""
Bilateral & Reflection Symmetry Analysis Module
Measures horizontal and vertical reflectional symmetry using centroid-centered IoU.
Does not assume objects are inherently symmetrical; measures actual geometric invariance.
"""

from typing import Tuple, Dict, Any
import numpy as np
import cv2

from .schemas import SymmetryMetrics


class SymmetryAnalyzer:
    @staticmethod
    def _calculate_iou(mask_a: np.ndarray, mask_b: np.ndarray) -> float:
        intersection = np.count_nonzero((mask_a > 127) & (mask_b > 127))
        union = np.count_nonzero((mask_a > 127) | (mask_b > 127))
        if union == 0:
            return 0.0
        return float(intersection) / float(union)

    def analyze_symmetry(self, binary_mask: np.ndarray) -> SymmetryMetrics:
        """
        Calculates reflectional symmetry across horizontal and vertical mirror planes.
        Returns:
            SymmetryMetrics instance
        """
        h, w = binary_mask.shape[:2]
        if np.count_nonzero(binary_mask > 127) == 0:
            return SymmetryMetrics(
                horizontal_symmetry=0.0,
                vertical_symmetry=0.0,
                estimated_axis_x=float(w) / 2.0,
                estimated_axis_y=float(h) / 2.0,
                symmetry_score=0.0
            )

        # 1. Image Moments to find centroid of the sketch
        M = cv2.moments(binary_mask)
        if M["m00"] > 0:
            cx = float(M["m10"] / M["m00"])
            cy = float(M["m01"] / M["m00"])
        else:
            cx = float(w) / 2.0
            cy = float(h) / 2.0

        # 2. Centroid-aligned bounding box crop to isolate the object
        pts = cv2.findNonZero(binary_mask)
        bx, by, bw, bh = cv2.boundingRect(pts)
        obj_crop = binary_mask[by:by+bh, bx:bx+bw]

        # 3. Horizontal Reflection (Left vs Right mirror)
        # Flip along vertical axis (horizontal reflection)
        flipped_h = cv2.flip(obj_crop, 1)
        sym_h = self._calculate_iou(obj_crop, flipped_h)

        # 4. Vertical Reflection (Top vs Bottom mirror)
        # Flip along horizontal axis (vertical reflection)
        flipped_v = cv2.flip(obj_crop, 0)
        sym_v = self._calculate_iou(obj_crop, flipped_v)

        # 5. Overall composite symmetry score (max of bilateral planes)
        overall_score = float(max(sym_h, sym_v))

        return SymmetryMetrics(
            horizontal_symmetry=round(sym_h, 4),
            vertical_symmetry=round(sym_v, 4),
            estimated_axis_x=round(cx, 2),
            estimated_axis_y=round(cy, 2),
            symmetry_score=round(overall_score, 4)
        )

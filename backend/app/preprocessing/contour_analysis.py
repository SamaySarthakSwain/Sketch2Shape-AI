"""
Contour Intelligence and Hierarchical Geometric Analysis Module
Extracts contours, hierarchy trees, convex hulls, bounding boxes, solidity, and extent.
"""

from typing import Tuple, List, Dict, Any, Optional
import numpy as np
import cv2

from .schemas import ContourMetrics


class ContourAnalyzer:
    def __init__(self, min_contour_area: float = 15.0):
        self.min_contour_area = min_contour_area

    def analyze_contours(self, binary_mask: np.ndarray) -> Tuple[np.ndarray, ContourMetrics, List[np.ndarray]]:
        """
        Extracts and analyzes all contours in the binary mask (255 = stroke, 0 = background).
        Returns:
            contour_overlay: 3-channel RGB image with drawn contours and bounding boxes
            metrics: ContourMetrics instance
            all_contours: raw list of OpenCV contours
        """
        h, w = binary_mask.shape[:2]
        overlay = cv2.cvtColor(binary_mask, cv2.COLOR_GRAY2BGR)

        # Extract contours with full 2-level tree hierarchy
        contours, hierarchy = cv2.findContours(binary_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # Filter out negligible noise specks
        valid_contours = [c for c in contours if cv2.contourArea(c) >= self.min_contour_area]
        contour_count = len(valid_contours)

        if contour_count == 0:
            # Fallback if drawing has fine lines below area threshold
            valid_contours = [c for c in contours if len(c) >= 4]
            contour_count = len(valid_contours)

        if contour_count == 0:
            return overlay, ContourMetrics(
                contour_count=0,
                main_contour_area=0.0,
                main_contour_perimeter=0.0,
                bounding_box=(0, 0, 0, 0),
                convex_hull_area=0.0,
                solidity=0.0,
                extent=0.0,
                aspect_ratio=0.0,
                hierarchy_depth=0
            ), []

        # Find largest (main) contour by area
        main_contour = max(valid_contours, key=cv2.contourArea)
        area = float(cv2.contourArea(main_contour))
        perimeter = float(cv2.arcLength(main_contour, closed=True))
        bx, by, bw, bh = cv2.boundingRect(main_contour)
        aspect_ratio = float(bw) / float(bh) if bh > 0 else 0.0

        # Convex Hull and Solidity
        hull = cv2.convexHull(main_contour)
        hull_area = float(cv2.contourArea(hull))
        solidity = float(area / hull_area) if hull_area > 0 else 0.0

        # Extent (ratio of contour area to bounding box area)
        bbox_area = float(bw * bh)
        extent = float(area / bbox_area) if bbox_area > 0 else 0.0

        # Hierarchy depth calculation
        max_depth = 1
        if hierarchy is not None and len(hierarchy) > 0:
            # hierarchy array: [Next, Previous, First_Child, Parent]
            parents = hierarchy[0][:, 3]
            for p in parents:
                depth = 1
                curr = p
                while curr != -1 and depth < 10:
                    depth += 1
                    curr = hierarchy[0][curr][3]
                if depth > max_depth:
                    max_depth = depth

        # Draw overlays: Green for all contours, Cyan for main contour, Red for hull, Blue for bbox
        cv2.drawContours(overlay, valid_contours, -1, (0, 200, 0), 1)
        cv2.drawContours(overlay, [hull], -1, (0, 0, 255), 1)
        cv2.drawContours(overlay, [main_contour], -1, (255, 255, 0), 2)
        cv2.rectangle(overlay, (bx, by), (bx + bw, by + bh), (255, 100, 0), 1)

        metrics = ContourMetrics(
            contour_count=contour_count,
            main_contour_area=round(area, 2),
            main_contour_perimeter=round(perimeter, 2),
            bounding_box=(int(bx), int(by), int(bw), int(bh)),
            convex_hull_area=round(hull_area, 2),
            solidity=round(solidity, 4),
            extent=round(extent, 4),
            aspect_ratio=round(aspect_ratio, 4),
            hierarchy_depth=max_depth
        )

        return overlay, metrics, valid_contours

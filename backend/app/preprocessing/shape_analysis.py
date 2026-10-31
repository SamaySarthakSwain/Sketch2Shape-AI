"""
Shape Analysis and PCA Orientation Module
Extracts foreground occupancy, compactness, complexity, centroid, and major axis orientation via PCA.
"""

from typing import Tuple, Dict, Any, Optional
import numpy as np
import cv2

from .schemas import ShapeMetrics


class ShapeAnalyzer:
    @staticmethod
    def calculate_pca_orientation(points: np.ndarray) -> Tuple[float, float]:
        """
        Calculates principal orientation angle (degrees [-90, 90]) and eccentricity (lambda1 / lambda2)
        using Principal Component Analysis on 2D coordinates.
        """
        if len(points) < 5:
            return 0.0, 1.0

        # Reshape points to float32 matrix (N, 2)
        pts_2d = points.reshape(-1, 2).astype(np.float32)
        
        # Compute PCA
        mean, eigenvectors, eigenvalues = cv2.PCACompute2(pts_2d, mean=None)
        
        # Primary eigenvector determines orientation angle
        v1 = eigenvectors[0]
        angle_rad = np.arctan2(v1[1], v1[0])
        angle_deg = float(np.degrees(angle_rad))

        # Normalize to [-90, 90]
        if angle_deg > 90:
            angle_deg -= 180
        elif angle_deg < -90:
            angle_deg += 180

        # Eccentricity ratio (eigenvalues[0] / eigenvalues[1])
        e1 = float(eigenvalues[0][0]) if eigenvalues.shape[0] > 0 else 1.0
        e2 = float(eigenvalues[1][0]) if eigenvalues.shape[0] > 1 else 1e-4
        eccentricity = float(e1 / max(e2, 1e-4))

        return round(angle_deg, 2), round(eccentricity, 3)

    def analyze_shape(self, binary_mask: np.ndarray, main_contour: Optional[np.ndarray] = None) -> ShapeMetrics:
        h, w = binary_mask.shape[:2]
        total_pixels = float(h * w)

        fg_pixels = int(np.count_nonzero(binary_mask > 127))
        occupancy = float(fg_pixels) / total_pixels if total_pixels > 0 else 0.0

        pts = cv2.findNonZero(binary_mask)
        if pts is None or len(pts) == 0:
            return ShapeMetrics(
                foreground_occupancy=0.0,
                bounding_box=(0, 0, 0, 0),
                aspect_ratio=0.0,
                centroid=(0.0, 0.0),
                compactness=0.0,
                contour_complexity=0.0,
                edge_density=0.0,
                orientation_degrees=0.0,
                eccentricity=1.0
            )

        bx, by, bw, bh = cv2.boundingRect(pts)
        aspect_ratio = float(bw) / float(bh) if bh > 0 else 0.0

        # Centroid
        M = cv2.moments(binary_mask)
        if M["m00"] > 0:
            cx = float(M["m10"] / M["m00"])
            cy = float(M["m01"] / M["m00"])
        else:
            cx = float(bx + bw / 2.0)
            cy = float(by + bh / 2.0)

        # Compactness and Complexity
        if main_contour is not None and len(main_contour) >= 3:
            area = float(cv2.contourArea(main_contour))
            perimeter = float(cv2.arcLength(main_contour, closed=True))
            hull = cv2.convexHull(main_contour)
            hull_perimeter = float(cv2.arcLength(hull, closed=True))
            
            # Compactness / Circularity = 4 * pi * Area / (Perimeter^2)
            compactness = float((4.0 * np.pi * area) / max(perimeter**2, 1.0))
            compactness = float(np.clip(compactness, 0.0, 1.0))
            
            # Complexity: perimeter ratio relative to convex hull
            complexity = float(perimeter / max(hull_perimeter, 1.0))
        else:
            compactness = 0.5
            complexity = 1.0

        # PCA orientation
        orientation_deg, eccentricity = self.calculate_pca_orientation(pts)

        # Edge density inside bounding box
        bbox_crop = binary_mask[by:by+bh, bx:bx+bw]
        edge_density = float(np.count_nonzero(bbox_crop > 127)) / float(max(bw * bh, 1))

        return ShapeMetrics(
            foreground_occupancy=round(occupancy, 4),
            bounding_box=(int(bx), int(by), int(bw), int(bh)),
            aspect_ratio=round(aspect_ratio, 4),
            centroid=(round(cx, 2), round(cy, 2)),
            compactness=round(compactness, 4),
            contour_complexity=round(complexity, 3),
            edge_density=round(edge_density, 4),
            orientation_degrees=orientation_deg,
            eccentricity=eccentricity
        )

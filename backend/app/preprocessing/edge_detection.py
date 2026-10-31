"""
Edge Detection and Gradient Analysis Module
Implements Canny, Sobel, Laplacian, and Scharr operators with quantitative edge density calculation.
"""

from typing import Dict, Any, Tuple, Optional
import numpy as np
import cv2

from .schemas import EdgeMetrics


class EdgeDetector:
    def __init__(
        self,
        canny_low: Optional[int] = None,
        canny_high: Optional[int] = None,
        sobel_ksize: int = 3,
        laplacian_ksize: int = 3
    ):
        self.canny_low = canny_low
        self.canny_high = canny_high
        self.sobel_ksize = sobel_ksize
        self.laplacian_ksize = laplacian_ksize

    def auto_canny(self, gray: np.ndarray, sigma: float = 0.33) -> np.ndarray:
        """Canny with automatic Otsu/median-derived threshold bounds."""
        if self.canny_low is not None and self.canny_high is not None:
            return cv2.Canny(gray, self.canny_low, self.canny_high)

        v = np.median(gray)
        lower = int(max(0, (1.0 - sigma) * v))
        upper = int(min(255, (1.0 + sigma) * v))
        return cv2.Canny(gray, lower, upper)

    def sobel(self, gray: np.ndarray) -> np.ndarray:
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=self.sobel_ksize)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=self.sobel_ksize)
        magnitude = np.sqrt(grad_x**2 + grad_y**2)
        norm = np.clip((magnitude / np.max(magnitude) * 255) if np.max(magnitude) > 0 else magnitude, 0, 255)
        return norm.astype(np.uint8)

    def laplacian(self, gray: np.ndarray) -> np.ndarray:
        lap = cv2.Laplacian(gray, cv2.CV_64F, ksize=self.laplacian_ksize)
        abs_lap = np.absolute(lap)
        norm = np.clip((abs_lap / np.max(abs_lap) * 255) if np.max(abs_lap) > 0 else abs_lap, 0, 255)
        return norm.astype(np.uint8)

    def scharr(self, gray: np.ndarray) -> np.ndarray:
        grad_x = cv2.Scharr(gray, cv2.CV_64F, 1, 0)
        grad_y = cv2.Scharr(gray, cv2.CV_64F, 0, 1)
        magnitude = np.sqrt(grad_x**2 + grad_y**2)
        norm = np.clip((magnitude / np.max(magnitude) * 255) if np.max(magnitude) > 0 else magnitude, 0, 255)
        return norm.astype(np.uint8)

    @staticmethod
    def calculate_edge_density(edge_map: np.ndarray, threshold: int = 50) -> float:
        total_pixels = edge_map.size
        edge_pixels = int(np.count_nonzero(edge_map > threshold))
        return round(float(edge_pixels) / float(total_pixels), 4)

    def detect_all(self, gray: np.ndarray) -> Dict[str, np.ndarray]:
        return {
            "canny": self.auto_canny(gray),
            "sobel": self.sobel(gray),
            "laplacian": self.laplacian(gray),
            "scharr": self.scharr(gray)
        }

    def detect_and_measure(self, gray: np.ndarray, preferred_method: str = "canny") -> Tuple[np.ndarray, EdgeMetrics]:
        canny_map = self.auto_canny(gray)
        sobel_map = self.sobel(gray)
        lap_map = self.laplacian(gray)

        canny_density = self.calculate_edge_density(canny_map, threshold=128)
        sobel_density = self.calculate_edge_density(sobel_map, threshold=60)
        lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())

        selected_map = canny_map if preferred_method.lower() == "canny" else sobel_map
        selected_density = canny_density if preferred_method.lower() == "canny" else sobel_density

        metrics = EdgeMetrics(
            edge_density=selected_density,
            canny_density=canny_density,
            sobel_density=sobel_density,
            laplacian_variance=round(lap_var, 2),
            selected_method=preferred_method
        )

        return selected_map, metrics

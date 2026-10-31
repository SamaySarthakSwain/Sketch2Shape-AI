"""
Stroke Analysis and Topological Graph Extraction Module
Analyzes stroke geometry, approximate width (via Euclidean distance transform),
endpoints, junctions, and connected components.

NOTE ON ESTIMATION ACCURACY:
Measurements here are 2D image-space geometric approximations derived from rasterized strokes.
They do not represent calibrated physical stylus pressure or real-time temporal pen dynamics.
"""

from typing import Dict, Any, Tuple, List
import numpy as np
import cv2
from scipy.signal import convolve2d

from .skeletonization import SketchSkeletonizer
from .schemas import StrokeMetrics


class StrokeAnalyzer:
    def __init__(self):
        # 8-neighbor convolution kernel for endpoint and junction detection
        self._neighbor_kernel = np.array([
            [1, 1, 1],
            [1, 0, 1],
            [1, 1, 1]
        ], dtype=np.uint8)

    def analyze_strokes(self, binary_mask: np.ndarray) -> Tuple[np.ndarray, np.ndarray, StrokeMetrics]:
        """
        Performs full topological and stroke analysis on a binary mask (255 = stroke, 0 = background).
        Returns:
            skeleton: 1-pixel wide skeleton image
            dist_transform: Euclidean distance transform
            metrics: StrokeMetrics instance
        """
        h, w = binary_mask.shape[:2]
        total_pixels = float(h * w)

        # 1. Skeletonization
        skeleton = SketchSkeletonizer.skeletonize(binary_mask)
        skel_mask = skeleton > 127
        skel_pixel_count = int(np.count_nonzero(skel_mask))

        # 2. Euclidean Distance Transform (L2 metric)
        dist_transform = cv2.distanceTransform(binary_mask, cv2.DIST_L2, 5)

        # 3. Approximate stroke width along centerline
        if skel_pixel_count > 0:
            radii = dist_transform[skel_mask]
            # Diameter = radius * 2
            avg_width = float(np.mean(radii)) * 2.0
        else:
            avg_width = 0.0

        # 4. Stroke density
        stroke_density = float(skel_pixel_count) / total_pixels if total_pixels > 0 else 0.0

        # 5. Topological graph: Endpoints & Junctions via 8-neighborhood convolution
        if skel_pixel_count > 0:
            skel_binary_01 = skel_mask.astype(np.uint8)
            # Convolve to get neighbor count for every pixel
            neighbor_count = convolve2d(skel_binary_01, self._neighbor_kernel, mode='same')
            
            # Endpoints: on skeleton with exactly 1 neighbor
            endpoints_mask = (skel_binary_01 == 1) & (neighbor_count == 1)
            endpoint_count = int(np.count_nonzero(endpoints_mask))

            # Junctions: on skeleton with 3 or more neighbors
            junctions_mask = (skel_binary_01 == 1) & (neighbor_count >= 3)
            junction_count = int(np.count_nonzero(junctions_mask))
        else:
            endpoint_count = 0
            junction_count = 0

        # 6. Connected Components Analysis
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary_mask, connectivity=8)
        # num_labels includes background (label 0), so foreground components = num_labels - 1
        connected_components_count = max(0, num_labels - 1)

        # 7. Line continuity estimation: ratio of length to discontinuities
        # Higher score (near 1.0) indicates continuous clean curves; lower indicates fragmented noise
        discontinuities = endpoint_count + connected_components_count
        if skel_pixel_count > 0 and discontinuities > 0:
            continuity_ratio = float(skel_pixel_count) / (float(discontinuities) * 20.0)
            continuity_score = float(np.clip(continuity_ratio, 0.0, 1.0))
        elif skel_pixel_count > 0:
            continuity_score = 1.0
        else:
            continuity_score = 0.0

        metrics = StrokeMetrics(
            average_width_estimate=round(avg_width, 2),
            stroke_density=round(stroke_density, 4),
            total_stroke_length=float(skel_pixel_count),
            endpoint_count=endpoint_count,
            junction_count=junction_count,
            connected_components_count=connected_components_count,
            line_continuity_score=round(continuity_score, 3)
        )

        return skeleton, dist_transform, metrics

    def extract_graph_points(self, skeleton: np.ndarray) -> Dict[str, List[Tuple[int, int]]]:
        """Returns pixel coordinates (x, y) of endpoints and junctions."""
        skel_mask = (skeleton > 127).astype(np.uint8)
        if np.count_nonzero(skel_mask) == 0:
            return {"endpoints": [], "junctions": []}

        neighbor_count = convolve2d(skel_mask, self._neighbor_kernel, mode='same')
        
        ep_ys, ep_xs = np.where((skel_mask == 1) & (neighbor_count == 1))
        j_ys, j_xs = np.where((skel_mask == 1) & (neighbor_count >= 3))

        endpoints = [(int(x), int(y)) for x, y in zip(ep_xs, ep_ys)]
        junctions = [(int(x), int(y)) for x, y in zip(j_xs, j_ys)]

        return {
            "endpoints": endpoints,
            "junctions": junctions
        }

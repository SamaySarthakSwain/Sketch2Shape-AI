"""
Unit Tests for Stroke Analysis and Skeletonization Module
Validates skeleton extraction, endpoint/junction graph detection, and distance transform width estimation.
"""

import sys
from pathlib import Path
import numpy as np
import cv2
import pytest

BASE_DIR = Path("C:/Sketch2Shape-AI").resolve()
BACKEND_DIR = BASE_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.preprocessing import StrokeAnalyzer, SketchSkeletonizer


def test_single_line_segment():
    mask = np.zeros((150, 150), dtype=np.uint8)
    # Draw horizontal line from x=30 to x=120 with thickness=6 (radius ~ 3)
    cv2.line(mask, (30, 75), (120, 75), 255, thickness=6)

    analyzer = StrokeAnalyzer()
    skeleton, dist, metrics = analyzer.analyze_strokes(mask)

    # Skeleton must have non-zero pixels
    assert np.count_nonzero(skeleton > 127) > 0
    # Line segment must have 2 endpoints
    assert metrics.endpoint_count == 2
    # No branch junctions on straight line
    assert metrics.junction_count == 0
    # Average width estimate should approximate 6-8 pixels
    assert 4.0 <= metrics.average_width_estimate <= 9.0
    # Connected component count is 1
    assert metrics.connected_components_count == 1
    # Continuity score should be high
    assert metrics.line_continuity_score > 0.5


def test_t_junction_detection():
    mask = np.zeros((150, 150), dtype=np.uint8)
    # Horizontal bar
    cv2.line(mask, (30, 50), (120, 50), 255, thickness=4)
    # Vertical stem connecting at (75, 50)
    cv2.line(mask, (75, 50), (75, 120), 255, thickness=4)

    analyzer = StrokeAnalyzer()
    skeleton, dist, metrics = analyzer.analyze_strokes(mask)

    # T-junction has 3 endpoints (with possible 1-pixel spur variation at thick intersections)
    assert metrics.endpoint_count in (3, 4)
    # Must detect the intersection junction point
    assert metrics.junction_count >= 1

    graph = analyzer.extract_graph_points(skeleton)
    assert len(graph["endpoints"]) in (3, 4)
    assert len(graph["junctions"]) >= 1


def test_disconnected_strokes():
    mask = np.zeros((150, 150), dtype=np.uint8)
    # Draw 3 separated dots/lines
    cv2.line(mask, (20, 20), (50, 20), 255, thickness=3)
    cv2.line(mask, (20, 70), (50, 70), 255, thickness=3)
    cv2.line(mask, (20, 120), (50, 120), 255, thickness=3)

    analyzer = StrokeAnalyzer()
    skeleton, dist, metrics = analyzer.analyze_strokes(mask)

    assert metrics.connected_components_count == 3
    assert metrics.endpoint_count == 6  # 2 endpoints per stroke


def test_empty_stroke_mask():
    blank = np.zeros((100, 100), dtype=np.uint8)
    analyzer = StrokeAnalyzer()
    skeleton, dist, metrics = analyzer.analyze_strokes(blank)

    assert metrics.endpoint_count == 0
    assert metrics.junction_count == 0
    assert metrics.average_width_estimate == 0.0
    assert metrics.connected_components_count == 0

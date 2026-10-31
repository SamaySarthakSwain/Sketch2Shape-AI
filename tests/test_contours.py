"""
Unit Tests for Contour Intelligence Module
Validates contour extraction, hierarchy trees, convex hulls, solidity, and extent.
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

from app.preprocessing import ContourAnalyzer


def test_rectangle_contour_properties():
    mask = np.zeros((200, 200), dtype=np.uint8)
    # Draw filled rectangle from (40, 40) to (140, 100) -> w=100, h=60, area=6000
    cv2.rectangle(mask, (40, 40), (140, 100), 255, -1)

    analyzer = ContourAnalyzer(min_contour_area=50.0)
    overlay, metrics, contours = analyzer.analyze_contours(mask)

    assert metrics.contour_count == 1
    assert abs(metrics.main_contour_area - 6000.0) < 150.0  # slight discretization variance
    assert metrics.solidity > 0.95  # convex shape has solidity ~ 1.0
    assert metrics.extent > 0.95    # fills bounding box
    assert metrics.bounding_box[2] >= 99  # width
    assert metrics.bounding_box[3] >= 59  # height
    assert overlay.shape == (200, 200, 3)


def test_donut_hierarchy():
    mask = np.zeros((200, 200), dtype=np.uint8)
    # Outer circle filled
    cv2.circle(mask, (100, 100), 60, 255, -1)
    # Inner circle cut out
    cv2.circle(mask, (100, 100), 25, 0, -1)

    analyzer = ContourAnalyzer(min_contour_area=50.0)
    overlay, metrics, contours = analyzer.analyze_contours(mask)

    # Must detect both outer boundary and inner hole (hierarchy depth >= 2)
    assert metrics.contour_count >= 1
    assert metrics.hierarchy_depth >= 2


def test_u_shape_solidity():
    # U-shape / horseshoe is non-convex (solidity < 0.85)
    mask = np.zeros((200, 200), dtype=np.uint8)
    # Draw U-shape
    cv2.rectangle(mask, (40, 40), (70, 160), 255, -1)
    cv2.rectangle(mask, (130, 40), (160, 160), 255, -1)
    cv2.rectangle(mask, (40, 130), (160, 160), 255, -1)

    analyzer = ContourAnalyzer(min_contour_area=50.0)
    overlay, metrics, contours = analyzer.analyze_contours(mask)

    assert metrics.contour_count == 1
    assert metrics.solidity < 0.85


def test_empty_mask_handling():
    blank = np.zeros((100, 100), dtype=np.uint8)
    analyzer = ContourAnalyzer()
    overlay, metrics, contours = analyzer.analyze_contours(blank)
    assert metrics.contour_count == 0
    assert metrics.main_contour_area == 0.0
    assert metrics.solidity == 0.0

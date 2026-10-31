"""
Unit Tests for Shape Analysis and PCA Orientation Module
Validates foreground occupancy, compactness, complexity, aspect ratio, and PCA orientation.
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

from app.preprocessing import ShapeAnalyzer, ContourAnalyzer


def test_circle_compactness():
    mask = np.zeros((200, 200), dtype=np.uint8)
    cv2.circle(mask, (100, 100), 40, 255, -1)

    c_analyzer = ContourAnalyzer()
    _, _, contours = c_analyzer.analyze_contours(mask)

    s_analyzer = ShapeAnalyzer()
    metrics = s_analyzer.analyze_shape(mask, contours[0])

    # A perfect circle has maximum compactness (~1.0)
    assert metrics.compactness > 0.85
    assert abs(metrics.aspect_ratio - 1.0) < 0.1
    assert abs(metrics.centroid[0] - 100.0) < 2.0
    assert abs(metrics.centroid[1] - 100.0) < 2.0


def test_pca_orientation_horizontal():
    # Long horizontal bar: angle should be close to 0 degrees
    mask = np.zeros((200, 200), dtype=np.uint8)
    cv2.rectangle(mask, (20, 95), (180, 105), 255, -1)

    s_analyzer = ShapeAnalyzer()
    metrics = s_analyzer.analyze_shape(mask)

    assert abs(metrics.orientation_degrees) < 15.0
    assert metrics.aspect_ratio > 10.0
    assert metrics.eccentricity > 10.0


def test_pca_orientation_vertical():
    # Long vertical bar: angle should be close to +/- 90 degrees
    mask = np.zeros((200, 200), dtype=np.uint8)
    cv2.rectangle(mask, (95, 20), (105, 180), 255, -1)

    s_analyzer = ShapeAnalyzer()
    metrics = s_analyzer.analyze_shape(mask)

    assert abs(abs(metrics.orientation_degrees) - 90.0) < 15.0
    assert metrics.aspect_ratio < 0.1


def test_foreground_occupancy():
    mask = np.zeros((100, 100), dtype=np.uint8)
    # Fill exactly 25% of the image (50x50 = 2500 pixels out of 10000)
    mask[0:50, 0:50] = 255

    s_analyzer = ShapeAnalyzer()
    metrics = s_analyzer.analyze_shape(mask)

    assert abs(metrics.foreground_occupancy - 0.25) < 1e-3

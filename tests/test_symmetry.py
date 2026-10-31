"""
Unit Tests for Symmetry Analysis Module
Validates reflectional symmetry across horizontal and vertical mirror planes.
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

from app.preprocessing import SymmetryAnalyzer


def test_perfect_bilateral_symmetry():
    # Symmetric circle in center
    mask = np.zeros((200, 200), dtype=np.uint8)
    cv2.circle(mask, (100, 100), 45, 255, -1)

    analyzer = SymmetryAnalyzer()
    metrics = analyzer.analyze_symmetry(mask)

    # Circle is symmetric across both axes
    assert metrics.horizontal_symmetry > 0.95
    assert metrics.vertical_symmetry > 0.95
    assert metrics.symmetry_score > 0.95
    assert abs(metrics.estimated_axis_x - 100.0) < 2.0
    assert abs(metrics.estimated_axis_y - 100.0) < 2.0


def test_horizontal_only_symmetry():
    # Symmetric vase / wine glass outline (symmetric left-right, asymmetric top-bottom)
    mask = np.zeros((200, 200), dtype=np.uint8)
    # Bowl on top
    cv2.circle(mask, (100, 70), 40, 255, -1)
    # Stem in middle
    cv2.rectangle(mask, (95, 110), (105, 160), 255, -1)
    # Base on bottom
    cv2.rectangle(mask, (70, 160), (130, 170), 255, -1)

    analyzer = SymmetryAnalyzer()
    metrics = analyzer.analyze_symmetry(mask)

    # Must have high horizontal symmetry (left-right mirror)
    assert metrics.horizontal_symmetry > 0.90
    # Must have low vertical symmetry (top-bottom mirror)
    assert metrics.vertical_symmetry < 0.65


def test_asymmetrical_shape():
    # L-shape: highly asymmetric
    mask = np.zeros((200, 200), dtype=np.uint8)
    cv2.rectangle(mask, (30, 30), (50, 150), 255, -1)
    cv2.rectangle(mask, (30, 130), (150, 150), 255, -1)

    analyzer = SymmetryAnalyzer()
    metrics = analyzer.analyze_symmetry(mask)

    assert metrics.horizontal_symmetry < 0.60
    assert metrics.vertical_symmetry < 0.60
    assert metrics.symmetry_score < 0.60


def test_blank_symmetry():
    blank = np.zeros((100, 100), dtype=np.uint8)
    analyzer = SymmetryAnalyzer()
    metrics = analyzer.analyze_symmetry(blank)
    assert metrics.symmetry_score == 0.0

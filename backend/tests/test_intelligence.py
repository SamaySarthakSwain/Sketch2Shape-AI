import numpy as np
import cv2
import pytest
from app.sketch_intelligence.analyzer import SketchAnalyzer

@pytest.fixture
def analyzer():
    return SketchAnalyzer()

@pytest.fixture
def symmetric_vase_mask():
    mask = np.zeros((512, 512), dtype=np.uint8)
    # Draw symmetric vase outline
    cv2.ellipse(mask, (256, 300), (80, 120), 0, 0, 360, 255, thickness=cv2.FILLED)
    cv2.rectangle(mask, (216, 120), (296, 200), 255, thickness=cv2.FILLED)
    return mask

def test_symmetry_computation(analyzer, symmetric_vase_mask):
    sym = analyzer.compute_symmetry(symmetric_vase_mask)
    assert "vertical_symmetry" in sym
    assert "horizontal_symmetry" in sym
    # Since vase is drawn symmetrically centered at 256, vertical symmetry should be high (> 0.8)
    assert sym["vertical_symmetry"] > 0.80

def test_geometry_analysis(analyzer, symmetric_vase_mask):
    geo = analyzer.analyze_geometry(symmetric_vase_mask, [136, 120, 240, 300])
    assert geo["aspect_ratio"] > 0
    assert geo["solidity"] > 0.5
    assert geo["contour_count"] >= 1

def test_classification_and_prompt(analyzer, symmetric_vase_mask):
    res = analyzer.analyze(symmetric_vase_mask, [136, 120, 240, 300])
    assert "classification" in res
    assert "synthesis_prompt" in res
    assert "recommended_3d_mode" in res
    assert res["recommended_3d_mode"] in ["rotational_symmetric", "hybrid", "extrusion_symmetric", "bilateral_symmetric"]

def test_user_hint_override(analyzer, symmetric_vase_mask):
    res = analyzer.analyze(symmetric_vase_mask, [136, 120, 240, 300], user_hint="futuristic cyber chair")
    assert "futuristic cyber chair" in res["synthesis_prompt"]

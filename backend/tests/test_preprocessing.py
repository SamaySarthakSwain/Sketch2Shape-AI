import numpy as np
import cv2
import pytest
from app.preprocessing.sketch_processor import SketchPreprocessor

@pytest.fixture
def preprocessor():
    return SketchPreprocessor(target_size=512, padding_pct=0.1)

@pytest.fixture
def synthetic_vase_sketch():
    # Create synthetic drawing of a vase (white canvas, black contour)
    img = np.ones((400, 400), dtype=np.uint8) * 255
    # Draw bottle/vase profile
    cv2.ellipse(img, (200, 260), (70, 100), 0, 0, 360, 0, thickness=6)
    cv2.rectangle(img, (170, 100), (230, 160), 0, thickness=6)
    return img

def test_load_and_standardize(preprocessor, synthetic_vase_sketch):
    mask, gray = preprocessor.standardize_strokes(synthetic_vase_sketch)
    assert mask.shape == (400, 400)
    # Check that strokes are extracted as 255
    assert np.any(mask == 255)

def test_center_and_crop(preprocessor, synthetic_vase_sketch):
    mask, _ = preprocessor.standardize_strokes(synthetic_vase_sketch)
    centered, bbox = preprocessor.center_and_crop(mask)
    assert centered.shape == (512, 512)
    assert len(bbox) == 4
    x, y, w, h = bbox
    assert w > 0 and h > 0

def test_depth_and_normals(preprocessor, synthetic_vase_sketch):
    mask, _ = preprocessor.standardize_strokes(synthetic_vase_sketch)
    centered, _ = preprocessor.center_and_crop(mask)
    depth, normal_map = preprocessor.generate_depth_and_normals(centered)
    
    assert depth.shape == (512, 512)
    assert normal_map.shape == (512, 512, 3)
    # Check normal map values are within valid byte range
    assert normal_map.min() >= 0 and normal_map.max() <= 255

def test_full_pipeline(preprocessor, synthetic_vase_sketch):
    res = preprocessor.process(synthetic_vase_sketch)
    assert res["success"] is True
    assert "cleaned_image_b64" in res
    assert "depth_map_b64" in res
    assert "normal_map_b64" in res
    assert res["stroke_density"] > 0

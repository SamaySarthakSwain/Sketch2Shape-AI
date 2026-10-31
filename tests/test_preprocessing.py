"""
Unit Tests for OpenCV Preprocessing Pipeline
Tests validation, enhancement, denoising, edge detection, binarization, normalization, and full pipeline execution.
"""

import os
import sys
from pathlib import Path
import numpy as np
import cv2
import pytest

# Ensure backend is on sys.path
BASE_DIR = Path("C:/Sketch2Shape-AI").resolve()
BACKEND_DIR = BASE_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.preprocessing import (
    ImageLoader,
    ImageValidator,
    ImageEnhancer,
    SketchDenoiser,
    EdgeDetector,
    SketchThresholder,
    ForegroundExtractor,
    SketchNormalizer,
    SketchPreprocessingPipeline,
    PreprocessingReport
)


def create_synthetic_sketch(size: int = 256) -> np.ndarray:
    """Creates a synthetic black stroke drawing on white canvas."""
    img = np.full((size, size, 3), 255, dtype=np.uint8)
    # Draw circle
    cv2.circle(img, (128, 128), 50, (0, 0, 0), 4)
    # Draw vertical line
    cv2.line(img, (128, 78), (128, 178), (0, 0, 0), 3)
    return img


def test_image_loader_and_validation():
    sketch = create_synthetic_sketch(256)
    bgr, alpha = ImageLoader.load(sketch)
    assert bgr.shape == (256, 256, 3)
    assert alpha is None

    val_res = ImageValidator.validate_array(bgr, alpha)
    assert val_res.is_valid is True
    assert val_res.dimensions.width == 256
    assert val_res.dimensions.height == 256
    assert val_res.dimensions.channels == 3
    assert abs(val_res.dimensions.aspect_ratio - 1.0) < 1e-3


def test_validation_rejects_blank_image():
    blank = np.full((256, 256, 3), 255, dtype=np.uint8)
    val_res = ImageValidator.validate_array(blank)
    assert val_res.is_valid is False
    assert "blank" in val_res.error_message.lower() or "variance" in val_res.error_message.lower()


def test_enhancement_and_denoising():
    sketch = create_synthetic_sketch(256)
    gray = ImageLoader.to_grayscale(sketch)
    enhancer = ImageEnhancer()
    enhanced, metrics = enhancer.enhance(gray)
    assert enhanced.shape == (256, 256)
    assert metrics.dynamic_range >= 0

    denoiser = SketchDenoiser()
    denoised = denoiser.denoise_for_reconstruction(enhanced, method="bilateral")
    assert denoised.shape == (256, 256)


def test_edge_detection():
    sketch = create_synthetic_sketch(256)
    gray = ImageLoader.to_grayscale(sketch)
    detector = EdgeDetector()
    edge_map, metrics = detector.detect_and_measure(gray)
    assert edge_map.shape == (256, 256)
    assert metrics.edge_density > 0.0
    assert metrics.selected_method == "canny"


def test_thresholding_and_morphology():
    sketch = create_synthetic_sketch(256)
    gray = ImageLoader.to_grayscale(sketch)
    thresholder = SketchThresholder()
    binary = thresholder.binarize(gray, method="adaptive_gaussian")
    assert binary.shape == (256, 256)
    # Strokes must be 255, background 0
    assert np.count_nonzero(binary == 255) > 0
    assert np.count_nonzero(binary == 0) > np.count_nonzero(binary == 255)


def test_normalization():
    sketch = create_synthetic_sketch(256)
    gray = ImageLoader.to_grayscale(sketch)
    thresholder = SketchThresholder()
    binary = thresholder.binarize(gray)
    
    normalizer = SketchNormalizer(target_size=512, padding_ratio=0.12)
    rgb, rgba, mask = normalizer.normalize(sketch, binary)
    assert rgb.shape == (512, 512, 3)
    assert rgba.shape == (512, 512, 4)
    assert mask.shape == (512, 512)
    assert np.count_nonzero(mask > 127) > 0


def test_full_pipeline_execution():
    sketch = create_synthetic_sketch(256)
    pipeline = SketchPreprocessingPipeline(target_size=512)
    variants, report = pipeline.process(sketch, return_base64=False)

    # Verify all 9 output image variants
    expected_variants = [
        "original_image", "enhanced_image", "denoised_image",
        "binary_image", "edge_image", "contour_visualization",
        "skeleton_image", "foreground_mask", "final_reconstruction_input"
    ]
    for name in expected_variants:
        assert name in variants, f"Missing output variant: {name}"
        assert variants[name] is not None
        assert isinstance(variants[name], np.ndarray)

    assert variants["final_reconstruction_input"].shape == (512, 512, 3)
    assert variants["foreground_mask"].shape == (512, 512)

    # Verify structured report
    assert isinstance(report, PreprocessingReport)
    d = report.to_dict()
    assert d["image_dimensions"]["width"] == 256
    assert d["image_dimensions"]["height"] == 256
    assert d["foreground_occupancy"] > 0.0
    assert d["contour_count"] >= 1
    assert d["stroke_analysis"]["average_width_estimate"] > 0.0
    assert "symmetry" in d
    assert "shape_analysis" in d

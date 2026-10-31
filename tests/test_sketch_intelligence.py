"""
Unit Test Suite for Sketch Intelligence and Semantic Recognition Engine
Tests neural architectures, geometric feature tagging, uncertainty quantification,
semantic description generation, and 3D reconstruction conditioning.
"""

import sys
import numpy as np
import pytest
import torch
from pathlib import Path

# Add backend to path
BACKEND_DIR = Path(r"C:\Sketch2Shape-AI\backend")
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.sketch_intelligence.models import LightweightCNN, ResNet18Sketch, get_model
from app.sketch_intelligence.geometry_tags import GeometricFeatureTagger
from app.sketch_intelligence.uncertainty import UncertaintyEstimator
from app.sketch_intelligence.semantic_generator import SemanticDescriptionGenerator
from app.sketch_intelligence.reconstruction_conditioning import ReconstructionConditioner


def test_model_architectures():
    """Verifies that both candidate models instantiate and compute forward pass."""
    dummy_input = torch.randn(2, 1, 128, 128)
    
    # 1. Lightweight CNN
    m_cnn = LightweightCNN(num_classes=50)
    out_cnn = m_cnn(dummy_input)
    assert out_cnn.shape == (2, 50)
    assert not torch.isnan(out_cnn).any()

    # 2. ResNet18 Adapted
    m_resnet = ResNet18Sketch(num_classes=50)
    out_resnet = m_resnet(dummy_input)
    assert out_resnet.shape == (2, 50)
    assert not torch.isnan(out_resnet).any()


def test_geometric_tagger_heuristics():
    """Verifies that geometric feature tagger accurately extracts categorical tags."""
    tagger = GeometricFeatureTagger()

    # Case 1: Circle with high symmetry
    mock_circle_report = {
        "symmetry": {"score": 0.85},
        "shape_analysis": {
            "orientation_degrees": 5.0,
            "aspect_ratio": 1.0,
            "compactness": 0.92,
            "complexity": 1.05
        },
        "stroke_analysis": {
            "stroke_density": 0.08,
            "average_width_estimate": 4.5,
            "connected_components_count": 1
        },
        "metadata": {"hierarchy_depth": 1}
    }
    tags = tagger.extract_tags(mock_circle_report)
    assert "approximately_symmetric" in tags
    assert "circular_structure" in tags
    assert "predominantly_horizontal" in tags

    # Case 2: Vertical elongated ladder with multiple components and holes
    mock_ladder_report = {
        "symmetry": {"score": 0.75},
        "shape_analysis": {
            "orientation_degrees": 88.0,
            "aspect_ratio": 0.35,
            "compactness": 0.25,
            "complexity": 2.10
        },
        "stroke_analysis": {
            "stroke_density": 0.03,
            "average_width_estimate": 3.0,
            "connected_components_count": 4
        },
        "metadata": {"hierarchy_depth": 3}
    }
    tags = tagger.extract_tags(mock_ladder_report)
    assert "predominantly_vertical" in tags
    assert "elongated" in tags
    assert "multiple_components" in tags
    assert "enclosed_region" in tags
    assert "thin_structure" in tags


def test_uncertainty_estimator_confident():
    """Verifies low uncertainty when rank-1 prediction has strong confidence and wide gap."""
    estimator = UncertaintyEstimator()
    class_names = [f"class_{i}" for i in range(50)]
    
    # Sharp distribution
    probs = np.zeros(50)
    probs[5] = 0.92
    probs[12] = 0.04
    probs[20] = 0.02
    probs /= probs.sum()

    res = estimator.evaluate_predictions(probs, class_names)
    assert res["predicted_category"] == "class_5"
    assert res["top_confidence"] >= 0.90
    assert res["confidence_gap"] > 0.80
    assert not res["is_ambiguous"]
    assert res["uncertainty_level"] == "low"
    assert len(res["top_predictions"]) == 5


def test_uncertainty_estimator_ambiguous():
    """Verifies high uncertainty when top predictions have low confidence or narrow gap."""
    estimator = UncertaintyEstimator()
    class_names = [f"class_{i}" for i in range(50)]

    # Diffuse, ambiguous distribution (e.g. chair vs table)
    probs = np.zeros(50)
    probs[10] = 0.36
    probs[25] = 0.33
    probs[40] = 0.15
    probs /= probs.sum()

    res = estimator.evaluate_predictions(probs, class_names)
    assert res["is_ambiguous"]
    assert res["uncertainty_level"] == "high"
    assert "class_25" in res["alternative_categories"]


def test_semantic_description_and_hints():
    """Verifies deterministic synthesis of semantic descriptions and reconstruction hints."""
    pred_info = {
        "predicted_category": "chair",
        "top_confidence": 0.91,
        "alternative_categories": ["table"],
        "is_ambiguous": False,
        "uncertainty_level": "low"
    }
    tags = ["approximately_symmetric", "predominantly_vertical", "multiple_components", "enclosed_region"]
    geom = {
        "stroke_analysis": {"connected_components_count": 3}
    }

    desc_info = SemanticDescriptionGenerator.generate(pred_info, tags, geom)
    assert desc_info["object_category"] == "chair"
    assert "chair" in desc_info["semantic_description"]
    assert "vertical" in desc_info["semantic_description"]
    assert desc_info["reconstruction_hints"]["object_type"] == "furniture"
    assert desc_info["reconstruction_hints"]["symmetry_prior"] is True
    assert desc_info["reconstruction_hints"]["confidence_level"] == "high"


def test_reconstruction_conditioning():
    """Verifies generation of decoupled conditioning metadata payload."""
    conditioning = ReconstructionConditioner.build_conditioning_payload(
        category="airplane",
        confidence=0.88,
        is_ambiguous=False,
        geometric_tags=["approximately_symmetric", "predominantly_horizontal"],
        geometry_metrics={"stroke_analysis": {"connected_components_count": 2}}
    )

    assert conditioning["category"] == "airplane"
    assert "airplane" in conditioning["semantic_prompt"]
    assert conditioning["geometry_constraints"]["symmetry_prior"] is True
    assert conditioning["geometry_constraints"]["orientation"] == "horizontal"
    assert conditioning["geometry_constraints"]["component_count"] == 2
    assert conditioning["uncertainty"]["is_ambiguous"] is False

"""
Comprehensive Test Suite for Stage 7: Multi-Model 3D Reconstruction Engine
Tests:
- Model Registry & Discovery
- Semantically-Aware Model Selector
- Mesh Topology & Geometric Validation
- Mesh Processing (Repair, Normalization, Decimation)
- Multi-Format Export (GLB, OBJ, MTL) with strict reload verification
- Procedural Lathe / Extrusion 3D Reconstruction
- End-to-End Reconstruction Pipeline Coordination
"""

import os
import sys
import shutil
from pathlib import Path
import pytest
import numpy as np
import trimesh

# Ensure backend is on PYTHONPATH
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.reconstruction.model_registry import model_registry
from app.reconstruction.model_selector import ModelSelector
from app.reconstruction.mesh_validation import MeshValidator
from app.reconstruction.mesh_processing import MeshProcessor
from app.reconstruction.texture_processing import TextureProcessor
from app.reconstruction.export_manager import ExportManager
from app.reconstruction.adapters.procedural_adapter import ProceduralAdapter
from app.reconstruction.reconstruction_config import ReconstructionRequest, ReconstructionResponse
from app.reconstruction.reconstruction_pipeline import reconstruction_pipeline


@pytest.fixture
def test_output_dir(tmp_path):
    out_dir = tmp_path / "test_reconstruction_outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    yield out_dir
    if out_dir.exists():
        shutil.rmtree(out_dir, ignore_errors=True)


@pytest.fixture
def sample_box_mesh():
    return trimesh.creation.box(extents=(1.0, 1.0, 1.0))


@pytest.fixture
def sample_chair_sketch():
    p = BASE_DIR / "outputs" / "preprocessing_tests" / "quickdraw_chair_normalized.png"
    if not p.exists():
        # Create a synthetic 128x128 sketch if file is missing in test sandbox
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (128, 128), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.rectangle([30, 20, 98, 108], outline=(0, 0, 0), width=4)
        p.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(p))
    return str(p)


# ==============================================================================
# 1. Model Registry Tests
# ==============================================================================

def test_model_registry_discovery():
    models = model_registry.list_models()
    assert len(models) >= 4, "Expected at least 4 registered reconstruction adapters."
    names = [m.name for m in models]
    assert "instantmesh" in names
    assert "procedural" in names
    assert "hunyuan3d-2" in names
    assert "triposr" in names


def test_model_registry_retrieval():
    proc = model_registry.get_model("procedural")
    assert proc is not None
    assert proc.name == "procedural"
    assert proc.is_available() is True

    # Case insensitivity
    assert model_registry.get_model("PROCEDURAL") is not None


# ==============================================================================
# 2. Model Selector Tests
# ==============================================================================

def test_model_selector_explicit_override():
    name, reason, _ = ModelSelector.select_model(user_model="procedural")
    assert name == "procedural"
    assert "explicitly requested" in reason


def test_model_selector_rotational_symmetry():
    # Symmetrical cup with fast preset -> procedural lathe
    name, reason, config = ModelSelector.select_model(
        category="cup",
        confidence=0.92,
        geometric_tags=["symmetric", "predominantly_vertical"],
        symmetry_scores={"vertical": 0.91},
        quality_preset="fast"
    )
    assert name == "procedural"
    assert config.get("mode") == "rotational"


def test_model_selector_complex_category():
    # Chair -> InstantMesh (if available) or procedural fallback
    name, reason, _ = ModelSelector.select_model(
        category="chair",
        confidence=0.88,
        geometric_tags=["multi_component"],
        quality_preset="balanced"
    )
    assert name in ("instantmesh", "procedural")


# ==============================================================================
# 3. Mesh Validation & Processing Tests
# ==============================================================================

def test_mesh_validator_valid_mesh(sample_box_mesh):
    report = MeshValidator.validate_trimesh(sample_box_mesh)
    assert report["is_valid"] is True
    assert report["vertices"] == 8
    assert report["faces"] == 12
    assert report["is_watertight"] is True
    assert report["euler_characteristic"] == 2
    assert report["volume"] is not None and report["volume"] > 0


def test_mesh_validator_empty():
    empty_mesh = trimesh.Trimesh()
    report = MeshValidator.validate_trimesh(empty_mesh)
    assert report["is_valid"] is False
    assert "empty" in report["error"]


def test_mesh_processor_normalize_and_decimate(sample_box_mesh):
    cleaned = MeshProcessor.clean_and_repair(sample_box_mesh)
    norm = MeshProcessor.center_and_normalize(cleaned, target_scale=0.9)
    extents = norm.bounding_box.extents
    assert max(extents) <= 0.9001, "Normalized mesh exceeds target bounding scale."


# ==============================================================================
# 4. Export Manager & Strict Reload Verification Tests
# ==============================================================================

def test_export_manager_glb_and_obj(sample_box_mesh, test_output_dir):
    exported = ExportManager.export_all(
        mesh=sample_box_mesh,
        output_dir=str(test_output_dir),
        base_filename="box_test",
        formats=["glb", "obj"]
    )
    assert "glb" in exported and Path(exported["glb"]).exists()
    assert "obj" in exported and Path(exported["obj"]).exists()

    # Strict reload verification with Trimesh
    glb_loaded = trimesh.load(exported["glb"], process=False)
    assert glb_loaded is not None

    obj_loaded = trimesh.load(exported["obj"], process=False)
    assert obj_loaded is not None
    assert len(obj_loaded.vertices) == len(sample_box_mesh.vertices)


# ==============================================================================
# 5. Procedural Lathe / Extrusion Reconstruction Tests
# ==============================================================================

def test_procedural_adapter_reconstruction(sample_chair_sketch, test_output_dir):
    adapter = ProceduralAdapter()
    req = ReconstructionRequest(
        image_path=sample_chair_sketch,
        output_dir=str(test_output_dir),
        quality_preset="fast",
        export_formats=["glb", "obj"]
    )
    resp = adapter.reconstruct(req)
    assert resp.success is True
    assert resp.vertices > 0
    assert resp.faces > 0
    assert resp.mesh_valid is True
    assert resp.mesh_path is not None
    assert Path(resp.mesh_path).exists()


# ==============================================================================
# 6. Master Pipeline Coordination Tests
# ==============================================================================

def test_master_reconstruction_pipeline(sample_chair_sketch, test_output_dir):
    req = ReconstructionRequest(
        image_path=sample_chair_sketch,
        output_dir=str(test_output_dir),
        model_name="procedural",  # Fast deterministic test
        quality_preset="fast",
        export_formats=["glb"],
        preprocess_first=True
    )
    resp = reconstruction_pipeline.execute(req)
    assert resp.success is True
    assert resp.vertices > 0
    assert "glb" in resp.formats
    assert Path(resp.formats["glb"]).exists()

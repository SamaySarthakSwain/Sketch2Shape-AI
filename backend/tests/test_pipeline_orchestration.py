"""
Unit and Integration Tests for Production Pipeline Orchestration
Tests input validation, stage progression, adaptive selection, procedural templates,
quality fallback, async job management, and cancellation.
"""

import os
import sys
import time
import base64
from pathlib import Path
import pytest
import numpy as np
from PIL import Image
import trimesh

from app.orchestration import (
    PipelineOrchestrator,
    PipelineConfig,
    PipelineJob,
    PipelineStage,
    StageExecutor,
    ExecutionLogger,
    PipelineException,
    job_manager
)
from app.reconstruction.category_templates import CategoryGeometryTemplates
from app.reconstruction.reconstruction_config import ReconstructionRequest
from app.reconstruction.adapters.procedural_adapter import ProceduralAdapter


@pytest.fixture
def sample_sketch_path(tmp_path):
    """Generates a simple synthetic sketch file."""
    img_path = tmp_path / "test_chair_sketch.png"
    arr = np.ones((128, 128), dtype=np.uint8) * 255
    # Draw simple chair back and seat
    arr[20:100, 30:35] = 0
    arr[60:65, 30:90] = 0
    arr[60:100, 85:90] = 0
    Image.fromarray(arr).save(str(img_path))
    return str(img_path)


@pytest.fixture
def sample_sketch_b64(sample_sketch_path):
    with open(sample_sketch_path, "rb") as f:
        data = f.read()
    return f"data:image/png;base64,{base64.b64encode(data).decode('utf-8')}"


# ==============================================================================
# 1. INPUT VALIDATION & ERROR HANDLING TESTS
# ==============================================================================

def test_input_validation_valid_file(sample_sketch_path, tmp_path):
    executor = StageExecutor()
    res = executor.validate_input(image_path=sample_sketch_path, image_b64=None, job_dir=tmp_path)
    assert res == sample_sketch_path
    assert Path(res).exists()


def test_input_validation_valid_b64(sample_sketch_b64, tmp_path):
    executor = StageExecutor()
    res = executor.validate_input(image_path=None, image_b64=sample_sketch_b64, job_dir=tmp_path)
    assert Path(res).exists()
    assert Path(res).name == "input_sketch.png"


def test_input_validation_missing_input(tmp_path):
    executor = StageExecutor()
    with pytest.raises(PipelineException) as exc:
        executor.validate_input(image_path=None, image_b64=None, job_dir=tmp_path)
    assert exc.value.stage == PipelineStage.VALIDATING_INPUT


def test_input_validation_corrupt_b64(tmp_path):
    executor = StageExecutor()
    with pytest.raises(PipelineException) as exc:
        executor.validate_input(image_path=None, image_b64="not_a_valid_base64_string!!!", job_dir=tmp_path)
    assert exc.value.stage == PipelineStage.VALIDATING_INPUT


# ==============================================================================
# 2. CATEGORY-AWARE PROCEDURAL GEOMETRY TESTS
# ==============================================================================

def test_category_geometry_templates_distinct():
    """Verify that each category generates tailored, distinct geometry rather than uniform 4802 verts."""
    chair = CategoryGeometryTemplates.generate_chair()
    car = CategoryGeometryTemplates.generate_car()
    airplane = CategoryGeometryTemplates.generate_airplane()
    cup = CategoryGeometryTemplates.generate_cup()
    apple = CategoryGeometryTemplates.generate_apple()
    bicycle = CategoryGeometryTemplates.generate_bicycle()
    table = CategoryGeometryTemplates.generate_table()

    # Verify vertex count diversity
    counts = {
        "chair": len(chair.vertices),
        "car": len(car.vertices),
        "airplane": len(airplane.vertices),
        "cup": len(cup.vertices),
        "apple": len(apple.vertices),
        "bicycle": len(bicycle.vertices),
        "table": len(table.vertices)
    }

    # Verify not all equal
    unique_counts = set(counts.values())
    assert len(unique_counts) >= 4, f"Template vertex counts must be diverse: {counts}"

    # Verify all meshes are non-empty and have finite vertices
    for name, m in [("chair", chair), ("car", car), ("airplane", airplane), ("cup", cup), ("apple", apple), ("bicycle", bicycle), ("table", table)]:
        assert not m.is_empty, f"{name} mesh is empty"
        assert np.isfinite(m.vertices).all(), f"{name} vertices contain NaN/Inf"
        assert len(m.faces) > 0, f"{name} faces are empty"


def test_category_rejection_unsupported():
    """Verify clean rejection of unsupported categories."""
    assert not CategoryGeometryTemplates.is_category_supported("cat")
    assert not CategoryGeometryTemplates.is_category_supported("elephant")
    with pytest.raises(ValueError):
        CategoryGeometryTemplates.dispatch_category_template("cat")


# ==============================================================================
# 3. ADAPTIVE MODEL SELECTION TESTS
# ==============================================================================

def test_adaptive_selection_user_preference():
    executor = StageExecutor()
    model, reason = executor.select_reconstruction_model(
        user_preference="procedural",
        category="chair",
        confidence=0.9,
        geometric_tags=["furniture"],
        quality_preset="balanced"
    )
    assert model == "procedural"
    assert "User explicitly selected" in reason


def test_adaptive_selection_fast_preset():
    executor = StageExecutor()
    model, reason = executor.select_reconstruction_model(
        user_preference="auto",
        category="chair",
        confidence=0.9,
        geometric_tags=["furniture"],
        quality_preset="fast"
    )
    # Fast preset routes to procedural template for instant latency
    assert model == "procedural"
    assert "Fast preset" in reason or "routed to dedicated" in reason



# ==============================================================================
# 4. END-TO-END PIPELINE ORCHESTRATION TEST (SYNCHRONOUS)
# ==============================================================================

def test_pipeline_orchestration_sync_procedural(sample_sketch_path, tmp_path):
    orchestrator = PipelineOrchestrator(base_output_dir=str(tmp_path / "jobs"))
    config = PipelineConfig(
        image_path=sample_sketch_path,
        preferred_model="procedural",
        quality_preset="fast",
        preprocess_first=True,
        auto_refine=True,
        refine_preset="fast",
        export_formats=["glb", "obj"],
        category_override="chair"
    )

    job = orchestrator.run_pipeline(config=config, job_id="test_sync_job")

    assert job.status == "completed"
    assert job.current_stage == PipelineStage.COMPLETED
    assert job.total_duration_seconds > 0

    # Verify stage history includes all core stages
    stage_names = [s.stage for s in job.stage_history]
    assert PipelineStage.VALIDATING_INPUT in stage_names
    assert PipelineStage.OPENCV_PREPROCESSING in stage_names
    assert PipelineStage.SKETCH_INTELLIGENCE in stage_names
    assert PipelineStage.MODEL_SELECTION in stage_names
    assert PipelineStage.RECONSTRUCTING_3D in stage_names
    assert PipelineStage.MESH_VALIDATION in stage_names
    assert PipelineStage.GEOMETRY_ANALYSIS in stage_names
    assert PipelineStage.MESH_REFINEMENT in stage_names
    assert PipelineStage.EXPORTING_ASSETS in stage_names

    # Verify physical mesh reload
    final_mesh = job.artifacts.get("final_mesh")
    assert final_mesh is not None
    assert Path(final_mesh).exists()
    loaded = trimesh.load(final_mesh, force="mesh")
    assert not loaded.is_empty
    assert len(loaded.vertices) > 0


# ==============================================================================
# 5. ASYNC JOB MANAGER & CANCELLATION TESTS
# ==============================================================================

def test_job_manager_submission_and_tracking(sample_sketch_path):
    config = PipelineConfig(
        image_path=sample_sketch_path,
        preferred_model="procedural",
        quality_preset="fast",
        category_override="cup"
    )
    job = job_manager.submit_job(config)
    assert job.job_id.startswith("job_")
    assert job.status in ["queued", "processing", "completed"]

    # Poll until completed (procedural takes ~1s)
    max_wait = 15
    start = time.time()
    while time.time() - start < max_wait:
        current = job_manager.get_job(job.job_id)
        if current.status in ["completed", "failed"]:
            break
        time.sleep(0.5)

    final_job = job_manager.get_job(job.job_id)
    assert final_job.status == "completed"
    assert final_job.metrics.get("predicted_category") == "cup"


def test_job_manager_cancellation():
    # Submit job and immediately cancel
    config = PipelineConfig(
        image_path="non_existent_file.png",
        preferred_model="procedural"
    )
    job = job_manager.submit_job(config)
    cancelled = job_manager.cancel_job(job.job_id)
    assert cancelled is True

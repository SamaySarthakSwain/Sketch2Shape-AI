import numpy as np
import cv2
import pytest
import trimesh
from app.reconstruction.procedural_engine import ProceduralReconstructionEngine

@pytest.fixture
def engine():
    return ProceduralReconstructionEngine()

@pytest.fixture
def sample_profile_mask():
    mask = np.zeros((256, 256), dtype=np.uint8)
    # Draw cylinder / vase silhouette
    cv2.circle(mask, (128, 128), 60, 255, -1)
    return mask

def test_surface_of_revolution(engine, sample_profile_mask):
    mesh = engine.reconstruct_surface_of_revolution(sample_profile_mask, num_slices=40, num_angles=24)
    assert isinstance(mesh, trimesh.Trimesh)
    assert len(mesh.vertices) > 0
    assert len(mesh.faces) > 0
    assert mesh.is_watertight

def test_bilateral_extrusion(engine, sample_profile_mask):
    depth = sample_profile_mask.copy()
    mesh = engine.reconstruct_bilateral_extrusion(sample_profile_mask, depth, grid_res=32)
    assert isinstance(mesh, trimesh.Trimesh)
    assert len(mesh.vertices) > 0
    assert len(mesh.faces) > 0

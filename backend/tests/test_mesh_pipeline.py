import trimesh
import pytest
from pathlib import Path
from app.mesh.validator import MeshValidator
from app.mesh.exporter import MeshExporter

@pytest.fixture
def sample_sphere_mesh():
    return trimesh.creation.icosphere(subdivisions=2, radius=1.0)

def test_mesh_validation(sample_sphere_mesh):
    validator = MeshValidator()
    report = validator.validate(sample_sphere_mesh)
    
    assert report["is_watertight"] is True
    assert report["is_winding_consistent"] is True
    assert report["euler_characteristic"] == 2 # sphere is Euler characteristic 2
    assert report["health_score"] >= 90
    assert report["is_valid_for_3d_print"] is True

def test_mesh_repair_and_normalize(sample_sphere_mesh):
    validator = MeshValidator(target_faces=100)
    repaired, report = validator.repair_and_normalize(sample_sphere_mesh)
    
    assert isinstance(repaired, trimesh.Trimesh)
    assert len(repaired.faces) <= 200
    # Center should be near 0, 0, 0
    assert abs(repaired.centroid[0]) < 1e-2

def test_mesh_export_formats(tmp_path, sample_sphere_mesh):
    # Test bytes export
    for fmt in ["glb", "obj", "stl", "ply"]:
        raw = MeshExporter.export_bytes(sample_sphere_mesh, format=fmt)
        assert len(raw) > 0
        if fmt == "glb":
            # GLB magic bytes: 0x46546C67 ("glTF")
            assert raw[:4] == b"glTF"
        elif fmt == "stl":
            assert len(raw) > 80

    # Test file export
    paths = MeshExporter.export_all_formats(sample_sphere_mesh, tmp_path, "test_model")
    assert len(paths) == 4
    for fmt, p in paths.items():
        assert Path(p).exists()
        assert Path(p).stat().st_size > 0

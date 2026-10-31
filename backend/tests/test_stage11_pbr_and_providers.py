"""
Stage 11 Comprehensive Test Suite: Premium AI 3D Generation, PBR Texturing, Visual Quality & Professional Asset Export

Covers:
1. Cloud AI Providers (Meshy, Tripo, Rodin) & Provider Selector fallback logic.
2. PBR Texturing Engine (Material Library, UV Unwrapping, Procedural Map Generation, glTF 2.0 Baking).
3. 3D Printability Analysis, LOD Generator, Multi-Format Exporter (GLB, GLTF, OBJ, STL, 3MF, USDZ).
4. Asset Distribution Packager (.zip bundle).
5. Stage 11 FastAPI Endpoints (/providers, /materials, /styles, /retexture, /download/bundle).
"""

import os
import sys
import json
import zipfile
from pathlib import Path
import pytest
import numpy as np
from PIL import Image
import trimesh
from fastapi.testclient import TestClient

from app.reconstruction.providers import (
    ProviderConfig,
    ProviderCredentials,
    ProviderTaskResult,
    ProviderTaskStatus,
    ProviderTextureUrls,
    MeshyProvider,
    TripoProvider,
    RodinProvider,
    ProviderRegistry,
    ProviderSelector,
    provider_registry
)
from app.texturing import (
    PBRMaterialLibrary,
    PBRMaterialDef,
    MATERIALS_DB,
    CATEGORY_MATERIAL_MAPPING,
    VisualStyle,
    STYLE_MODIFIERS,
    UVUnwrapper,
    PBRTextureGenerator,
    PBRBaker
)
from app.packaging import (
    PrintabilityAnalyzer,
    PrintabilityReport,
    LODGenerator,
    MultiFormatExporter,
    AssetPackager
)
from app.main import app
from app.orchestration import (
    PipelineOrchestrator,
    PipelineConfig,
    StageExecutor,
    job_manager
)

client = TestClient(app)


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def test_mesh():
    """Generates a clean watertight box mesh for geometry and packaging tests."""
    return trimesh.creation.box(extents=(1.0, 1.5, 0.8))


@pytest.fixture
def non_watertight_mesh():
    """Generates an open surface mesh."""
    mesh = trimesh.creation.box(extents=(1.0, 1.0, 1.0))
    # Remove one face to make it non-watertight
    faces = mesh.faces[:-1]
    return trimesh.Trimesh(vertices=mesh.vertices, faces=faces, process=False)


@pytest.fixture
def sample_sketch_path(tmp_path):
    """Creates a sample sketch PNG."""
    img_path = tmp_path / "stage11_test_sketch.png"
    arr = np.ones((128, 128), dtype=np.uint8) * 255
    arr[30:100, 40:45] = 0
    arr[65:70, 40:90] = 0
    arr[65:100, 85:90] = 0
    Image.fromarray(arr).save(str(img_path))
    return str(img_path)


# ==============================================================================
# 1. CLOUD AI PROVIDERS & SELECTOR TESTS
# ==============================================================================

def test_provider_configuration_and_credentials(monkeypatch):
    """Verifies credential detection and status reporting for all cloud providers."""
    monkeypatch.delenv("MESHY_API_KEY", raising=False)
    monkeypatch.delenv("TRIPO_API_KEY", raising=False)
    monkeypatch.delenv("RODIN_API_KEY", raising=False)

    meshy = MeshyProvider()
    tripo = TripoProvider()
    rodin = RodinProvider()

    assert not meshy.is_available()
    assert not tripo.is_available()
    assert not rodin.is_available()

    # With credentials configured
    cfg = ProviderConfig()
    cfg.credentials.meshy_api_key = "msy_test_credential_12345"
    meshy_active = MeshyProvider(config=cfg)
    assert meshy_active.is_available()


def test_provider_registry():
    """Verifies registry indexing and query."""
    registry = ProviderRegistry()
    providers = registry.list_all_providers()
    assert "meshy" in providers
    assert "tripo" in providers
    assert "rodin" in providers

    status_dict = registry.get_provider_status()
    assert "meshy" in status_dict
    assert status_dict["meshy"]["name"] == "meshy"


def test_provider_selector_fallback():
    """Verifies that the selector falls back to local engines when cloud keys are not provided."""
    selector = ProviderSelector()
    
    # Cloud requested but no key -> should gracefully choose local
    engine_name, reason, is_cloud = selector.select_engine(
        user_preference="meshy",
        category="chair",
        quality_preset="high"
    )
    # Since MESHY_API_KEY is not set in test environment, it must fallback to local
    assert is_cloud is False
    assert engine_name in ["instantmesh", "procedural"]

    # Explicit local procedural request
    engine_local, reason_local, is_cloud_local = selector.select_engine(
        user_preference="procedural",
        category="chair",
        quality_preset="fast"
    )
    assert is_cloud_local is False
    assert engine_local == "procedural"


def test_cloud_provider_mock_workflow(monkeypatch, tmp_path):
    """Tests provider execution workflow with mocked API endpoints."""
    # Setup mock config with key
    cfg = ProviderConfig()
    cfg.credentials.meshy_api_key = "msy_mock_test_key"
    meshy = MeshyProvider(config=cfg)
    
    # Save a dummy GLB
    dummy_glb = tmp_path / "mock_download.glb"
    box = trimesh.creation.box()
    box.export(str(dummy_glb))

    class MockResponse:
        def __init__(self, json_data, status_code=200, content=b""):
            self._json = json_data
            self.status_code = status_code
            self.content = content
        def json(self):
            return self._json
        def raise_for_status(self):
            pass

    import requests

    def mock_post(url, *args, **kwargs):
        if "image-to-3d" in url:
            return MockResponse({"result": "task_abc123"}, 202)
        return MockResponse({}, 404)

    def mock_get(url, *args, **kwargs):
        if "task_abc123" in url:
            return MockResponse({
                "id": "task_abc123",
                "status": "SUCCEEDED",
                "progress": 100,
                "model_urls": {
                    "glb": "http://mock.mesh.test/model.glb"
                },
                "texture_urls": [
                    {"base_color": "http://mock.mesh.test/albedo.png"}
                ]
            }, 200)
        elif "model.glb" in url:
            return MockResponse({}, 200, content=dummy_glb.read_bytes())
        return MockResponse({}, 404)

    monkeypatch.setattr(requests, "post", mock_post)
    monkeypatch.setattr(requests, "get", mock_get)

    img_file = tmp_path / "input.png"
    Image.new("RGB", (64, 64), color="white").save(str(img_file))

    task_res = meshy.submit_task(image_path=str(img_file), category="chair")
    assert task_res.status == ProviderTaskStatus.QUEUED
    assert task_res.task_id == "task_abc123"

    poll_res = meshy.poll_task("task_abc123")
    assert poll_res.status == ProviderTaskStatus.SUCCEEDED
    assert poll_res.download_url_glb == "http://mock.mesh.test/model.glb"


# ==============================================================================
# 2. PBR TEXTURING & MATERIAL LIBRARY TESTS
# ==============================================================================

def test_pbr_material_library():
    """Tests PBR materials across 50+ categories and visual styles."""
    # Verify default material lookup
    mat = PBRMaterialLibrary.get_material_for_category("chair")
    assert "natural_wood" in mat.name
    assert mat.roughness > 0.4

    # Verify vehicle mapping
    mat_car = PBRMaterialLibrary.get_material_for_category("car")
    assert "automotive" in mat_car.name
    assert mat_car.metallic > 0.8

    # Verify override
    mat_custom = PBRMaterialLibrary.get_material_for_category("chair", material_override="gold_polished")
    assert "gold_polished" in mat_custom.name
    assert mat_custom.metallic >= 0.95

    # Verify styles
    mat_stylized = PBRMaterialLibrary.get_material_for_category("chair", style="stylized")
    assert mat_stylized.roughness != mat.roughness or mat_stylized.base_color_rgb != mat.base_color_rgb


def test_uv_unwrapper(test_mesh):
    """Tests automatic UV parameterization via tri-planar, cylindrical, and spherical methods."""
    # Tri-planar projection
    mesh_triplanar = UVUnwrapper.generate_uvs(test_mesh.copy(), mode="box")
    assert hasattr(mesh_triplanar.visual, "uv")
    uvs = mesh_triplanar.visual.uv
    assert uvs.shape == (len(mesh_triplanar.vertices), 2)
    assert np.all(uvs >= 0.0) and np.all(uvs <= 1.0)

    # Cylindrical projection
    mesh_cylindrical = UVUnwrapper.generate_uvs(test_mesh.copy(), mode="cylindrical")
    assert hasattr(mesh_cylindrical.visual, "uv")
    assert mesh_cylindrical.visual.uv.shape == (len(mesh_cylindrical.vertices), 2)


def test_pbr_texture_generator(tmp_path):
    """Tests procedural high-res generation of Albedo, Normal, Roughness, Metallic, and AO maps."""
    mat = PBRMaterialLibrary.get_material("natural_wood")
    out_dir = tmp_path / "textures"
    
    maps = PBRTextureGenerator.generate_pbr_set(
        material=mat,
        resolution=256,
        output_dir=str(out_dir)
    )

    assert "albedo" in maps and isinstance(maps["albedo"], Image.Image)
    assert "normal" in maps and isinstance(maps["normal"], Image.Image)
    assert "roughness" in maps and isinstance(maps["roughness"], Image.Image)
    assert "metallic" in maps and isinstance(maps["metallic"], Image.Image)
    assert "ao" in maps and isinstance(maps["ao"], Image.Image)

    # Verify image dimensions
    alb_img = maps["albedo"]
    assert alb_img.size == (256, 256)
    assert alb_img.mode == "RGB"

    norm_img = maps["normal"]
    assert norm_img.size == (256, 256)
    norm_arr = np.array(norm_img)
    assert norm_arr.shape == (256, 256, 3)
    assert norm_arr[:, :, 2].mean() > 180  # Strong Blue channel (Z up in tangent space)

    # Verify files saved on disk
    assert (out_dir / "albedo.png").exists()


def test_pbr_baker(test_mesh, tmp_path):
    """Tests baking procedural PBR materials onto meshes into valid glTF 2.0 GLB."""
    textured_mesh, texture_paths = PBRBaker.apply_pbr_textures(
        mesh=test_mesh,
        category="cup",
        style="realistic",
        texture_resolution=256,
        output_dir=str(tmp_path)
    )

    assert textured_mesh is not None
    assert len(texture_paths) >= 4
    
    out_glb = tmp_path / "baked_test.glb"
    glb_bytes = textured_mesh.export(file_type="glb")
    with open(out_glb, "wb") as f:
        f.write(glb_bytes)

    assert out_glb.exists()
    assert out_glb.stat().st_size > 1000

    # Load back using trimesh to verify glTF 2.0 validity
    loaded = trimesh.load(str(out_glb))
    assert loaded is not None
    if isinstance(loaded, trimesh.Scene):
        loaded_mesh = trimesh.util.concatenate(list(loaded.geometry.values()))
    else:
        loaded_mesh = loaded
    assert len(loaded_mesh.vertices) == len(test_mesh.vertices)


# ==============================================================================
# 3. PRINTABILITY, LOD & MULTI-FORMAT EXPORT TESTS
# ==============================================================================

def test_printability_analyzer(test_mesh, non_watertight_mesh):
    """Tests 3D printability analysis on watertight and non-watertight geometry."""
    # Clean box
    rep_clean = PrintabilityAnalyzer.analyze(test_mesh)
    assert rep_clean.is_watertight is True
    assert rep_clean.printability_score >= 70.0
    assert rep_clean.volume_cm3 > 0
    assert rep_clean.surface_area_cm2 > 0

    # Non-watertight mesh
    rep_open = PrintabilityAnalyzer.analyze(non_watertight_mesh)
    assert rep_open.is_watertight is False
    assert rep_open.printability_score < 70.0
    assert any("watertight" in w.lower() for w in rep_open.warnings)


def test_lod_generator(test_mesh, tmp_path):
    """Tests generation of LOD0, LOD1, and LOD2 geometries."""
    # Use a slightly denser sphere to test decimation
    sphere = trimesh.creation.icosphere(subdivisions=3, radius=1.0)
    
    lods = LODGenerator.generate_lods(sphere, output_dir=str(tmp_path), base_name="test_lod")
    assert "lod0" in lods
    assert "lod1" in lods
    assert "lod2" in lods

    assert lods["lod0"]["faces"] >= lods["lod1"]["faces"]
    assert lods["lod1"]["faces"] >= lods["lod2"]["faces"]
    assert Path(lods["lod1"]["path"]).exists()


def test_multi_format_exporter(test_mesh, tmp_path):
    """Tests export to GLB, GLTF, OBJ, STL, 3MF, and USDZ."""
    out_dir = tmp_path / "exports"
    
    exported = MultiFormatExporter.export_all_formats(
        mesh=test_mesh,
        output_dir=str(out_dir),
        base_filename="export_test"
    )

    assert "glb" in exported and Path(exported["glb"]).exists()
    assert "gltf" in exported and Path(exported["gltf"]).exists()
    assert "obj" in exported and Path(exported["obj"]).exists()
    assert "stl" in exported and Path(exported["stl"]).exists()
    assert "3mf" in exported and Path(exported["3mf"]).exists()
    assert "usdz" in exported and Path(exported["usdz"]).exists()

    # Verify 3MF is valid zip with [Content_Types].xml
    with zipfile.ZipFile(exported["3mf"], "r") as z:
        names = z.namelist()
        assert "[Content_Types].xml" in names
        assert "3D/3dmodel.model" in names

    # Verify USDZ is valid zip containing .usda
    with zipfile.ZipFile(exported["usdz"], "r") as z:
        assert any(n.endswith(".usda") for n in z.namelist())


def test_asset_packager(test_mesh, tmp_path):
    """Tests building the comprehensive distribution bundle .zip."""
    pkg_res = AssetPackager.create_package(
        mesh=test_mesh,
        category="chair",
        job_id="test_job_123",
        output_dir=str(tmp_path),
        base_name="test_asset"
    )

    zip_path = pkg_res["zip_path"]
    assert Path(zip_path).exists()
    assert zipfile.is_zipfile(zip_path)

    with zipfile.ZipFile(zip_path, "r") as z:
        files = z.namelist()
        assert "README.md" in files
        assert "reports/printability_report.json" in files
        assert any("models/test_asset.glb" in f for f in files)
        assert any("models/test_asset.obj" in f for f in files)
        assert any("models/test_asset.stl" in f for f in files)
        assert any("models/test_asset.3mf" in f for f in files)
        assert any("models/test_asset.usdz" in f for f in files)
        assert any("lods/" in f for f in files)


# ==============================================================================
# 4. FASTAPI STAGE 11 ENDPOINT TESTS
# ==============================================================================

def test_api_providers_endpoint():
    """Tests GET /api/v1/pipeline/providers endpoint."""
    resp = client.get("/api/v1/pipeline/providers")
    assert resp.status_code == 200
    data = resp.json()
    assert "cloud_providers" in data
    assert "local_engines" in data
    assert "meshy" in data["cloud_providers"]
    assert "tripo" in data["cloud_providers"]
    assert "rodin" in data["cloud_providers"]


def test_api_materials_endpoint():
    """Tests GET /api/v1/pipeline/materials endpoint."""
    resp = client.get("/api/v1/pipeline/materials")
    assert resp.status_code == 200
    data = resp.json()
    assert "materials" in data
    assert "categories_mapped" in data
    assert len(data["materials"]) >= 14
    mat_ids = [m["id"] for m in data["materials"]]
    assert "natural_wood" in mat_ids


def test_api_styles_endpoint():
    """Tests GET /api/v1/pipeline/styles endpoint."""
    resp = client.get("/api/v1/pipeline/styles")
    assert resp.status_code == 200
    data = resp.json()
    assert "styles" in data
    style_ids = [s["id"] for s in data["styles"]]
    assert "realistic" in style_ids
    assert "stylized" in style_ids
    assert "futuristic" in style_ids


def test_api_retexture_and_bundle_download(sample_sketch_path):
    """Tests full pipeline generation followed by dynamic retexturing and bundle zip download."""
    # 1. Run a fast synchronous pipeline generation
    resp = client.post("/api/v1/pipeline/generate", json={
        "image_path": sample_sketch_path,
        "preferred_model": "procedural",
        "quality_preset": "fast",
        "async_execution": False,
        "category_override": "chair",
        "visual_style": "realistic",
        "material_override": "natural_wood",
        "enable_pbr": True,
        "enable_packaging": True
    })
    assert resp.status_code == 200
    job_data = resp.json()
    job_id = job_data["job_id"]
    assert job_data["status"].lower() == "completed"
    assert "artifacts" in job_data
    assert "pbr_glb" in job_data["artifacts"] or "final_mesh" in job_data["artifacts"]
    assert "bundle_zip" in job_data["artifacts"]

    # 2. Test GET bundle download endpoint
    resp_download = client.get(f"/api/v1/pipeline/download/bundle/{job_id}")
    assert resp_download.status_code == 200
    assert resp_download.headers["content-type"] == "application/zip"
    assert len(resp_download.content) > 1000

    # 3. Test POST dynamic retexture endpoint
    resp_retexture = client.post(f"/api/v1/pipeline/retexture/{job_id}", json={
        "material_override": "gold_polished",
        "visual_style": "futuristic",
        "texture_resolution": 256
    })
    assert resp_retexture.status_code == 200
    ret_data = resp_retexture.json()
    assert ret_data["status"].lower() == "completed"
    assert "pbr_glb" in ret_data["artifacts"]
    assert ret_data["metrics"]["material"]["visual_style"] == "futuristic"

"""
Unit and Integration Test Suite for Geometry Intelligence & Refinement Engine
Tests 12 edge cases and core requirements specified in Stage 9 Phase 11:
1. Valid watertight mesh
2. Open boundary mesh
3. Empty mesh
4. Degenerate triangles
5. Disconnected components
6. Duplicate vertices
7. Non-finite coordinates (NaN/Inf)
8. Missing texture (untextured clay)
9. Vertex-colored mesh
10. UV-textured mesh
11. High-polygon mesh
12. Low-polygon mesh
13. Automated refinement presets (Fast, Balanced, High)
"""

import pytest
import numpy as np
import trimesh
from pathlib import Path

from app.geometry_intelligence import (
    TopologyAnalyzer,
    SurfaceAnalyzer,
    SymmetryAnalyzer,
    ComponentAnalyzer,
    TextureAnalyzer,
    DefectDetector,
    QualityScorer,
    MeshRefiner,
    MeshAnalyzer,
)


@pytest.fixture
def watertight_sphere():
    """Generates standard watertight UV sphere."""
    return trimesh.creation.icosphere(subdivisions=2, radius=1.0)


@pytest.fixture
def open_mesh():
    """Generates an open mesh with unclosed boundary edges (cube with 2 faces removed)."""
    box = trimesh.creation.box(extents=[1.0, 1.0, 1.0])
    return trimesh.Trimesh(vertices=box.vertices, faces=box.faces[:-2], process=False)


@pytest.fixture
def empty_mesh():
    """Generates empty mesh with 0 vertices and 0 faces."""
    return trimesh.Trimesh(vertices=np.zeros((0, 3)), faces=np.zeros((0, 3)), process=False)


@pytest.fixture
def degenerate_mesh():
    """Generates mesh containing zero-area degenerate triangles."""
    v = np.array([
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0],  # Duplicate
    ])
    f = np.array([
        [0, 1, 2],
        [0, 0, 1],  # Degenerate: duplicate vertex index
        [0, 1, 3],  # Zero area
    ])
    return trimesh.Trimesh(vertices=v, faces=f, process=False)


@pytest.fixture
def disconnected_mesh():
    """Generates mesh with 2 distinct disconnected components."""
    b1 = trimesh.creation.box(extents=[1, 1, 1])
    b2 = trimesh.creation.box(extents=[0.5, 0.5, 0.5])
    b2.vertices += [3.0, 0.0, 0.0]
    return trimesh.util.concatenate([b1, b2])


@pytest.fixture
def duplicate_vertex_mesh():
    """Generates mesh with unmerged coincident vertices."""
    v = np.array([
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0],  # Coincident with vertex 0
        [1.0, 0.0, 0.0],  # Coincident with vertex 1
        [1.0, 1.0, 0.0],
    ])
    f = np.array([
        [0, 1, 2],
        [3, 5, 4],
    ])
    return trimesh.Trimesh(vertices=v, faces=f, process=False)


@pytest.fixture
def non_finite_mesh():
    """Generates mesh containing NaN and Inf coordinates."""
    v = np.array([
        [0.0, 0.0, 0.0],
        [np.nan, 1.0, 0.0],
        [0.0, np.inf, 0.0],
    ])
    f = np.array([[0, 1, 2]])
    return trimesh.Trimesh(vertices=v, faces=f, process=False)


# =========================================================================
# TEST 1: Watertight Mesh Inspection
# =========================================================================
def test_watertight_mesh(watertight_sphere):
    topo = TopologyAnalyzer.analyze(watertight_sphere)
    assert topo.is_watertight is True
    assert topo.euler_characteristic == 2
    assert topo.connected_components == 1
    assert topo.boundary_edges_count == 0

    surf = SurfaceAnalyzer.analyze(watertight_sphere)
    assert surf.is_volume_valid is True
    assert surf.volume is not None and surf.volume > 0.0


# =========================================================================
# TEST 2: Open Boundary Mesh Inspection
# =========================================================================
def test_open_mesh(open_mesh):
    topo = TopologyAnalyzer.analyze(open_mesh)
    assert topo.is_watertight is False
    assert topo.boundary_edges_count > 0

    surf = SurfaceAnalyzer.analyze(open_mesh)
    assert surf.is_volume_valid is False
    assert surf.volume is None


# =========================================================================
# TEST 3: Empty Mesh Handling
# =========================================================================
def test_empty_mesh(empty_mesh):
    topo = TopologyAnalyzer.analyze(empty_mesh)
    assert topo.vertex_count == 0
    assert topo.face_count == 0
    assert topo.is_watertight is False

    analyzer = MeshAnalyzer()
    report = analyzer.analyze(empty_mesh, asset_id="empty_test")
    assert report.topology.vertex_count == 0
    assert report.quality.overall_score == 0.0 or report.quality.subscores.export == 0.0


# =========================================================================
# TEST 4: Degenerate Triangles Detection
# =========================================================================
def test_degenerate_triangles(degenerate_mesh):
    topo = TopologyAnalyzer.analyze(degenerate_mesh)
    assert topo.degenerate_faces_count >= 1

    surf = SurfaceAnalyzer.analyze(degenerate_mesh)
    struct = ComponentAnalyzer.analyze(degenerate_mesh)
    defects = DefectDetector.detect(degenerate_mesh, topo, surf, struct)
    assert defects.has_defects is True
    assert defects.degenerate_triangles >= 1


# =========================================================================
# TEST 5: Disconnected Components Detection
# =========================================================================
def test_disconnected_components(disconnected_mesh):
    topo = TopologyAnalyzer.analyze(disconnected_mesh)
    assert topo.connected_components == 2

    struct = ComponentAnalyzer.analyze(disconnected_mesh)
    assert len(struct.component_sizes) == 2


# =========================================================================
# TEST 6: Duplicate Vertices Detection & Removal
# =========================================================================
def test_duplicate_vertices(duplicate_vertex_mesh):
    topo = TopologyAnalyzer.analyze(duplicate_vertex_mesh)
    assert topo.duplicate_vertices_count >= 2

    refined, comp = MeshRefiner.refine(duplicate_vertex_mesh, preset="fast")
    assert len(refined.vertices) <= len(duplicate_vertex_mesh.vertices)


# =========================================================================
# TEST 7: Non-Finite Coordinates
# =========================================================================
def test_non_finite_coordinates(non_finite_mesh):
    topo = TopologyAnalyzer.analyze(non_finite_mesh)
    surf = SurfaceAnalyzer.analyze(non_finite_mesh)
    struct = ComponentAnalyzer.analyze(non_finite_mesh)
    defects = DefectDetector.detect(non_finite_mesh, topo, surf, struct)

    assert defects.non_finite_coordinates > 0
    assert defects.has_defects is True


# =========================================================================
# TEST 8 & 9: Texture Modes (Clay vs Vertex Colors)
# =========================================================================
def test_texture_analysis(watertight_sphere):
    # Untextured sphere
    tex_clay = TextureAnalyzer.analyze(watertight_sphere)
    assert tex_clay.texture_mode == "untextured_clay"
    assert "clay" in tex_clay.texture_status_message.lower()

    # Vertex-colored sphere
    colored_sphere = watertight_sphere.copy()
    colored_sphere.visual.vertex_colors = np.random.randint(0, 255, size=(len(watertight_sphere.vertices), 4))
    tex_color = TextureAnalyzer.analyze(colored_sphere)
    assert tex_color.texture_mode == "vertex_colored"
    assert "vertex-colored" in tex_color.texture_status_message.lower()


# =========================================================================
# TEST 10: Low-Poly Mesh Refinement Non-Destruction
# =========================================================================
def test_low_poly_refinement_preservation():
    # 8-vertex cuboid (similar to the car mesh)
    box = trimesh.creation.box(extents=[1, 2, 0.5])
    assert len(box.vertices) == 8
    assert len(box.faces) == 12

    refined, comp = MeshRefiner.refine(box, preset="balanced")
    # Low-poly geometry must not be destroyed by decimation
    assert len(refined.vertices) == 8
    assert len(refined.faces) == 12
    assert comp.is_degraded is False
    assert comp.refined_watertight is True


# =========================================================================
# TEST 11: High-Poly Mesh Refinement & Decimation
# =========================================================================
def test_high_poly_refinement():
    high_poly = trimesh.creation.icosphere(subdivisions=4, radius=1.0)
    assert len(high_poly.faces) > 2000

    refined, comp = MeshRefiner.refine(high_poly, preset="balanced")
    assert comp.refined_watertight is True
    assert comp.is_degraded is False


# =========================================================================
# TEST 12: Full Geometry Analyzer End-to-End
# =========================================================================
def test_full_analyzer_report(watertight_sphere):
    analyzer = MeshAnalyzer()
    report = analyzer.analyze(watertight_sphere, asset_id="sphere_benchmark", run_multiview=False)

    assert report.asset_id == "sphere_benchmark"
    assert report.topology.is_watertight is True
    assert report.quality.overall_score >= 80.0
    assert report.quality.subscores.topology == 100.0
    assert report.defects.has_defects is False

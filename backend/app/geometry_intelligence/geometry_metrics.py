"""
Geometry Intelligence Data Models & Metrics Schema
Defines strictly typed structures for 3D topology, geometry, surface properties,
multi-view consistency, defect detection, and transparent quality scoring.
"""

from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field


class TopologyMetrics(BaseModel):
    vertex_count: int
    face_count: int
    edge_count: int
    is_watertight: bool
    is_volume: bool
    euler_characteristic: int
    connected_components: int
    boundary_edges_count: int
    non_manifold_edges_count: int
    duplicate_vertices_count: int
    degenerate_faces_count: int
    is_manifold: bool


class SurfaceMetrics(BaseModel):
    surface_area: float
    volume: Optional[float] = None
    is_volume_valid: bool
    normal_consistency: bool
    inverted_normals_count: int
    mean_curvature_estimate: float
    gaussian_curvature_estimate: float
    surface_roughness_std: float


class SpatialMetrics(BaseModel):
    bounding_box_min: List[float]
    bounding_box_max: List[float]
    dimensions_xyz: List[float]
    aspect_ratios: Dict[str, float]
    center_of_mass: List[float]
    principal_extents: List[float]
    approximate_symmetry_scores: Dict[str, float]  # x_plane, y_plane, z_plane


class StructuralMetrics(BaseModel):
    component_sizes: List[int]
    isolated_fragments_count: int
    has_unexpected_protrusions: bool
    max_protrusion_distance: float
    thin_structures_detected: bool


class TextureMetrics(BaseModel):
    has_vertex_colors: bool
    has_uv_coordinates: bool
    has_texture_image: bool
    texture_resolution: Optional[List[int]] = None
    material_type: str
    texture_mode: str  # "vertex_colored", "uv_mapped", "untextured_clay"
    texture_status_message: str


class ViewSilhouetteMetric(BaseModel):
    view_name: str
    camera_eye: List[float]
    camera_target: List[float]
    occupancy_ratio: float
    silhouette_pixels: int
    rendered_image_path: Optional[str] = None
    iou_with_sketch: Optional[float] = None


class MultiViewMetrics(BaseModel):
    views: Dict[str, ViewSilhouetteMetric]
    front_sketch_iou: Optional[float] = None
    cross_view_continuity_score: float
    asymmetry_detected: bool
    structural_completeness_score: float


class DefectReport(BaseModel):
    has_defects: bool
    defect_count: int
    non_manifold_edges: int
    boundary_holes: int
    degenerate_triangles: int
    duplicate_vertices: int
    isolated_fragments: int
    non_finite_coordinates: int
    unoriented_normals: bool
    defect_list: List[str]


class QualitySubscores(BaseModel):
    topology: float = Field(..., ge=0.0, le=100.0, description="Topology & manifold score [0-100]")
    geometry: float = Field(..., ge=0.0, le=100.0, description="Spatial & symmetry score [0-100]")
    surface: float = Field(..., ge=0.0, le=100.0, description="Normals & curvature smoothness [0-100]")
    multiview: Optional[float] = Field(None, ge=0.0, le=100.0, description="Multi-view silhouette IoU [0-100]")
    texture: float = Field(..., ge=0.0, le=100.0, description="Texture completeness [0-100]")
    export: float = Field(..., ge=0.0, le=100.0, description="Export format integrity [0-100]")


class QualityScore(BaseModel):
    overall_score: float = Field(..., ge=0.0, le=100.0)
    subscores: QualitySubscores
    warnings: List[str]
    detected_defects: List[str]
    recommendations: List[str]
    confidence_level: str  # "high", "moderate", "heuristic_only"


class MeshComparison(BaseModel):
    asset_id: str
    operation: str
    duration_seconds: float
    original_vertices: int
    refined_vertices: int
    vertex_delta: int
    original_faces: int
    refined_faces: int
    face_delta: int
    original_watertight: bool
    refined_watertight: bool
    original_surface_area: float
    refined_surface_area: float
    original_file_size_bytes: int
    refined_file_size_bytes: int
    is_degraded: bool
    summary: str


class GeometryReport(BaseModel):
    asset_id: str
    source_file: str
    timestamp: float
    topology: TopologyMetrics
    surface: SurfaceMetrics
    spatial: SpatialMetrics
    structural: StructuralMetrics
    texture: TextureMetrics
    multiview: Optional[MultiViewMetrics] = None
    defects: DefectReport
    quality: QualityScore

"""
Structured Schemas and Data Models for Sketch Preprocessing & Analysis
Defines strongly-typed representations for metrics, analysis results, and configuration.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Tuple


@dataclass
class ImageDimensions:
    width: int
    height: int
    channels: int
    aspect_ratio: float


@dataclass
class ValidationResult:
    is_valid: bool
    format: str
    dimensions: ImageDimensions
    file_size_bytes: int
    has_alpha: bool
    is_grayscale: bool
    error_message: Optional[str] = None


@dataclass
class EnhancementMetrics:
    mean_luminance_before: float
    mean_luminance_after: float
    contrast_std_before: float
    contrast_std_after: float
    dynamic_range: float
    gamma_applied: float
    illumination_corrected: bool


@dataclass
class EdgeMetrics:
    edge_density: float
    canny_density: float
    sobel_density: float
    laplacian_variance: float
    selected_method: str


@dataclass
class ContourMetrics:
    contour_count: int
    main_contour_area: float
    main_contour_perimeter: float
    bounding_box: Tuple[int, int, int, int]  # (x, y, w, h)
    convex_hull_area: float
    solidity: float
    extent: float
    aspect_ratio: float
    hierarchy_depth: int


@dataclass
class StrokeMetrics:
    average_width_estimate: float
    stroke_density: float
    total_stroke_length: float
    endpoint_count: int
    junction_count: int
    connected_components_count: int
    line_continuity_score: float


@dataclass
class SymmetryMetrics:
    horizontal_symmetry: float
    vertical_symmetry: float
    estimated_axis_x: float
    estimated_axis_y: float
    symmetry_score: float


@dataclass
class ShapeMetrics:
    foreground_occupancy: float
    bounding_box: Tuple[int, int, int, int]  # (x, y, w, h)
    aspect_ratio: float
    centroid: Tuple[float, float]  # (cx, cy)
    compactness: float
    contour_complexity: float
    edge_density: float
    orientation_degrees: float
    eccentricity: float


@dataclass
class PreprocessingReport:
    image_dimensions: Dict[str, Any]
    foreground_occupancy: float
    edge_density: float
    contour_count: int
    stroke_analysis: Dict[str, Any]
    shape_analysis: Dict[str, Any]
    symmetry: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

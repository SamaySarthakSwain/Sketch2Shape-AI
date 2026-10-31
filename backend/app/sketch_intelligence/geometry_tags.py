"""
Geometric Feature Tagging Engine for Sketch Intelligence
Extracts interpretable, documented geometric tags from Stage 5 preprocessing metrics.

Documented Thresholds:
1. `approximately_symmetric`: Reflectional symmetry IoU >= 0.60
2. `predominantly_horizontal`: Dominant orientation |theta| <= 20 degrees
3. `predominantly_vertical`: Dominant orientation |theta| >= 70 degrees
4. `elongated`: Aspect ratio >= 1.70 or <= 0.58
5. `circular_structure`: Isoperimetric compactness >= 0.65
6. `thin_structure`: Stroke density <= 0.05 or stroke width <= 3.5 px
7. `complex_contour`: Contour complexity >= 1.75
8. `multiple_components`: Connected components count >= 3
9. `enclosed_region`: Enclosed internal holes >= 1 or hierarchy depth >= 2
"""

from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class GeometricThresholds:
    symmetry_min: float = 0.60
    horizontal_angle_max: float = 20.0
    vertical_angle_min: float = 70.0
    elongation_high: float = 1.70
    elongation_low: float = 0.58
    circular_compactness_min: float = 0.65
    thin_density_max: float = 0.05
    thin_width_max: float = 3.5
    complexity_min: float = 1.75
    multiple_components_min: int = 3
    enclosed_hierarchy_min: int = 2


class GeometricFeatureTagger:
    def __init__(self, thresholds: GeometricThresholds = GeometricThresholds()):
        self.t = thresholds

    def extract_tags(self, stage5_report: Any) -> List[str]:
        """
        Extracts categorical geometric tags from a Stage 5 PreprocessingReport or dict.
        """
        tags = []

        # 1. Symmetry
        symm_score = 0.0
        if hasattr(stage5_report, "symmetry"):
            symm_score = getattr(stage5_report.symmetry, "score", 0.0) if hasattr(stage5_report.symmetry, "score") else stage5_report.symmetry.get("score", 0.0)
        elif isinstance(stage5_report, dict) and "symmetry" in stage5_report:
            symm_score = stage5_report["symmetry"].get("score", 0.0)

        if symm_score >= self.t.symmetry_min:
            tags.append("approximately_symmetric")

        # 2. Shape Moments & PCA Orientation
        orientation = 0.0
        aspect_ratio = 1.0
        compactness = 0.0
        complexity = 1.0

        if hasattr(stage5_report, "shape_analysis"):
            sa = stage5_report.shape_analysis
            orientation = getattr(sa, "orientation_degrees", 0.0) if hasattr(sa, "orientation_degrees") else sa.get("orientation_degrees", 0.0)
            aspect_ratio = getattr(sa, "aspect_ratio", 1.0) if hasattr(sa, "aspect_ratio") else sa.get("aspect_ratio", 1.0)
            compactness = getattr(sa, "compactness", 0.0) if hasattr(sa, "compactness") else sa.get("compactness", 0.0)
            complexity = getattr(sa, "complexity", 1.0) if hasattr(sa, "complexity") else sa.get("complexity", 1.0)
        elif isinstance(stage5_report, dict) and "shape_analysis" in stage5_report:
            sa = stage5_report["shape_analysis"]
            orientation = sa.get("orientation_degrees", 0.0)
            aspect_ratio = sa.get("aspect_ratio", 1.0)
            compactness = sa.get("compactness", 0.0)
            complexity = sa.get("complexity", 1.0)

        abs_angle = abs(orientation)
        if abs_angle <= self.t.horizontal_angle_max:
            tags.append("predominantly_horizontal")
        elif abs_angle >= self.t.vertical_angle_min:
            tags.append("predominantly_vertical")

        if aspect_ratio >= self.t.elongation_high or aspect_ratio <= self.t.elongation_low:
            tags.append("elongated")

        if compactness >= self.t.circular_compactness_min:
            tags.append("circular_structure")

        if complexity >= self.t.complexity_min:
            tags.append("complex_contour")

        # 3. Stroke Topology
        stroke_density = 0.05
        stroke_width = 4.0
        components = 1

        if hasattr(stage5_report, "stroke_analysis"):
            sta = stage5_report.stroke_analysis
            stroke_density = getattr(sta, "stroke_density", 0.05) if hasattr(sta, "stroke_density") else sta.get("stroke_density", 0.05)
            stroke_width = getattr(sta, "average_width_estimate", 4.0) if hasattr(sta, "average_width_estimate") else sta.get("average_width_estimate", 4.0)
            components = getattr(sta, "connected_components_count", 1) if hasattr(sta, "connected_components_count") else sta.get("connected_components_count", 1)
        elif isinstance(stage5_report, dict) and "stroke_analysis" in stage5_report:
            sta = stage5_report["stroke_analysis"]
            stroke_density = sta.get("stroke_density", 0.05)
            stroke_width = sta.get("average_width_estimate", 4.0)
            components = sta.get("connected_components_count", 1)

        if stroke_density <= self.t.thin_density_max or stroke_width <= self.t.thin_width_max:
            tags.append("thin_structure")

        if components >= self.t.multiple_components_min:
            tags.append("multiple_components")

        # 4. Enclosed Regions / Hierarchy Depth
        depth = 1
        if hasattr(stage5_report, "metadata"):
            md = stage5_report.metadata
            depth = getattr(md, "hierarchy_depth", 1) if hasattr(md, "hierarchy_depth") else md.get("hierarchy_depth", 1)
        elif isinstance(stage5_report, dict) and "metadata" in stage5_report:
            depth = stage5_report["metadata"].get("hierarchy_depth", 1)

        if depth >= self.t.enclosed_hierarchy_min:
            tags.append("enclosed_region")

        return tags

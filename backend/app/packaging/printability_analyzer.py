"""
3D Printability and Physical Geometry Analyzer
Evaluates mesh topology for additive manufacturing (FDM, SLA, SLS):
- Watertightness / Closure verification
- Non-manifold edges and boundary seams
- Connected component count
- Estimated minimum wall thickness and thin-feature detection
- Physical bounding dimensions (mm) and volumetric mass estimate
- Printability score (0..100) and actionable warnings
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import numpy as np
import trimesh


@dataclass
class PrintabilityReport:
    is_printable: bool
    printability_score: float  # 0 to 100
    is_watertight: bool
    is_manifold: bool
    connected_components: int
    volume_cm3: float
    surface_area_cm2: float
    dimensions_mm: Dict[str, float]  # width, height, depth
    min_wall_thickness_estimate_mm: float
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_printable": self.is_printable,
            "printability_score": round(self.printability_score, 1),
            "is_watertight": self.is_watertight,
            "is_manifold": self.is_manifold,
            "connected_components": self.connected_components,
            "volume_cm3": round(self.volume_cm3, 2),
            "surface_area_cm2": round(self.surface_area_cm2, 2),
            "dimensions_mm": {k: round(v, 1) for k, v in self.dimensions_mm.items()},
            "min_wall_thickness_estimate_mm": round(self.min_wall_thickness_estimate_mm, 2),
            "warnings": self.warnings,
            "recommendations": self.recommendations,
        }


class PrintabilityAnalyzer:
    DEFAULT_SCALE_TARGET_MM = 100.0  # Scale longest dimension to 100mm for analysis

    @classmethod
    def analyze(
        cls,
        mesh: trimesh.Trimesh,
        target_longest_dim_mm: float = 100.0
    ) -> PrintabilityReport:
        warnings = []
        recommendations = []
        score = 100.0

        if mesh.is_empty or len(mesh.vertices) == 0:
            return PrintabilityReport(
                is_printable=False,
                printability_score=0.0,
                is_watertight=False,
                is_manifold=False,
                connected_components=0,
                volume_cm3=0.0,
                surface_area_cm2=0.0,
                dimensions_mm={"x": 0.0, "y": 0.0, "z": 0.0},
                min_wall_thickness_estimate_mm=0.0,
                warnings=["Mesh is empty or contains 0 vertices."]
            )

        # Scale mesh to physical millimeter dimension for realistic print diagnostics
        scaled_m = mesh.copy()
        current_max_dim = max(scaled_m.extents)
        if current_max_dim > 0:
            scale_factor = target_longest_dim_mm / current_max_dim
            scaled_m.apply_scale(scale_factor)
        else:
            scale_factor = 1.0

        extents_mm = {
            "x": float(scaled_m.extents[0]),
            "y": float(scaled_m.extents[1]),
            "z": float(scaled_m.extents[2])
        }

        # 1. Watertightness check
        is_watertight = bool(scaled_m.is_watertight)
        if not is_watertight:
            score -= 35.0
            warnings.append("Mesh is NOT watertight (open boundary edges found). Slicers may produce invalid toolpaths.")
            recommendations.append("Apply mesh repair (closing boundary holes) before slicing.")

        # 2. Manifoldness check
        is_manifold = bool(scaled_m.is_winding_consistent and not scaled_m.faces.size == 0)
        # Check for non-manifold edges
        edges = scaled_m.edges_sorted
        unique_edges, counts = np.unique(edges, axis=0, return_counts=True)
        non_manifold_edges = np.sum(counts > 2)
        if non_manifold_edges > 0:
            is_manifold = False
            score -= 20.0
            warnings.append(f"Detected {non_manifold_edges} non-manifold edges (edges shared by more than 2 faces).")

        # 3. Connected components check
        components = scaled_m.split(only_watertight=False)
        comp_count = len(components)
        if comp_count > 1:
            score -= min(25.0, (comp_count - 1) * 5.0)
            warnings.append(f"Mesh consists of {comp_count} disconnected geometric parts (floating shells).")
            recommendations.append("Union separate bodies using Boolean operations or support structures.")

        # 4. Volume & Surface Area
        try:
            vol_mm3 = float(scaled_m.volume) if is_watertight else float(scaled_m.convex_hull.volume * 0.7)
            vol_cm3 = max(0.0, vol_mm3 / 1000.0)
        except Exception:
            vol_cm3 = float(np.prod(scaled_m.extents) / 1000.0 * 0.4)

        try:
            area_mm2 = float(scaled_m.area)
            area_cm2 = max(0.0, area_mm2 / 100.0)
        except Exception:
            area_cm2 = 0.0

        # 5. Wall Thickness Estimation
        # Compute nearest distance between interior surface vertices
        min_thickness_mm = cls._estimate_wall_thickness(scaled_m)
        if min_thickness_mm < 0.8:  # Typical 0.4mm nozzle needs at least 0.8mm for 2 perimeters
            score -= 15.0
            warnings.append(f"Estimated minimum wall thickness is {min_thickness_mm:.2f}mm, which is below the recommended 1.2mm minimum for FDM printing.")
            recommendations.append("Scale up the physical model or thicken thin wall features.")

        # Ensure score bounds
        final_score = float(np.clip(score, 0.0, 100.0))
        is_printable = bool(final_score >= 60.0 and is_watertight)

        if is_printable and not recommendations:
            recommendations.append("Mesh is solid and manifold. Ready for slicing in Cura, PrusaSlicer, or Bambu Studio.")

        return PrintabilityReport(
            is_printable=is_printable,
            printability_score=final_score,
            is_watertight=is_watertight,
            is_manifold=is_manifold,
            connected_components=comp_count,
            volume_cm3=vol_cm3,
            surface_area_cm2=area_cm2,
            dimensions_mm=extents_mm,
            min_wall_thickness_estimate_mm=min_thickness_mm,
            warnings=warnings,
            recommendations=recommendations
        )

    @classmethod
    def _estimate_wall_thickness(cls, mesh: trimesh.Trimesh) -> float:
        """
        Estimates minimum geometric thickness across the mesh.
        """
        try:
            # Check bounding box minimum extent as an upper bound
            min_dim = float(min(mesh.extents))
            if len(mesh.vertices) < 30:
                return max(0.5, min_dim * 0.5)

            # Sample random surface points and raycast inwards along inverted normals
            sample_count = min(100, len(mesh.vertices))
            indices = np.random.choice(len(mesh.vertices), sample_count, replace=False)
            origins = mesh.vertices[indices]
            directions = -mesh.vertex_normals[indices]

            # Ray-mesh intersection query
            locations, index_ray, _ = mesh.ray.intersects_location(
                ray_origins=origins + directions * 1e-4,
                ray_directions=directions
            )

            if len(locations) > 0:
                dists = np.linalg.norm(locations - origins[index_ray], axis=1)
                valid_dists = dists[dists > 0.1]
                if len(valid_dists) > 0:
                    return float(np.percentile(valid_dists, 10))

            return max(1.0, min_dim * 0.1)
        except Exception:
            return 1.5

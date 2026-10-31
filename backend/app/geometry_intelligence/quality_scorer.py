"""
Transparent Asset Quality Scorer Module
Calculates interpretable, mathematically grounded subscores (0-100)
for topology, geometry, surface properties, multi-view consistency, texture, and export.
"""

from typing import List, Dict, Any, Optional
from .geometry_metrics import (
    TopologyMetrics,
    SurfaceMetrics,
    SpatialMetrics,
    StructuralMetrics,
    TextureMetrics,
    MultiViewMetrics,
    DefectReport,
    QualitySubscores,
    QualityScore,
)


class QualityScorer:
    @staticmethod
    def calculate_scores(
        topology: TopologyMetrics,
        surface: SurfaceMetrics,
        spatial: SpatialMetrics,
        structural: StructuralMetrics,
        texture: TextureMetrics,
        multiview: Optional[MultiViewMetrics],
        defects: DefectReport,
    ) -> QualityScore:
        """
        Computes transparent mathematical quality score and actionable recommendations.
        """
        warnings: List[str] = []
        recommendations: List[str] = []

        # -------------------------------------------------------------
        # 1. Topology Subscore (0 - 100)
        # -------------------------------------------------------------
        s_topo = 100.0
        if not topology.is_watertight:
            s_topo -= 35.0
            warnings.append("Mesh is non-watertight (contains open boundary edges).")
            recommendations.append("Apply mesh hole-filling and manifold repair prior to 3D printing.")

        if topology.non_manifold_edges_count > 0:
            s_topo -= min(30.0, float(topology.non_manifold_edges_count) * 4.0)
            warnings.append(f"Non-manifold geometry detected ({topology.non_manifold_edges_count} edges).")
            recommendations.append("Execute non-manifold edge split or removal pass.")

        if topology.degenerate_faces_count > 0:
            s_topo -= min(15.0, float(topology.degenerate_faces_count) * 2.0)
            recommendations.append("Purge zero-area degenerate triangles.")

        if topology.duplicate_vertices_count > 0:
            s_topo -= min(10.0, float(topology.duplicate_vertices_count) * 1.0)
            recommendations.append("Merge coincident duplicate vertices.")

        # Penalize extreme under-tessellation (e.g. 8-vertex cuboid)
        if topology.vertex_count < 16 or topology.face_count < 24:
            s_topo = min(s_topo, 35.0)
            warnings.append(
                f"Severe under-tessellation ({topology.vertex_count} vertices, {topology.face_count} faces). Reconstruction captured minimal volume."
            )

        s_topo = max(0.0, min(100.0, round(s_topo, 1)))

        # -------------------------------------------------------------
        # 2. Geometry Subscore (0 - 100)
        # -------------------------------------------------------------
        s_geom = 50.0

        # Bilateral symmetry reward (sagittal X-plane)
        x_sym = spatial.approximate_symmetry_scores.get("x_plane", 0.5)
        s_geom += x_sym * 35.0

        # Protrusions penalty
        if structural.has_unexpected_protrusions:
            s_geom -= 20.0
            warnings.append("Unexpected geometric protrusion detected.")
            recommendations.append("Apply outlier vertex smoothing to eliminate spikes.")
        else:
            s_geom += 15.0

        # Aspect ratio bounds penalty (extreme thin sliver or extreme pancake)
        ratios = spatial.aspect_ratios
        if ratios.get("xy", 1.0) > 8.0 or ratios.get("xy", 1.0) < 0.1:
            s_geom -= 15.0
            warnings.append("Extreme aspect ratio deviation detected.")

        s_geom = max(0.0, min(100.0, round(s_geom, 1)))

        # -------------------------------------------------------------
        # 3. Surface Subscore (0 - 100)
        # -------------------------------------------------------------
        s_surf = 100.0
        if not surface.normal_consistency:
            s_surf -= 40.0
            warnings.append("Inconsistent polygon winding order detected.")
            recommendations.append("Recalculate face normals with outward orientation.")

        if surface.inverted_normals_count > 0 and topology.face_count > 0:
            inv_ratio = float(surface.inverted_normals_count) / float(topology.face_count)
            s_surf -= min(35.0, inv_ratio * 70.0)

        # Roughness penalty
        if surface.surface_roughness_std > 0.8:
            s_surf -= min(25.0, (surface.surface_roughness_std - 0.8) * 20.0)
            recommendations.append("Apply Taubin volume-preserving smoothing to reduce surface noise.")

        s_surf = max(0.0, min(100.0, round(s_surf, 1)))

        # -------------------------------------------------------------
        # 4. Multi-View Subscore (0 - 100 or None)
        # -------------------------------------------------------------
        s_multi: Optional[float] = None
        if multiview is not None:
            if multiview.front_sketch_iou is not None:
                # 60% front IoU + 40% continuity
                score_mv = (multiview.front_sketch_iou * 60.0) + (multiview.cross_view_continuity_score * 40.0)
            else:
                score_mv = multiview.cross_view_continuity_score * 100.0

            if multiview.asymmetry_detected:
                score_mv -= 12.0
                warnings.append("Significant lateral asymmetry observed in orthogonal views.")

            s_multi = max(0.0, min(100.0, round(score_mv, 1)))
        else:
            # Explicitly mark missing metric as None (not silently 100)
            s_multi = None

        # -------------------------------------------------------------
        # 5. Texture Subscore (0 - 100)
        # -------------------------------------------------------------
        if texture.texture_mode == "uv_mapped":
            s_tex = 95.0
            if texture.texture_resolution and min(texture.texture_resolution) >= 1024:
                s_tex = 100.0
        elif texture.texture_mode == "vertex_colored":
            s_tex = 70.0  # Functional vertex color representation
        elif texture.texture_mode == "uv_without_texture":
            s_tex = 40.0
            warnings.append("UV coordinates present without bound texture image.")
        else:
            # Clay mode is clean neutral baseline for untextured sculptures
            s_tex = 55.0

        s_tex = max(0.0, min(100.0, round(s_tex, 1)))

        # -------------------------------------------------------------
        # 6. Export Integrity Subscore (0 - 100)
        # -------------------------------------------------------------
        s_exp = 100.0
        if defects.non_finite_coordinates > 0:
            s_exp = 0.0
            warnings.append("CRITICAL: Non-finite coordinates present. Model will crash standard 3D loaders.")
        elif topology.face_count == 0 or topology.vertex_count == 0:
            s_exp = 0.0
        elif topology.face_count < 15:
            s_exp -= 35.0

        if defects.isolated_fragments > 0:
            s_exp -= min(15.0, float(defects.isolated_fragments) * 5.0)
            recommendations.append("Prune disconnected floating fragments before production export.")

        s_exp = max(0.0, min(100.0, round(s_exp, 1)))

        # -------------------------------------------------------------
        # 7. Composite Overall Score
        # -------------------------------------------------------------
        if s_multi is not None:
            # Standard weighted average with multi-view
            overall = (
                0.25 * s_topo
                + 0.20 * s_geom
                + 0.15 * s_surf
                + 0.20 * s_multi
                + 0.10 * s_tex
                + 0.10 * s_exp
            )
            confidence = "high"
        else:
            # Re-normalized weights without multi-view
            w_sum = 0.30 + 0.25 + 0.20 + 0.12 + 0.13
            overall = (
                0.30 * s_topo
                + 0.25 * s_geom
                + 0.20 * s_surf
                + 0.12 * s_tex
                + 0.13 * s_exp
            ) / w_sum
            confidence = "moderate"

        overall = max(0.0, min(100.0, round(overall, 1)))

        subscores = QualitySubscores(
            topology=s_topo,
            geometry=s_geom,
            surface=s_surf,
            multiview=s_multi,
            texture=s_tex,
            export=s_exp,
        )

        return QualityScore(
            overall_score=overall,
            subscores=subscores,
            warnings=warnings,
            detected_defects=defects.defect_list,
            recommendations=recommendations,
            confidence_level=confidence,
        )

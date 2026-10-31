"""
Geometry Report Serialization and Formatting Module
Outputs JSON data structures, Markdown summaries, and comparative benchmarks.
"""

import json
from pathlib import Path
from typing import Dict, Any, Union
from .geometry_metrics import GeometryReport, MeshComparison


class GeometryReportFormatter:
    @staticmethod
    def to_dict(report: GeometryReport) -> Dict[str, Any]:
        """Converts report to standard JSON-compatible Python dictionary."""
        return report.dict()

    @staticmethod
    def save_json(report: Union[GeometryReport, Dict[str, Any]], output_path: Union[str, Path]):
        """Persists report dictionary to formatted JSON file."""
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        data = report.dict() if hasattr(report, "dict") else report
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def to_markdown(report: GeometryReport) -> str:
        """Renders comprehensive Markdown diagnostic report."""
        q = report.quality
        t = report.topology
        s = report.surface
        sp = report.spatial
        st = report.structural
        tex = report.texture
        d = report.defects

        md = f"""# Geometry Intelligence Diagnostic: `{report.asset_id}`

**Overall Quality Score:** **{q.overall_score} / 100** ({q.confidence_level.upper()} CONFIDENCE)

### Subscore Breakdown:
* **Topology:** {q.subscores.topology}/100
* **Geometry:** {q.subscores.geometry}/100
* **Surface:** {q.subscores.surface}/100
* **Multi-View Consistency:** {q.subscores.multiview if q.subscores.multiview is not None else 'N/A'}/100
* **Texture Completeness:** {q.subscores.texture}/100
* **Export Integrity:** {q.subscores.export}/100

---

### 1. Topological Metrics:
* **Vertices:** {t.vertex_count:,}
* **Faces:** {t.face_count:,}
* **Edges:** {t.edge_count:,}
* **Watertight:** {'✅ YES' if t.is_watertight else '❌ NO'}
* **Euler Characteristic (χ):** {t.euler_characteristic}
* **Connected Components:** {t.connected_components}
* **Boundary Edges:** {t.boundary_edges_count}
* **Non-Manifold Edges:** {t.non_manifold_edges_count}
* **Degenerate Faces:** {t.degenerate_faces_count}
* **Duplicate Vertices:** {t.duplicate_vertices_count}

---

### 2. Surface & Spatial Properties:
* **Surface Area:** {s.surface_area:.4f} m²
* **Volume:** {f'{s.volume:.6f} m³' if s.is_volume_valid else 'N/A (open mesh)'}
* **Normal Consistency:** {'✅ Consistent' if s.normal_consistency else '⚠️ Inconsistent Winding'}
* **Roughness (Std Dev):** {s.surface_roughness_std:.4f}
* **Dimensions (XYZ):** [{sp.dimensions_xyz[0]:.3f}, {sp.dimensions_xyz[1]:.3f}, {sp.dimensions_xyz[2]:.3f}]
* **Bilateral Symmetry (X-Plane):** {sp.approximate_symmetry_scores.get('x_plane', 0.0):.2f} / 1.0

---

### 3. Material & Texture Status:
* **Texture Mode:** `{tex.texture_mode}`
* **Status:** {tex.texture_status_message}
* **Vertex Colors:** {'Yes' if tex.has_vertex_colors else 'No'}
* **UV Map:** {'Yes' if tex.has_uv_coordinates else 'No'}

---

### 4. Defect Detection & Recommendations:
* **Defect Count:** {d.defect_count}
"""
        if d.defect_list:
            for item in d.defect_list:
                md += f"  - ⚠️ {item}\n"
        else:
            md += "  - ✅ No critical geometric defects detected.\n"

        if q.recommendations:
            md += "\n**Recommendations:**\n"
            for rec in q.recommendations:
                md += f"  - 💡 {rec}\n"

        return md

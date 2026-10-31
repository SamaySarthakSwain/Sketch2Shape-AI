"""
Master Mesh Analyzer Module
Coordinates topology, surface, spatial, component, texture, multi-view inspection,
defect detection, and transparent quality scoring into a unified API.
"""

import time
from pathlib import Path
from typing import Optional, Union, Dict, Any
import trimesh

from .geometry_metrics import GeometryReport
from .topology_analyzer import TopologyAnalyzer
from .surface_analyzer import SurfaceAnalyzer
from .symmetry_analyzer import SymmetryAnalyzer
from .component_analyzer import ComponentAnalyzer
from .texture_analyzer import TextureAnalyzer
from .defect_detector import DefectDetector
from .multiview_inspector import MultiViewInspector
from .quality_scorer import QualityScorer


class MeshAnalyzer:
    def __init__(self, multiview_output_dir: Optional[Path] = None):
        self.multiview_inspector = MultiViewInspector(output_dir=multiview_output_dir)

    def analyze(
        self,
        mesh_input: Union[trimesh.Trimesh, str, Path],
        asset_id: str = "asset",
        run_multiview: bool = False,
        sketch_path: Optional[str] = None
    ) -> GeometryReport:
        """
        Executes complete multi-domain geometric, topological, texture,
        and multi-view quality audit.
        """
        t0 = time.time()
        source_file = "in_memory_mesh"

        # 1. Ingest Mesh
        if isinstance(mesh_input, (str, Path)):
            source_file = str(mesh_input)
            mesh = trimesh.load(source_file, force="mesh")
        else:
            mesh = mesh_input

        # 2. Domain Analyzers
        topology = TopologyAnalyzer.analyze(mesh)
        surface = SurfaceAnalyzer.analyze(mesh)
        spatial = SymmetryAnalyzer.analyze(mesh)
        structural = ComponentAnalyzer.analyze(mesh)
        texture = TextureAnalyzer.analyze(mesh if source_file == "in_memory_mesh" else source_file)

        # 3. Defect Detection
        defects = DefectDetector.detect(mesh, topology, surface, structural)

        # 4. Optional Multi-View Inspection
        multiview = None
        if run_multiview:
            # Need a physical file for Open3D offscreen rendering
            temp_path = None
            if source_file == "in_memory_mesh":
                temp_dir = Path(r"C:\Sketch2Shape-AI\outputs\geometry_analysis")
                temp_dir.mkdir(parents=True, exist_ok=True)
                temp_path = temp_dir / f"{asset_id}_temp.obj"
                mesh.export(str(temp_path))
                target_file = str(temp_path)
            else:
                target_file = source_file

            try:
                multiview = self.multiview_inspector.inspect(
                    mesh_path=target_file,
                    asset_id=asset_id,
                    sketch_path=sketch_path
                )
            except Exception as e:
                print(f"[MeshAnalyzer] Multi-view inspection warning: {e}")
                multiview = None
            finally:
                if temp_path and temp_path.exists():
                    try:
                        temp_path.unlink()
                    except Exception:
                        pass

        # 5. Quality Scoring
        quality = QualityScorer.calculate_scores(
            topology=topology,
            surface=surface,
            spatial=spatial,
            structural=structural,
            texture=texture,
            multiview=multiview,
            defects=defects,
        )

        return GeometryReport(
            asset_id=asset_id,
            source_file=source_file,
            timestamp=round(t0, 2),
            topology=topology,
            surface=surface,
            spatial=spatial,
            structural=structural,
            texture=texture,
            multiview=multiview,
            defects=defects,
            quality=quality,
        )

"""
Production Asset Packaging Engine
Assembles comprehensive distribution packages (.zip) containing:
- Multi-format 3D models (GLB, OBJ+MTL, STL, 3MF, USDZ)
- Standalone PBR texture maps (Albedo, Normal, Roughness, Metallic, AO)
- Multi-resolution LODs (LOD0, LOD1, LOD2)
- Printability and topology verification reports
- Integration instructions for Blender, Unity, Unreal Engine, and Web
"""

import os
import json
import zipfile
from pathlib import Path
from typing import Dict, Any, Optional
import trimesh

from .multi_format_exporter import MultiFormatExporter
from .printability_analyzer import PrintabilityAnalyzer, PrintabilityReport
from .lod_generator import LODGenerator


class AssetPackager:
    @classmethod
    def create_package(
        cls,
        mesh: trimesh.Trimesh,
        category: str,
        job_id: str,
        output_dir: str,
        base_name: str = "asset",
        texture_paths: Optional[Dict[str, str]] = None,
        untextured_mesh: Optional[trimesh.Trimesh] = None,
        geometry_metrics: Optional[Dict[str, Any]] = None,
        material_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Creates a complete professional distribution bundle in output_dir.
        Returns package metadata and zip download path.
        """
        pkg_dir = Path(output_dir) / f"{base_name}_package"
        pkg_dir.mkdir(parents=True, exist_ok=True)

        # 1. Export all 3D formats
        models_dir = pkg_dir / "models"
        exported_formats = MultiFormatExporter.export_all_formats(
            mesh=mesh,
            output_dir=str(models_dir),
            base_filename=base_name
        )

        # 2. Export untextured reference GLB if provided
        if untextured_mesh:
            untextured_path = models_dir / f"{base_name}_untextured.glb"
            with open(untextured_path, "wb") as f:
                f.write(untextured_mesh.export(file_type="glb"))

        # 3. Generate Level of Detail (LODs)
        lods_info = LODGenerator.generate_lods(
            mesh=mesh,
            output_dir=str(pkg_dir),
            base_name=base_name
        )

        # 4. Copy standalone PBR texture maps
        textures_dir = pkg_dir / "textures"
        textures_dir.mkdir(parents=True, exist_ok=True)
        included_textures = {}
        if texture_paths:
            for map_name, src_p in texture_paths.items():
                p = Path(src_p)
                if p.exists():
                    dest = textures_dir / p.name
                    with open(p, "rb") as rf, open(dest, "wb") as wf:
                        wf.write(rf.read())
                    included_textures[map_name] = p.name

        # 5. Run Printability Analysis
        print_report: PrintabilityReport = PrintabilityAnalyzer.analyze(mesh)
        print_dict = print_report.to_dict()

        # 6. Save Reports
        reports_dir = pkg_dir / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        with open(reports_dir / "printability_report.json", "w") as f:
            json.dump(print_dict, f, indent=2)

        if geometry_metrics:
            with open(reports_dir / "geometry_report.json", "w") as f:
                json.dump(geometry_metrics, f, indent=2)

        if material_metadata:
            with open(reports_dir / "material_metadata.json", "w") as f:
                json.dump(material_metadata, f, indent=2)

        # 7. Write README.md
        cls._write_readme(
            readme_path=pkg_dir / "README.md",
            category=category,
            base_name=base_name,
            print_report=print_report,
            lods_info=lods_info
        )

        # 8. Compress into Final ZIP Bundle
        zip_path = Path(output_dir) / f"{base_name}_bundle.zip"
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for root, _, files in os.walk(pkg_dir):
                for file in files:
                    full_p = Path(root) / file
                    arcname = full_p.relative_to(pkg_dir)
                    z.write(full_p, arcname=str(arcname))

        return {
            "zip_path": str(zip_path),
            "zip_size_bytes": zip_path.stat().st_size,
            "exported_formats": list(exported_formats.keys()),
            "included_textures": list(included_textures.keys()),
            "printability": print_dict,
            "lods": {k: {"faces": v["faces"], "verts": v["vertices"]} for k, v in lods_info.items()}
        }

    @staticmethod
    def _write_readme(
        readme_path: Path,
        category: str,
        base_name: str,
        print_report: PrintabilityReport,
        lods_info: Dict[str, Any]
    ):
        content = f"""# Sketch2Shape AI — Professional 3D Asset Package

**Generated Asset:** `{base_name}`  
**Category:** `{category}`  
**Pipeline Standard:** glTF 2.0 PBR Metallic-Roughness  

---

## 1. Included Files

### Models (`/models/`)
- `{base_name}.glb`: Production glTF 2.0 binary asset with embedded PBR textures.
- `{base_name}.gltf`: Standard JSON glTF scene for web and game engines.
- `{base_name}.obj` + `{base_name}.mtl`: Universal Wavefront geometry.
- `{base_name}.stl`: Binary Stereolithography mesh for 3D slicers.
- `{base_name}.3mf`: 3D Manufacturing Format archive for multi-material printers.
- `{base_name}.usdz`: Apple AR / iOS QuickLook scene.

### Level of Detail (`/lods/`)
- `LOD0`: 100% Geometry ({lods_info['lod0']['faces']} faces) — High detail render.
- `LOD1`: ~50% Geometry ({lods_info['lod1']['faces']} faces) — Game runtime.
- `LOD2`: ~25% Geometry ({lods_info['lod2']['faces']} faces) — Mobile & background.

### Textures (`/textures/`)
- `albedo.png`: Base Color / Albedo map (sRGB).
- `normal.png`: Tangent-space Normal map (+Y OpenGL).
- `roughness.png`: Greyscale micro-roughness map.
- `metallic.png`: Greyscale metallic reflection map.
- `ao.png`: Ambient occlusion shading map.

---

## 2. 3D Printing Diagnostics

- **Printable:** {'YES' if print_report.is_printable else 'CAUTION / REPAIR REQUIRED'}
- **Printability Score:** {print_report.printability_score:.1f} / 100
- **Watertight:** {'Yes' if print_report.is_watertight else 'No'}
- **Estimated Volume:** {print_report.volume_cm3:.2f} cm³
- **Physical Extents (mm):** X={print_report.dimensions_mm['x']:.1f}mm, Y={print_report.dimensions_mm['y']:.1f}mm, Z={print_report.dimensions_mm['z']:.1f}mm

---

## 3. Engine Compatibility

- **Blender:** Drag and drop `.glb` or `.obj`.
- **Unity:** Supports `.glb` via UnityGLTF or import `.obj` with textures.
- **Unreal Engine 5:** Import `.glb` directly; materials auto-populate Nanite / Lumen PBR.
- **Three.js / Web:** Load via `GLTFLoader`.
"""
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(content)

"""
Level of Detail (LOD) Generation Engine
Generates multi-resolution mesh representations for runtime optimization:
- LOD0: Original high-fidelity mesh (100% geometry)
- LOD1: Medium detail (~50% face count, preserving UVs and silhouette)
- LOD2: Low detail (~25% face count, lightweight web/mobile asset)
"""

from pathlib import Path
from typing import Dict, Tuple, Optional, Any
import trimesh
from ..reconstruction.mesh_processing import MeshProcessor


class LODGenerator:
    @classmethod
    def generate_lods(
        cls,
        mesh: trimesh.Trimesh,
        output_dir: Optional[str] = None,
        base_name: str = "model"
    ) -> Dict[str, Dict[str, Any]]:
        """
        Creates LOD0, LOD1, and LOD2 meshes.
        Optionally exports each LOD as GLB to output_dir/lods/.
        Returns dict with mesh objects, vertex/face counts, and paths.
        """
        lod_dir = (Path(output_dir) / "lods") if output_dir else None
        if lod_dir:
            lod_dir.mkdir(parents=True, exist_ok=True)

        original_faces = len(mesh.faces)

        # LOD0: Original
        lod0_mesh = mesh.copy()

        # LOD1: Target 50% faces
        target_f1 = max(40, int(original_faces * 0.50))
        lod1_mesh = MeshProcessor.decimate(lod0_mesh, max_faces=target_f1)

        # LOD2: Target 25% faces
        target_f2 = max(20, int(original_faces * 0.25))
        lod2_mesh = MeshProcessor.decimate(lod0_mesh, max_faces=target_f2)

        results = {
            "lod0": {
                "mesh": lod0_mesh,
                "vertices": len(lod0_mesh.vertices),
                "faces": len(lod0_mesh.faces),
                "percentage": 100.0,
                "path": str(lod_dir / f"{base_name}_lod0.glb") if lod_dir else None
            },
            "lod1": {
                "mesh": lod1_mesh,
                "vertices": len(lod1_mesh.vertices),
                "faces": len(lod1_mesh.faces),
                "percentage": round(len(lod1_mesh.faces) / max(1, original_faces) * 100.0, 1),
                "path": str(lod_dir / f"{base_name}_lod1.glb") if lod_dir else None
            },
            "lod2": {
                "mesh": lod2_mesh,
                "vertices": len(lod2_mesh.vertices),
                "faces": len(lod2_mesh.faces),
                "percentage": round(len(lod2_mesh.faces) / max(1, original_faces) * 100.0, 1),
                "path": str(lod_dir / f"{base_name}_lod2.glb") if lod_dir else None
            }
        }

        # Export if output_dir provided
        if lod_dir:
            for lod_key, data in results.items():
                m = data["mesh"]
                p = data["path"]
                if p:
                    glb_bytes = m.export(file_type="glb")
                    with open(p, "wb") as f:
                        f.write(glb_bytes)

        return results

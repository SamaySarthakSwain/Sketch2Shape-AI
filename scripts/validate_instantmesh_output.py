"""
Mesh Validation Script for InstantMesh Outputs in Sketch2Shape AI
Validates OBJ outputs and generates validated GLB files using Trimesh.
"""

import os
import sys
import json
import numpy as np
import trimesh
from pathlib import Path

def validate_mesh(obj_path: str, glb_output_path: str = None) -> dict:
    if not os.path.exists(obj_path):
        raise FileNotFoundError(f"Mesh file not found at: {obj_path}")

    file_size_bytes = os.path.getsize(obj_path)
    print(f"[1/6] Loading OBJ mesh: {obj_path} ({file_size_bytes:,} bytes)")
    mesh = trimesh.load(obj_path, process=False)

    # Handle Scene vs Trimesh object
    if isinstance(mesh, trimesh.Scene):
        print("  Collapsing trimesh.Scene into single Trimesh object...")
        mesh = trimesh.util.concatenate([g for g in mesh.geometry.values() if isinstance(g, trimesh.Trimesh)])

    vertices_count = len(mesh.vertices)
    faces_count = len(mesh.faces)
    print(f"[2/6] Topology: {vertices_count:,} vertices, {faces_count:,} faces")

    if vertices_count == 0 or faces_count == 0:
        raise ValueError(f"Invalid mesh topology: vertices={vertices_count}, faces={faces_count}")

    # Check finite coordinates
    is_finite = bool(np.all(np.isfinite(mesh.vertices)))
    print(f"[3/6] Coordinates finite: {is_finite}")
    if not is_finite:
        raise ValueError("Mesh contains NaN or Inf vertex coordinates.")

    # Bounding box
    bbox_min = mesh.bounds[0].tolist()
    bbox_max = mesh.bounds[1].tolist()
    bbox_extents = mesh.extents.tolist()
    print(f"[4/6] Bounding Box: min={bbox_min}, max={bbox_max}, extents={bbox_extents}")

    # Watertightness and Euler characteristic
    is_watertight = bool(mesh.is_watertight)
    euler = int(mesh.euler_number)
    print(f"[5/6] Properties: watertight={is_watertight}, Euler characteristic={euler}")

    # Export to GLB
    if glb_output_path is None:
        glb_output_path = os.path.splitext(obj_path)[0] + ".glb"

    print(f"[6/6] Exporting and validating GLB: {glb_output_path}")
    mesh.export(glb_output_path, file_type="glb")
    glb_size = os.path.getsize(glb_output_path)
    print(f"  GLB export successful ({glb_size:,} bytes).")

    # Round-trip validation
    reloaded_glb = trimesh.load(glb_output_path, process=False)
    if isinstance(reloaded_glb, trimesh.Scene):
        reloaded_glb = trimesh.util.concatenate([g for g in reloaded_glb.geometry.values() if isinstance(g, trimesh.Trimesh)])
    reloaded_verts = len(reloaded_glb.vertices)
    reloaded_faces = len(reloaded_glb.faces)
    print(f"  Round-trip GLB reload verified: {reloaded_verts:,} vertices, {reloaded_faces:,} faces")

    results = {
        "status": "VALIDATED",
        "source_obj": obj_path,
        "source_size_bytes": file_size_bytes,
        "exported_glb": glb_output_path,
        "glb_size_bytes": glb_size,
        "vertices_count": vertices_count,
        "faces_count": faces_count,
        "coordinates_finite": is_finite,
        "bounding_box": {
            "min": bbox_min,
            "max": bbox_max,
            "extents": bbox_extents
        },
        "is_watertight": is_watertight,
        "euler_number": euler,
        "round_trip_reloaded": True,
        "reloaded_vertices": reloaded_verts,
        "reloaded_faces": reloaded_faces
    }

    results_json_path = os.path.splitext(obj_path)[0] + "_validation.json"
    with open(results_json_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n[DONE] Validation report saved to {results_json_path}")
    return results

if __name__ == "__main__":
    target_obj = sys.argv[1] if len(sys.argv) > 1 else "C:/Sketch2Shape-AI/model_repositories/InstantMesh/outputs/instant-mesh-large/meshes/hatsune_miku.obj"
    res = validate_mesh(target_obj)
    print(json.dumps(res, indent=2))

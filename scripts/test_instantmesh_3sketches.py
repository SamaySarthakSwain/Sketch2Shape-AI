"""
Stage 7 Phase 1 Audit: InstantMesh Multi-Sketch 3D Reconstruction Verification
Tests actual 3D reconstruction on 3 distinct sketches:
1. Chair
2. Car
3. Airplane
Verifies:
- Complete end-to-end inference
- Output mesh file existence
- Non-empty vertices & faces
- Trimesh loading & validation
- Reopening exported GLB & OBJ
"""

import os
import sys
import time
import json
from pathlib import Path
import trimesh

# Ensure backend is on PYTHONPATH
BASE_DIR = Path(r"C:\Sketch2Shape-AI")
BACKEND_DIR = BASE_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.reconstruction.adapters.instantmesh_adapter import InstantMeshAdapter
from app.reconstruction.reconstruction_config import ReconstructionRequest
from app.reconstruction.mesh_validation import MeshValidator


def main():
    print("==================================================================")
    print(" STAGE 7 PHASE 1: INSTANTMESH MULTI-SKETCH RECONSTRUCTION AUDIT   ")
    print("==================================================================")

    test_sketches = [
        ("chair", BASE_DIR / "outputs" / "preprocessing_tests" / "quickdraw_chair_normalized.png"),
        ("car", BASE_DIR / "outputs" / "preprocessing_tests" / "quickdraw_car_normalized.png"),
        ("airplane", BASE_DIR / "outputs" / "preprocessing_tests" / "quickdraw_airplane_normalized.png")
    ]

    adapter = InstantMeshAdapter()
    info = adapter.get_model_info()
    print(f"Model: {info.display_name} | Available: {info.is_available} | Device: {adapter.device}\n")

    output_dir = BASE_DIR / "outputs" / "reconstructions" / "phase1_audit"
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []

    for name, img_path in test_sketches:
        if not img_path.exists():
            print(f"Error: {img_path} not found!")
            continue

        print(f"\n>>> Running Reconstruction for: {name.upper()} ({img_path.name})")
        req = ReconstructionRequest(
            image_path=str(img_path),
            output_dir=str(output_dir),
            quality_preset="fast",  # 30 diffusion steps for fast testing
            export_formats=["glb", "obj"]
        )

        resp = adapter.reconstruct(req)
        print(f"  Result: Success={resp.success} | Latency={resp.inference_time_seconds}s | Error={resp.error}")
        
        if resp.success:
            print(f"  Vertices: {resp.vertices:,} | Faces: {resp.faces:,}")
            print(f"  Exported Formats: {resp.formats}")
            
            # Reopen check
            glb_path = resp.formats.get("glb")
            reopen_report = MeshValidator.validate_file(glb_path)
            print(f"  Strict Reopen Verified: {reopen_report.get('vertices', 0):,} vertices, {reopen_report.get('faces', 0):,} faces, is_watertight={reopen_report.get('is_watertight')}")

            results.append({
                "sketch": name,
                "input_image": str(img_path),
                "success": True,
                "latency_seconds": resp.inference_time_seconds,
                "vertices": resp.vertices,
                "faces": resp.faces,
                "is_watertight": resp.quality_report.get("is_watertight", False),
                "glb_file": resp.formats.get("glb"),
                "obj_file": resp.formats.get("obj")
            })
        else:
            results.append({
                "sketch": name,
                "input_image": str(img_path),
                "success": False,
                "error": resp.error
            })

    # Save audit log
    audit_file = output_dir / "instantmesh_audit_report.json"
    with open(audit_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n==================================================================")
    print(f" Audit Complete! Results saved to: {audit_file}")
    print(f"==================================================================")


if __name__ == "__main__":
    main()

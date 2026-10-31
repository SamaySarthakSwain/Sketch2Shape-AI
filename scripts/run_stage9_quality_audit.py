"""
Stage 9 Benchmark & Asset Quality Audit Script
Executes Phase 1 (Audit), Phase 2 (Multi-View Consistency),
Phase 4 (Refinement), and Phase 7 (Before/After Comparison) across all 6 benchmark assets.
"""

import os
import sys
import json
import time
from pathlib import Path
import trimesh

# Add backend to PYTHONPATH
BASE_DIR = Path(r"C:\Sketch2Shape-AI")
BACKEND_DIR = BASE_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.geometry_intelligence import (
    MeshAnalyzer,
    MeshRefiner,
    GeometryReportFormatter,
)


def run_audit():
    print("==================================================================")
    print(" STAGE 9: 3D ASSET QUALITY AUDIT & MULTI-VIEW CONSISTENCY ENGINE  ")
    print("==================================================================")

    audit_dir = BASE_DIR / "outputs" / "reconstructions" / "phase1_audit"
    multiview_dir = BASE_DIR / "outputs" / "geometry_analysis" / "multiview"
    refined_dir = BASE_DIR / "outputs" / "geometry_analysis" / "refined"
    experiments_dir = BASE_DIR / "experiments" / "geometry"

    multiview_dir.mkdir(parents=True, exist_ok=True)
    refined_dir.mkdir(parents=True, exist_ok=True)
    experiments_dir.mkdir(parents=True, exist_ok=True)

    analyzer = MeshAnalyzer(multiview_output_dir=multiview_dir)

    # Assets to audit
    assets = [
        # InstantMesh reconstructions
        {
            "id": "instantmesh_chair",
            "name": "InstantMesh Chair",
            "category": "chair",
            "mesh_path": audit_dir / "instantmesh_quickdraw_chair_normalized.glb",
            "sketch_path": BASE_DIR / "frontend" / "public" / "examples" / "quickdraw_chair_normalized.png",
        },
        {
            "id": "instantmesh_car",
            "name": "InstantMesh Car (Low-Poly Investigation)",
            "category": "car",
            "mesh_path": audit_dir / "instantmesh_quickdraw_car_normalized.glb",
            "sketch_path": BASE_DIR / "frontend" / "public" / "examples" / "quickdraw_car_normalized.png",
        },
        {
            "id": "instantmesh_airplane",
            "name": "InstantMesh Airplane",
            "category": "airplane",
            "mesh_path": audit_dir / "instantmesh_quickdraw_airplane_normalized.glb",
            "sketch_path": BASE_DIR / "frontend" / "public" / "examples" / "quickdraw_airplane_normalized.png",
        },
        # Procedural reconstructions
        {
            "id": "procedural_chair",
            "name": "Procedural Chair",
            "category": "chair",
            "mesh_path": audit_dir / "procedural_quickdraw_chair_normalized_preprocessed.glb",
            "sketch_path": BASE_DIR / "frontend" / "public" / "examples" / "quickdraw_chair_normalized.png",
        },
        {
            "id": "procedural_car",
            "name": "Procedural Car",
            "category": "car",
            "mesh_path": audit_dir / "procedural_quickdraw_car_normalized_preprocessed.glb",
            "sketch_path": BASE_DIR / "frontend" / "public" / "examples" / "quickdraw_car_normalized.png",
        },
        {
            "id": "procedural_airplane",
            "name": "Procedural Airplane",
            "category": "airplane",
            "mesh_path": audit_dir / "procedural_quickdraw_airplane_normalized_preprocessed.glb",
            "sketch_path": BASE_DIR / "frontend" / "public" / "examples" / "quickdraw_airplane_normalized.png",
        },
        {
            "id": "procedural_cup",
            "name": "Procedural Cup",
            "category": "cup",
            "mesh_path": audit_dir / "procedural_quickdraw_cup_normalized_preprocessed.glb",
            "sketch_path": BASE_DIR / "frontend" / "public" / "examples" / "quickdraw_cup_normalized.png",
        },
        {
            "id": "procedural_bicycle",
            "name": "Procedural Bicycle",
            "category": "bicycle",
            "mesh_path": audit_dir / "procedural_quickdraw_bicycle_normalized_preprocessed.glb",
            "sketch_path": BASE_DIR / "frontend" / "public" / "examples" / "quickdraw_bicycle_normalized.png",
        },
        {
            "id": "procedural_apple",
            "name": "Procedural Apple",
            "category": "apple",
            "mesh_path": audit_dir / "procedural_quickdraw_apple_normalized_preprocessed.glb",
            "sketch_path": BASE_DIR / "frontend" / "public" / "examples" / "quickdraw_apple_normalized.png",
        },
    ]

    all_reports = {}
    all_comparisons = {}

    for item in assets:
        asset_id = item["id"]
        mesh_path = item["mesh_path"]
        sketch_path = item["sketch_path"]

        if not mesh_path.exists():
            print(f"Skipping {asset_id}: File not found ({mesh_path})")
            continue

        print(f"\n=======================================================")
        print(f" Auditing Asset: {item['name']} ({asset_id})")
        print(f" Source: {mesh_path.name}")
        print(f"=======================================================")

        # Phase 1 & 2: Complete Audit & Multi-View Rendering
        print(f"[{asset_id}] Analyzing topology, geometry, surface, texture, and multi-view consistency...")
        report = analyzer.analyze(
            mesh_input=str(mesh_path),
            asset_id=asset_id,
            run_multiview=True,
            sketch_path=str(sketch_path) if sketch_path.exists() else None,
        )

        all_reports[asset_id] = GeometryReportFormatter.to_dict(report)
        print(f"  Overall Score: {report.quality.overall_score:.1f} / 100")
        print(f"  Vertices: {report.topology.vertex_count:,} | Faces: {report.topology.face_count:,} | Watertight: {report.topology.is_watertight}")
        print(f"  Euler Chi: {report.topology.euler_characteristic} | Components: {report.topology.connected_components}")
        if report.multiview:
            print(f"  Front Sketch IoU: {report.multiview.front_sketch_iou} | Cross-View Continuity: {report.multiview.cross_view_continuity_score:.2f}")

        # Phase 4 & 7: Refinement & Before/After Comparison
        print(f"[{asset_id}] Applying automated safe refinement (Balanced Preset)...")
        refined_mesh, comparison = MeshRefiner.refine(
            mesh_input=str(mesh_path),
            preset="balanced",
            asset_id=asset_id,
        )

        # Export refined meshes
        refined_glb = refined_dir / f"{asset_id}_refined.glb"
        refined_obj = refined_dir / f"{asset_id}_refined.obj"
        refined_mesh.export(str(refined_glb))
        refined_mesh.export(str(refined_obj))

        comparison.original_file_size_bytes = mesh_path.stat().st_size
        comparison.refined_file_size_bytes = refined_glb.stat().st_size
        all_comparisons[asset_id] = comparison.dict()

        print(f"  Refined Verts: {comparison.original_vertices} -> {comparison.refined_vertices} ({comparison.vertex_delta:+d})")
        print(f"  Refined Faces: {comparison.original_faces} -> {comparison.refined_faces} ({comparison.face_delta:+d})")
        print(f"  Refined Watertight: {comparison.refined_watertight}")
        print(f"  Refined File Size: {comparison.original_file_size_bytes:,} -> {comparison.refined_file_size_bytes:,} bytes")
        print(f"  Degraded: {comparison.is_degraded}")

    # Save comprehensive benchmark JSON
    output_benchmark = {
        "benchmark_timestamp": time.time(),
        "total_assets_audited": len(all_reports),
        "reports": all_reports,
        "comparisons": all_comparisons,
    }

    out_json_path = experiments_dir / "quality_comparison.json"
    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(output_benchmark, f, indent=2)

    print(f"\n=======================================================")
    print(f" Audit complete! Benchmark saved to: {out_json_path}")
    print(f" Multi-view images saved to: {multiview_dir}")
    print(f" Refined models saved to: {refined_dir}")
    print(f"=======================================================")


if __name__ == "__main__":
    run_audit()

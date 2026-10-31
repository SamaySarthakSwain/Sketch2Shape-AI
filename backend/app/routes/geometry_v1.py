"""
Sketch2Shape AI - Geometry Intelligence & Refinement API v1
FastAPI endpoints for 3D quality audit, multi-view consistency,
automated mesh refinement, and before/after comparisons.
"""

import os
import sys
import time
import uuid
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import trimesh
from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form, Query
from fastapi.responses import FileResponse

from app.geometry_intelligence import (
    MeshAnalyzer,
    MeshRefiner,
    GeometryReportFormatter,
)

router = APIRouter(prefix="/api/v1/geometry", tags=["Geometry Intelligence & Refinement"])

BASE_DIR = Path(r"C:\Sketch2Shape-AI")
OUTPUTS_DIR = BASE_DIR / "outputs" / "geometry_analysis"
REFINED_DIR = OUTPUTS_DIR / "refined"
MULTIVIEW_DIR = OUTPUTS_DIR / "multiview"
EXPERIMENTS_DIR = BASE_DIR / "experiments" / "geometry"

REFINED_DIR.mkdir(parents=True, exist_ok=True)
MULTIVIEW_DIR.mkdir(parents=True, exist_ok=True)

# In-memory stores with fallback to experiments/geometry/quality_comparison.json
GEOMETRY_REPORTS: Dict[str, Dict[str, Any]] = {}
GEOMETRY_COMPARISONS: Dict[str, Dict[str, Any]] = {}

# Pre-populate from disk if exists
try:
    comparison_file = EXPERIMENTS_DIR / "quality_comparison.json"
    if comparison_file.exists():
        with open(comparison_file, "r", encoding="utf-8") as f:
            disk_data = json.load(f)
            GEOMETRY_REPORTS.update(disk_data.get("reports", {}))
            GEOMETRY_COMPARISONS.update(disk_data.get("comparisons", {}))
except Exception:
    pass

analyzer = MeshAnalyzer(multiview_output_dir=MULTIVIEW_DIR)


class AnalyzeRequest(BaseModel):
    mesh_path: Optional[str] = None
    asset_id: Optional[str] = None
    run_multiview: bool = False
    sketch_path: Optional[str] = None


class RefineRequest(BaseModel):
    mesh_path: Optional[str] = None
    asset_id: Optional[str] = None
    preset: str = Field(default="balanced", description="fast, balanced, or high")
    remove_isolated_shards: bool = True
    export_formats: List[str] = Field(default=["glb", "obj"])


@router.post("/analyze")
def analyze_mesh(payload: AnalyzeRequest):
    """
    Executes complete geometry audit, topological metric calculation,
    defect detection, and transparent quality scoring.
    """
    asset_id = payload.asset_id or str(uuid.uuid4())[:8]

    # Resolve mesh path
    target_path = None
    if payload.mesh_path and Path(payload.mesh_path).exists():
        target_path = payload.mesh_path
    elif payload.asset_id:
        # Check known directories
        candidates = [
            REFINED_DIR / f"{payload.asset_id}_refined.glb",
            BASE_DIR / "outputs" / "reconstructions" / "phase1_audit" / f"{payload.asset_id}.glb",
            BASE_DIR / "frontend" / "public" / "models" / f"{payload.asset_id}.glb",
        ]
        for c in candidates:
            if c.exists():
                target_path = str(c)
                break

    if not target_path:
        raise HTTPException(status_code=400, detail="Valid 'mesh_path' or existing 'asset_id' must be provided.")

    try:
        report = analyzer.analyze(
            mesh_input=target_path,
            asset_id=asset_id,
            run_multiview=payload.run_multiview,
            sketch_path=payload.sketch_path,
        )
        report_dict = GeometryReportFormatter.to_dict(report)
        GEOMETRY_REPORTS[asset_id] = report_dict
        return report_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Geometry analysis failed: {str(e)}")


@router.post("/refine")
def refine_mesh(payload: RefineRequest):
    """
    Applies safe automated mesh refinement: Taubin volume-preserving smoothing,
    quadric decimation, normal reorientation, and shard pruning.
    """
    asset_id = payload.asset_id or str(uuid.uuid4())[:8]

    target_path = None
    if payload.mesh_path and Path(payload.mesh_path).exists():
        target_path = payload.mesh_path
    elif payload.asset_id:
        candidates = [
            BASE_DIR / "outputs" / "reconstructions" / "phase1_audit" / f"{payload.asset_id}.glb",
            BASE_DIR / "frontend" / "public" / "models" / f"{payload.asset_id}.glb",
            REFINED_DIR / f"{payload.asset_id}_refined.glb",
        ]
        for c in candidates:
            if c.exists():
                target_path = str(c)
                break

    if not target_path:
        raise HTTPException(status_code=400, detail="Valid 'mesh_path' or existing 'asset_id' must be provided.")

    try:
        refined_mesh, comparison = MeshRefiner.refine(
            mesh_input=target_path,
            preset=payload.preset,
            remove_isolated_shards=payload.remove_isolated_shards,
            asset_id=asset_id,
        )

        downloads = {}
        for fmt in payload.export_formats:
            fmt_clean = fmt.lower().strip()
            out_file = REFINED_DIR / f"{asset_id}_refined.{fmt_clean}"
            refined_mesh.export(str(out_file))
            downloads[fmt_clean] = f"/api/v1/geometry/download/{asset_id}/{fmt_clean}"

        # Record file sizes
        comparison.original_file_size_bytes = Path(target_path).stat().st_size
        ref_glb = REFINED_DIR / f"{asset_id}_refined.glb"
        if ref_glb.exists():
            comparison.refined_file_size_bytes = ref_glb.stat().st_size

        comp_dict = comparison.dict() if hasattr(comparison, "dict") else comparison.model_dump()
        GEOMETRY_COMPARISONS[asset_id] = comp_dict

        return {
            "asset_id": asset_id,
            "status": "completed",
            "preset": payload.preset,
            "comparison": comp_dict,
            "downloads": downloads,
            "refined_mesh_metrics": {
                "vertices": len(refined_mesh.vertices),
                "faces": len(refined_mesh.faces),
                "is_watertight": bool(getattr(refined_mesh, "is_watertight", False)),
                "surface_area": round(float(refined_mesh.area), 4),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Refinement failed: {str(e)}")


@router.get("/report/{asset_id}")
def get_geometry_report(asset_id: str):
    """Retrieves cached geometry intelligence report for given asset."""
    if asset_id in GEOMETRY_REPORTS:
        return GEOMETRY_REPORTS[asset_id]
    raise HTTPException(status_code=404, detail=f"No geometry report found for asset '{asset_id}'.")


@router.get("/compare/{asset_id}")
def get_geometry_comparison(asset_id: str):
    """Retrieves before-and-after refinement comparison for given asset."""
    if asset_id in GEOMETRY_COMPARISONS:
        return GEOMETRY_COMPARISONS[asset_id]
    raise HTTPException(status_code=404, detail=f"No refinement comparison found for asset '{asset_id}'.")


@router.get("/download/{asset_id}/{format}")
def download_refined_mesh(asset_id: str, format: str):
    """Downloads refined GLB or OBJ mesh asset."""
    fmt = format.lower().strip()
    target = REFINED_DIR / f"{asset_id}_refined.{fmt}"
    if not target.exists():
        # Check without _refined suffix
        target = REFINED_DIR / f"{asset_id}.{fmt}"
    if not target.exists():
        raise HTTPException(status_code=404, detail=f"Refined asset file '{target.name}' not found.")

    media_type = "model/gltf-binary" if fmt == "glb" else "text/plain"
    return FileResponse(
        path=str(target),
        filename=f"sketch2shape_{asset_id}_refined.{fmt}",
        media_type=media_type,
    )

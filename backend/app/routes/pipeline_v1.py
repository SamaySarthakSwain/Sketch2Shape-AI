"""
Pipeline V1 Endpoints
Async job-based and synchronous 11-stage sketch-to-3D pipeline execution API.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field

from app.orchestration import (
    job_manager,
    PipelineConfig,
    PipelineJob,
    PipelineStage
)

router = APIRouter(prefix="/api/v1/pipeline", tags=["Pipeline V1"])


class PipelineGenerateRequest(BaseModel):
    image_b64: Optional[str] = Field(default=None, description="Base64 encoded PNG/JPEG sketch")
    image_path: Optional[str] = Field(default=None, description="Server-side image file path")
    prompt: Optional[str] = Field(default=None, description="Natural language prompt for Text-to-3D mode")
    preferred_model: str = Field(default="auto", description="auto, instantmesh, procedural, meshy, tripo, rodin")
    quality_preset: str = Field(default="balanced", description="fast, balanced, high, ultra_fast")
    preprocess_first: bool = Field(default=True, description="Whether to run OpenCV preprocessing")
    auto_refine: bool = Field(default=True, description="Whether to run mesh refinement")
    refine_preset: str = Field(default="balanced", description="fast, balanced, high")
    export_formats: List[str] = Field(default=["glb", "obj", "stl", "3mf", "usdz", "gltf"], description="Mesh formats to export")
    allow_fallback: bool = True
    category_override: Optional[str] = Field(default=None, description="Override predicted category")
    visual_style: str = Field(default="realistic", description="realistic, stylized, cartoon, low_poly, product_render, futuristic, metallic, matte, glossy")
    material_override: Optional[str] = Field(default=None, description="Specific material from library")
    enable_pbr: bool = Field(default=True, description="Synthesize PBR textures")
    enable_packaging: bool = Field(default=True, description="Generate full ZIP asset bundle")
    cloud_provider: Optional[str] = Field(default="auto", description="auto, meshy, tripo, rodin, local")
    async_execution: bool = Field(default=True, description="If true, returns immediately with job_id")
    primary_color_rgb: Optional[List[int]] = None
    secondary_color_rgb: Optional[List[int]] = None



def _format_job_response(job: PipelineJob) -> Dict[str, Any]:
    job_dict = job.dict() if hasattr(job, "dict") else job.model_dump()
    
    # Enrich artifacts with web URLs if files exist under backend/data/jobs
    web_artifacts = {}
    for key, path_str in job.artifacts.items():
        if isinstance(path_str, str):
            p = Path(path_str)
            web_artifacts[key] = path_str
            # Check if relative or absolute under backend/data/jobs
            norm_str = str(p).replace("\\", "/")
            if "backend/data/jobs/" in norm_str:
                rel = norm_str.split("backend/data/jobs/")[1]
                web_artifacts[f"{key}_url"] = f"/static/jobs/{rel}"
            elif "exports/" in norm_str:
                rel = norm_str.split("exports/")[1]
                web_artifacts[f"{key}_url"] = f"/static/exports/{rel}"

    job_dict["web_artifacts"] = web_artifacts
    return job_dict


@router.post("/generate", summary="Trigger unified sketch-to-3D or prompt-to-3D reconstruction pipeline")
async def generate_3d_pipeline(req: PipelineGenerateRequest):
    if not req.image_b64 and not req.image_path and not req.prompt:
        raise HTTPException(status_code=400, detail="Must provide either 'image_b64', 'image_path', or 'prompt'")

    config = PipelineConfig(
        image_b64=req.image_b64,
        image_path=req.image_path,
        prompt=req.prompt,
        preferred_model=req.preferred_model,
        quality_preset=req.quality_preset,
        preprocess_first=req.preprocess_first,
        auto_refine=req.auto_refine,
        refine_preset=req.refine_preset,
        export_formats=req.export_formats,
        allow_fallback=req.allow_fallback,
        category_override=req.category_override,
        visual_style=req.visual_style,
        material_override=req.material_override,
        enable_pbr=req.enable_pbr,
        enable_packaging=req.enable_packaging,
        cloud_provider=req.cloud_provider,
        primary_color_rgb=req.primary_color_rgb,
        secondary_color_rgb=req.secondary_color_rgb,
    )

    if req.async_execution:
        job = job_manager.submit_job(config)
        return {
            "status": "queued",
            "job_id": job.job_id,
            "created_at": job.created_at,
            "current_stage": job.current_stage,
            "status_url": f"/api/v1/pipeline/status/{job.job_id}",
            "result_url": f"/api/v1/pipeline/result/{job.job_id}",
            "cancel_url": f"/api/v1/pipeline/cancel/{job.job_id}",
        }
    else:
        # Synchronous execution
        job = job_manager.run_sync(config)
        return _format_job_response(job)


@router.get("/status/{job_id}", summary="Check status and chronological stage history of a pipeline job")
async def get_pipeline_status(job_id: str):
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    return {
        "job_id": job.job_id,
        "status": job.status,
        "current_stage": job.current_stage,
        "stage_history": [s.dict() if hasattr(s, "dict") else s.model_dump() for s in job.stage_history],
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "total_duration_seconds": job.total_duration_seconds,
        "peak_vram_mb": job.peak_vram_mb,
        "is_cancelled": job.is_cancelled,
        "error": job.error,
    }


@router.get("/result/{job_id}", summary="Retrieve full result, artifacts, and geometry analysis of a pipeline job")
async def get_pipeline_result(job_id: str):
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    return _format_job_response(job)


@router.post("/cancel/{job_id}", summary="Cancel an in-progress or queued pipeline job")
async def cancel_pipeline_job(job_id: str):
    success = job_manager.cancel_job(job_id)
    if not success:
        job = job_manager.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
        return {"job_id": job_id, "status": job.status, "message": "Cannot cancel completed or failed job"}

    return {"job_id": job_id, "status": "cancelling", "message": "Cancellation flag issued"}


@router.get("/jobs", summary="List recent pipeline jobs")
async def list_pipeline_jobs(limit: int = Query(default=20, ge=1, le=100)):
    jobs = job_manager.list_jobs(limit=limit)
    return {
        "count": len(jobs),
        "jobs": [
            {
                "job_id": j.job_id,
                "status": j.status,
                "current_stage": j.current_stage,
                "created_at": j.created_at,
                "total_duration_seconds": j.total_duration_seconds,
                "peak_vram_mb": j.peak_vram_mb,
                "error": j.error,
            }
            for j in jobs
        ]
    }


# ==============================================================================
# STAGE 11: PROVIDERS, MATERIALS, STYLES, & RETEXTURING ENDPOINTS
# ==============================================================================

@router.get("/providers", summary="Get status and availability of external AI 3D providers & local engines")
async def get_providers_status():
    from app.reconstruction.providers import provider_registry
    from app.reconstruction.model_registry import model_registry

    cloud_status = provider_registry.get_provider_status()
    local_models = model_registry.list_models()

    return {
        "cloud_providers": cloud_status,
        "available_cloud_count": len(provider_registry.list_available_providers()),
        "local_engines": [
            {
                "name": m.name,
                "display_name": m.display_name,
                "category": m.category,
                "vram_required_gb": m.vram_required_gb,
                "is_available": m.is_available,
                "status_message": m.status_message
            }
            for m in local_models
        ],
        "credentials_required": {
            "meshy": "MESHY_API_KEY",
            "tripo": "TRIPO_API_KEY",
            "rodin": "RODIN_API_KEY"
        }
    }


@router.get("/materials", summary="List supported PBR materials and category recommendations")
async def list_materials(category: Optional[str] = None):
    from app.texturing import PBRMaterialLibrary, MATERIALS_DB, CATEGORY_MATERIAL_MAPPING

    all_materials = [
        {
            "id": mat.name,
            "display_name": mat.display_name,
            "roughness": mat.roughness,
            "metallic": mat.metallic,
            "pattern_type": mat.pattern_type,
            "base_color_rgb": mat.base_color_rgb
        }
        for mat in MATERIALS_DB.values()
    ]

    recommended = []
    if category:
        recommended = PBRMaterialLibrary.list_options_for_category(category)

    return {
        "total_materials": len(all_materials),
        "materials": all_materials,
        "recommended_for_category": recommended,
        "categories_mapped": list(CATEGORY_MATERIAL_MAPPING.keys())
    }


@router.get("/styles", summary="List supported visual rendering and aesthetic styles")
async def list_visual_styles():
    from app.texturing import VisualStyle, STYLE_MODIFIERS

    return {
        "styles": [
            {
                "id": s.value,
                "name": STYLE_MODIFIERS[s.value].name,
                "roughness_multiplier": STYLE_MODIFIERS[s.value].roughness_multiplier,
                "metallic_multiplier": STYLE_MODIFIERS[s.value].metallic_multiplier,
                "saturation_multiplier": STYLE_MODIFIERS[s.value].saturation_multiplier
            }
            for s in VisualStyle
        ]
    }


class RetextureRequest(BaseModel):
    visual_style: str = Field(default="realistic", description="Visual aesthetic style")
    material_override: Optional[str] = Field(default=None, description="Specific material from library")
    texture_resolution: int = Field(default=1024, description="Resolution of baked PBR maps")


@router.post("/retexture/{job_id}", summary="Dynamically re-bake PBR materials and textures on existing 3D mesh")
async def retexture_pipeline_job(job_id: str, req: RetextureRequest):
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    target_mesh = job.artifacts.get("refined_glb") or job.artifacts.get("final_mesh") or job.artifacts.get("primary_mesh")
    if not target_mesh or not Path(target_mesh).exists():
        raise HTTPException(status_code=400, detail="Job does not have an accessible 3D mesh to retexture")

    from app.texturing import PBRBaker, PBRMaterialLibrary
    import trimesh

    category = job.metrics.get("predicted_category", "chair")
    job_dir = Path(target_mesh).parent.parent

    try:
        mesh = trimesh.load(target_mesh, force="mesh")
        textured_dir = job_dir / "textured"
        textured_dir.mkdir(parents=True, exist_ok=True)

        textured_mesh, tex_paths = PBRBaker.apply_pbr_textures(
            mesh=mesh,
            category=category,
            style=req.visual_style,
            material_override=req.material_override,
            texture_resolution=req.texture_resolution,
            output_dir=str(textured_dir)
        )

        pbr_glb_path = textured_dir / f"{job_id}_{req.visual_style}_pbr.glb"
        glb_bytes = textured_mesh.export(file_type="glb")
        with open(pbr_glb_path, "wb") as f:
            f.write(glb_bytes)

        # Update job artifacts
        job.artifacts["pbr_glb"] = str(pbr_glb_path)
        job.artifacts["final_mesh"] = str(pbr_glb_path)
        for k, v in tex_paths.items():
            job.artifacts[f"texture_{k}"] = v

        mat_def = PBRMaterialLibrary.get_material_for_category(category, req.visual_style, req.material_override)
        job.metrics["material"] = {
            "material_name": mat_def.name,
            "display_name": mat_def.display_name,
            "roughness": mat_def.roughness,
            "metallic": mat_def.metallic,
            "visual_style": req.visual_style
        }

        return _format_job_response(job)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retexturing failed: {str(e)}")


@router.get("/download/bundle/{job_id}", summary="Download complete multi-format 3D asset distribution bundle (.zip)")
async def download_asset_bundle(job_id: str):
    from fastapi.responses import FileResponse

    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    zip_path = job.artifacts.get("bundle_zip")
    if not zip_path or not Path(zip_path).exists():
        # Check standard location
        candidate = Path("backend/data/jobs") / job_id / f"{job_id}_bundle.zip"
        if candidate.exists():
            zip_path = str(candidate)
        else:
            raise HTTPException(status_code=404, detail="Distribution package (.zip) not generated for this job")

    return FileResponse(
        path=zip_path,
        media_type="application/zip",
        filename=f"sketch2shape_{job_id}_bundle.zip"
    )


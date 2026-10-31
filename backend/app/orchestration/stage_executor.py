"""
Pipeline Stage Executor Module
Coordinates each discrete stage of the sketch-to-3D pipeline with
typed return values, hardware monitoring, and intelligent quality-based fallback.
"""

import os
import sys
import time
import base64
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
import numpy as np
from PIL import Image
import trimesh

from app.preprocessing.preprocessing_pipeline import SketchPreprocessingPipeline
from app.preprocessing.image_loader import ImageLoader
from app.sketch_intelligence.classifier import SketchIntelligenceEngine
from app.reconstruction.model_registry import model_registry
from app.reconstruction.model_selector import ModelSelector
from app.reconstruction.reconstruction_config import ReconstructionRequest, ReconstructionResponse
from app.reconstruction.mesh_validation import MeshValidator
from app.reconstruction.category_templates import CategoryGeometryTemplates
from app.reconstruction.providers import provider_registry, ProviderTaskStatus
from app.texturing import PBRBaker, PBRMaterialLibrary, VisualStyle
from app.packaging import MultiFormatExporter, AssetPackager, PrintabilityAnalyzer
from app.geometry_intelligence import MeshAnalyzer, MeshRefiner, GeometryReportFormatter
from app.sketch_intelligence.gemini_vision_analyzer import gemini_vision_analyzer

from .pipeline_state import PipelineStage, StageExecutionRecord
from .execution_logger import ExecutionLogger
from .error_handler import PipelineException


class StageExecutor:
    def __init__(self):
        self.preprocessing_pipeline = SketchPreprocessingPipeline(target_size=512)
        self.intelligence_engine = SketchIntelligenceEngine()
        self.geometry_analyzer = MeshAnalyzer()

    # -------------------------------------------------------------
    # 1. INPUT VALIDATION
    # -------------------------------------------------------------
    def validate_input(
        self,
        image_path: Optional[str],
        image_b64: Optional[str],
        job_dir: Path,
        prompt: Optional[str] = None
    ) -> str:
        """Validates sketch file existence, decodes base64 payload, or synthesizes reference canvas for prompt."""
        if image_path and Path(image_path).exists():
            # Validate can be opened by PIL
            try:
                img = Image.open(image_path)
                img.verify()
                return str(image_path)
            except Exception as e:
                raise PipelineException(PipelineStage.VALIDATING_INPUT, f"Invalid or corrupt image file: {e}")

        elif image_b64:
            try:
                b64_clean = image_b64
                if "," in b64_clean:
                    b64_clean = b64_clean.split(",", 1)[1]
                data = base64.b64decode(b64_clean)
                target_path = job_dir / "input_sketch.png"
                with open(target_path, "wb") as f:
                    f.write(data)
                img = Image.open(target_path)
                img.verify()
                return str(target_path)
            except Exception as e:
                raise PipelineException(PipelineStage.VALIDATING_INPUT, f"Failed to decode base64 sketch: {e}")

        elif prompt and prompt.strip():
            # Prompt-to-3D mode: synthesize a clean canvas placeholder
            target_path = job_dir / "prompt_canvas.png"
            img = Image.new("RGB", (512, 512), color=(255, 255, 255))
            from PIL import ImageDraw
            draw = ImageDraw.Draw(img)
            draw.rectangle([32, 32, 480, 480], outline=(100, 100, 100), width=4)
            img.save(str(target_path))
            return str(target_path)

        raise PipelineException(PipelineStage.VALIDATING_INPUT, "Neither 'image_path', 'image_b64', nor 'prompt' provided.")

    # -------------------------------------------------------------
    # 2. OPENCV PREPROCESSING
    # -------------------------------------------------------------
    def execute_preprocessing(self, input_image_path: str, job_dir: Path, enabled: bool = True) -> Tuple[str, Dict[str, Any]]:
        if not enabled:
            return input_image_path, {"status": "bypassed"}

        try:
            variants, report = self.preprocessing_pipeline.process(input_image_path)
            prep_dir = job_dir / "preprocessed"
            prep_dir.mkdir(parents=True, exist_ok=True)
            norm_path = prep_dir / "normalized_sketch.png"

            norm = variants.get("normalized")
            if isinstance(norm, np.ndarray):
                Image.fromarray(norm).save(str(norm_path))
            elif hasattr(norm, "save"):
                norm.save(str(norm_path))
            else:
                Image.open(input_image_path).save(str(norm_path))

            if hasattr(report, "to_dict"):
                report_dict = report.to_dict()
            elif hasattr(report, "dict"):
                report_dict = report.dict()
            elif hasattr(report, "model_dump"):
                report_dict = report.model_dump()
            else:
                report_dict = {"status": "success"}
            return str(norm_path), report_dict
        except Exception as e:
            print(f"[StageExecutor] Preprocessing warning: {e}. Falling back to raw image.")
            return input_image_path, {"error": str(e), "status": "fallback_raw"}

    # -------------------------------------------------------------
    # 3. SKETCH INTELLIGENCE & SEMANTIC ANALYSIS
    # -------------------------------------------------------------
    def execute_sketch_intelligence(
        self,
        image_path: str,
        category_override: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        if prompt and prompt.strip():
            try:
                ai_data = gemini_vision_analyzer.analyze_prompt(prompt.strip())
                cat = category_override or ai_data.get("category", "object")
                return {
                    "predicted_category": cat,
                    "predicted_object": ai_data.get("predicted_object", prompt.strip().title()),
                    "top_confidence": 0.96,
                    "is_colorful": ai_data.get("is_colorful", True),
                    "primary_color_rgb": ai_data.get("primary_color_rgb", [220, 38, 38]),
                    "primary_color_hex": ai_data.get("primary_color_hex", "#DC2626"),
                    "secondary_color_rgb": ai_data.get("secondary_color_rgb", [30, 41, 59]),
                    "secondary_color_hex": ai_data.get("secondary_color_hex", "#1E293B"),
                    "dominant_colors": ai_data.get("dominant_colors", []),
                    "semantic_description": f"Text-to-3D generation for '{prompt}'. Color palette: {ai_data.get('primary_color_hex')}.",
                    "reconstruction_hints": [f"Synthesize 3D geometry from prompt: {prompt}"],
                    "geometric_tags": ["text_to_3d_generation", "parametric_surface"],
                    "ai_vision_model": ai_data.get("ai_model_used", "gemini-2.5-flash"),
                    "prompt_3d": ai_data.get("prompt_3d", prompt)
                }
            except Exception as e:
                print(f"[StageExecutor] Prompt intelligence warning: {e}")

        try:
            intel = self.intelligence_engine.analyze(image_path)
            if category_override:
                intel["predicted_category"] = category_override
                intel["user_overridden"] = True
            return intel
        except Exception as e:
            print(f"[StageExecutor] Intelligence warning: {e}")
            cat = category_override or "unknown"
            return {
                "predicted_category": cat,
                "top_confidence": 0.5,
                "geometric_tags": [],
                "error": str(e)
            }

    # -------------------------------------------------------------
    # 4. ADAPTIVE MODEL SELECTION
    # -------------------------------------------------------------
    def select_reconstruction_model(
        self,
        user_preference: str,
        category: str,
        confidence: float,
        geometric_tags: List[str],
        quality_preset: str
    ) -> Tuple[str, str]:
        """
        Intelligently routes between InstantMesh and Procedural engines.
        Returns (primary_model, selection_reason).
        """
        pref = (user_preference or "auto").lower().strip()

        # 1. User explicitly requested a cloud provider (meshy, tripo, rodin)
        if pref in ["meshy", "tripo", "rodin"]:
            p = provider_registry.get_provider(pref)
            if p and p.is_available():
                return pref, f"User explicitly selected cloud provider '{pref}'"
            else:
                print(f"[StageExecutor] Cloud provider '{pref}' not configured. Falling back to local pipeline.")

        # 2. User explicitly selected engine
        if pref in ["trellis", "instantmesh", "procedural"]:
            return pref, f"Selected 3D reconstruction engine '{pref}'"

        # 3. Auto mode with cloud provider configured:
        # If high quality preset is requested and a cloud provider is active, use it!
        avail_cloud = provider_registry.list_available_providers()
        if pref == "auto" and avail_cloud and quality_preset == "high":
            for cand in ["meshy", "tripo", "rodin"]:
                if cand in avail_cloud:
                    return cand, f"Auto-selected cloud provider '{cand}' for high-fidelity PBR generation"

        # 4. Microsoft TRELLIS selection for high quality
        trellis_adapter = model_registry.get_model("trellis")
        if trellis_adapter and trellis_adapter.is_available() and quality_preset == "high":
            return "trellis", f"Microsoft TRELLIS (Structured 3D Latents) selected for high-fidelity 3D reconstruction"

        # 4. Local execution routing
        has_procedural_template = CategoryGeometryTemplates.is_category_supported(category)

        # Categories with dedicated procedural templates:
        if has_procedural_template and quality_preset != "high":
            return "procedural", f"Category '{category}' routed to dedicated watertight parametric template"

        # Fast preset for any category routes to procedural engine
        if quality_preset in ["fast", "ultra_fast"]:
            return "procedural", f"Fast preset routed to procedural engine for '{category}'"

        # Complex organic categories or high quality preset: route to InstantMesh neural triplane
        im_adapter = model_registry.get_model("instantmesh")
        if im_adapter and im_adapter.is_available():
            return "instantmesh", f"InstantMesh neural triplane selected for '{category}' ({quality_preset} preset)"

        if has_procedural_template:
            return "procedural", f"Procedural template selected for '{category}'"

        return "procedural", "Default fallback to procedural engine"

    # -------------------------------------------------------------
    # 5. 3D RECONSTRUCTION WITH QUALITY-BASED FALLBACK
    # -------------------------------------------------------------
    def execute_reconstruction(
        self,
        primary_model: str,
        image_path: str,
        job_dir: Path,
        quality_preset: str,
        export_formats: List[str],
        semantic_metadata: Dict[str, Any],
        allow_fallback: bool = True
    ) -> Tuple[ReconstructionResponse, Dict[str, Any]]:
        """
        Executes reconstruction with intelligent quality evaluation and fallback.
        Supports both external cloud providers (Meshy, Tripo, Rodin) and local engines.
        """
        ExecutionLogger.cleanup_gpu_memory()

        # Check if primary_model is an external cloud provider
        if primary_model in ["meshy", "tripo", "rodin"]:
            cloud_p = provider_registry.get_provider(primary_model)
            if cloud_p and cloud_p.is_available():
                cat = semantic_metadata.get("predicted_category", "object")
                print(f"[StageExecutor] Submitting task to cloud provider '{primary_model}'...")
                task = cloud_p.submit_task(
                    image_path=image_path,
                    prompt=f"3D asset of a {cat}",
                    category=cat,
                    enable_pbr=True
                )
                if task.status != ProviderTaskStatus.FAILED and task.task_id:
                    completed_task = cloud_p.wait_for_completion(task.task_id)
                    if completed_task.status == ProviderTaskStatus.SUCCEEDED and completed_task.download_url_glb:
                        models_dir = job_dir / "models"
                        downloaded = cloud_p.download_and_verify_result(completed_task, str(models_dir))
                        if downloaded.status == ProviderTaskStatus.SUCCEEDED and downloaded.local_glb_path:
                            m = trimesh.load(downloaded.local_glb_path)
                            v_count = len(m.vertices) if hasattr(m, "vertices") else sum(len(g.vertices) for g in m.geometry.values() if hasattr(g, "vertices"))
                            f_count = len(m.faces) if hasattr(m, "faces") else sum(len(g.faces) for g in m.geometry.values() if hasattr(g, "faces"))
                            resp = ReconstructionResponse(
                                success=True,
                                model_name=primary_model,
                                mesh_path=downloaded.local_glb_path,
                                inference_time_seconds=downloaded.execution_time_seconds,
                                vertices=v_count,
                                faces=f_count,
                                formats={"glb": downloaded.local_glb_path}
                            )
                            return resp, {
                                "primary_model": primary_model,
                                "primary_success": True,
                                "fallback_triggered": False,
                                "cloud_task_id": downloaded.task_id
                            }
                print(f"[StageExecutor] Cloud provider '{primary_model}' did not complete successfully. Falling back to local pipeline.")
                primary_model = "procedural"

        rec_req = ReconstructionRequest(
            image_path=image_path,
            output_dir=str(job_dir / "models"),
            model_name=primary_model,
            quality_preset=quality_preset,
            export_formats=export_formats,
            metadata=semantic_metadata,
            preprocess_first=False  # Already executed
        )

        adapter = model_registry.get_model(primary_model)
        if not adapter or not adapter.is_available():

            print(f"[StageExecutor] Model '{primary_model}' not ready. Switching to procedural.")
            adapter = model_registry.get_model("procedural")
            primary_model = "procedural"

        resp = adapter.reconstruct(rec_req)
        ExecutionLogger.cleanup_gpu_memory()

        fallback_telemetry = {
            "primary_model": primary_model,
            "primary_success": resp.success,
            "fallback_triggered": False,
            "fallback_reason": None,
        }

        # Quality Check: Rejection criteria for neural reconstruction
        is_unacceptable = False
        rejection_reason = None

        if not resp.success:
            is_unacceptable = True
            rejection_reason = resp.error or "Model execution failed"
        elif resp.vertices < 16 or resp.faces < 24:
            is_unacceptable = True
            rejection_reason = f"Severe under-tessellation ({resp.vertices} verts, {resp.faces} faces)"

        # Trigger procedural fallback if primary model output is unacceptable
        if is_unacceptable and allow_fallback and primary_model != "procedural":
            category = semantic_metadata.get("predicted_category") or semantic_metadata.get("category")
            print(f"[StageExecutor] Fallback triggered! Reason: {rejection_reason}. Executing procedural reconstruction...")
            fallback_adapter = model_registry.get_model("procedural")
            if fallback_adapter:
                fallback_resp = fallback_adapter.reconstruct(rec_req)
                if fallback_resp.success:
                    fallback_telemetry["fallback_triggered"] = True
                    fallback_telemetry["fallback_reason"] = rejection_reason
                    fallback_telemetry["original_candidate_model"] = primary_model
                    resp = fallback_resp
                    resp.model_name = f"{primary_model} -> procedural (fallback)"

        if not resp.success:
            raise PipelineException(PipelineStage.RECONSTRUCTING_3D, f"Reconstruction failed: {resp.error}")

        return resp, fallback_telemetry

    # -------------------------------------------------------------
    # 6. GEOMETRY INTELLIGENCE & QUALITY EVALUATION
    # -------------------------------------------------------------
    def execute_geometry_intelligence(
        self,
        mesh_path: str,
        asset_id: str,
        sketch_path: Optional[str] = None
    ) -> Dict[str, Any]:
        report = self.geometry_analyzer.analyze(
            mesh_input=mesh_path,
            asset_id=asset_id,
            run_multiview=True,
            sketch_path=sketch_path
        )
        return GeometryReportFormatter.to_dict(report)

    # -------------------------------------------------------------
    # 7. AUTOMATED MESH REFINEMENT
    # -------------------------------------------------------------
    def execute_refinement(
        self,
        mesh_path: str,
        preset: str,
        asset_id: str,
        job_dir: Path,
        export_formats: List[str]
    ) -> Tuple[Dict[str, Any], Dict[str, str]]:
        refined_mesh, comparison = MeshRefiner.refine(
            mesh_input=mesh_path,
            preset=preset,
            asset_id=asset_id
        )

        downloads = {}
        refined_dir = job_dir / "refined"
        refined_dir.mkdir(parents=True, exist_ok=True)

        for fmt in export_formats:
            fmt_clean = fmt.lower().strip()
            out_file = refined_dir / f"{asset_id}_refined.{fmt_clean}"
            if fmt_clean == "3mf":
                MultiFormatExporter._export_3mf(refined_mesh, str(out_file))
            elif fmt_clean == "usdz":
                MultiFormatExporter._export_usdz(refined_mesh, str(out_file), f"{asset_id}_refined")
            else:
                refined_mesh.export(str(out_file))
            downloads[fmt_clean] = str(out_file)

        comp_dict = comparison.dict() if hasattr(comparison, "dict") else comparison.model_dump()
        return comp_dict, downloads

    # -------------------------------------------------------------
    # 8. PBR TEXTURE SYNTHESIS & GLB BAKING
    # -------------------------------------------------------------
    def execute_pbr_texturing(
        self,
        mesh_path: str,
        category: str,
        style: str,
        material_override: Optional[str],
        job_dir: Path,
        color_palette: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, Dict[str, str], Dict[str, Any]]:
        """
        Synthesizes high-resolution PBR textures and bakes them into standard glTF 2.0 PBR material.
        If color_palette is provided, ensures textures reflect the exact colors of the sketch.
        Returns: (textured_glb_path, texture_paths_dict, material_metadata)
        """
        m = trimesh.load(mesh_path, force="mesh")
        textured_dir = job_dir / "textured"
        textured_dir.mkdir(parents=True, exist_ok=True)

        textured_mesh, tex_paths = PBRBaker.apply_pbr_textures(
            mesh=m,
            category=category,
            style=style,
            material_override=material_override,
            output_dir=str(textured_dir),
            color_palette=color_palette
        )

        pbr_glb_path = textured_dir / f"{job_dir.name}_pbr.glb"
        glb_bytes = textured_mesh.export(file_type="glb")
        with open(pbr_glb_path, "wb") as f:
            f.write(glb_bytes)

        mat_def = PBRMaterialLibrary.get_material_for_category(category, style, material_override)
        mat_meta = {
            "material_name": mat_def.name,
            "display_name": mat_def.display_name,
            "roughness": mat_def.roughness,
            "metallic": mat_def.metallic,
            "pattern_type": mat_def.pattern_type,
            "base_color_rgb": mat_def.base_color_rgb,
            "visual_style": style
        }

        return str(pbr_glb_path), tex_paths, mat_meta

    # -------------------------------------------------------------
    # 9. MULTI-FORMAT EXPORT & ASSET PACKAGING
    # -------------------------------------------------------------
    def execute_asset_packaging(
        self,
        mesh_path: str,
        category: str,
        job_id: str,
        job_dir: Path,
        texture_paths: Dict[str, str],
        untextured_mesh_path: Optional[str] = None,
        geometry_metrics: Optional[Dict[str, Any]] = None,
        material_metadata: Optional[Dict[str, Any]] = None,
        export_formats: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        mesh = trimesh.load(mesh_path, force="mesh")
        untextured_m = trimesh.load(untextured_mesh_path, force="mesh") if untextured_mesh_path else None

        return AssetPackager.create_package(
            mesh=mesh,
            category=category,
            job_id=job_id,
            output_dir=str(job_dir),
            base_name=job_id,
            texture_paths=texture_paths,
            untextured_mesh=untextured_m,
            geometry_metrics=geometry_metrics,
            material_metadata=material_metadata
        )


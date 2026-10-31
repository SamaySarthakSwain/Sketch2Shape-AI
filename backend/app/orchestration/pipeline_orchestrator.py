"""
Pipeline Orchestrator Module
Coordinates the end-to-end execution of the 11-stage sketch-to-3D pipeline,
handling timeouts, job cancellation, telemetry, quality-based fallback, and asset export.
"""

import os
import sys
import time
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, Callable, Union
import trimesh

from .pipeline_state import PipelineStage, StageExecutionRecord, PipelineJob
from .pipeline_config import PipelineConfig
from .stage_executor import StageExecutor
from .execution_logger import ExecutionLogger
from .error_handler import PipelineException


class PipelineOrchestrator:
    def __init__(self, base_output_dir: Optional[Union[str, Path]] = None):
        if base_output_dir is None:
            resolved_jobs = Path(__file__).resolve().parents[2] / "data" / "jobs"
            self.base_output_dir = resolved_jobs
        else:
            self.base_output_dir = Path(base_output_dir)
        self.base_output_dir.mkdir(parents=True, exist_ok=True)
        self.stage_executor = StageExecutor()

    def run_pipeline(
        self,
        config: PipelineConfig,
        job_id: Optional[str] = None,
        job_tracker: Optional[PipelineJob] = None,
        is_cancelled_check: Optional[Callable[[], bool]] = None
    ) -> PipelineJob:
        """
        Executes the full sketch-to-3D pipeline synchronously or within a worker thread.
        Updates the job_tracker (if provided) in real-time.
        """
        if not job_id:
            job_id = f"job_{uuid.uuid4().hex[:12]}"

        job_dir = self.base_output_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        if not job_tracker:
            job_tracker = PipelineJob(
                job_id=job_id,
                created_at=time.time(),
                updated_at=time.time(),
                current_stage=PipelineStage.INITIALIZED,
                status="processing",
                config=config.dict() if hasattr(config, "dict") else config.model_dump()
            )

        start_time = time.time()
        job_tracker.status = "processing"
        peak_vram = 0.0

        def check_cancellation():
            if is_cancelled_check and is_cancelled_check():
                raise PipelineException(PipelineStage.CANCELLED, "Pipeline execution was cancelled by user request.")
            if job_tracker.is_cancelled:
                raise PipelineException(PipelineStage.CANCELLED, "Pipeline execution was cancelled by user request.")

        def update_vram():
            nonlocal peak_vram
            telem = ExecutionLogger.get_hardware_telemetry()
            if telem["vram_used_mb"] > peak_vram:
                peak_vram = telem["vram_used_mb"]
            job_tracker.peak_vram_mb = peak_vram

        def record_stage_start(stage: PipelineStage, msg: str) -> StageExecutionRecord:
            check_cancellation()
            ExecutionLogger.log_stage_event(job_id, stage.value, msg)
            job_tracker.current_stage = stage
            job_tracker.updated_at = time.time()
            record = StageExecutionRecord(
                stage=stage,
                start_time=time.time(),
                message=msg
            )
            job_tracker.stage_history.append(record)
            update_vram()
            return record

        def record_stage_complete(record: StageExecutionRecord, msg: str, artifacts: Dict[str, str] = None, metadata: Dict[str, Any] = None):
            record.end_time = time.time()
            record.duration_seconds = round(record.end_time - record.start_time, 3)
            record.success = True
            record.message = msg
            if artifacts:
                record.artifacts.update(artifacts)
                job_tracker.artifacts.update(artifacts)
            if metadata:
                record.metadata.update(metadata)
            job_tracker.updated_at = time.time()
            update_vram()

        try:
            # ---------------------------------------------------------
            # Stage 1: VALIDATING_INPUT
            # ---------------------------------------------------------
            rec = record_stage_start(PipelineStage.VALIDATING_INPUT, "Validating input sketch format or text prompt")
            validated_path = self.stage_executor.validate_input(
                image_path=config.image_path,
                image_b64=config.image_b64,
                job_dir=job_dir,
                prompt=getattr(config, "prompt", None)
            )
            record_stage_complete(rec, f"Input valid: {Path(validated_path).name}", artifacts={"input_sketch": validated_path})

            # ---------------------------------------------------------
            # Stage 2: OPENCV_PREPROCESSING
            # ---------------------------------------------------------
            rec = record_stage_start(PipelineStage.OPENCV_PREPROCESSING, "Executing multi-pass OpenCV stroke normalization")
            processed_path, prep_report = self.stage_executor.execute_preprocessing(
                input_image_path=validated_path,
                job_dir=job_dir,
                enabled=config.preprocess_first and not bool(getattr(config, "prompt", None))
            )
            record_stage_complete(
                rec,
                "OpenCV preprocessing and morphological enhancement completed",
                artifacts={"normalized_sketch": processed_path},
                metadata={"preprocessing_metrics": prep_report}
            )

            # ---------------------------------------------------------
            # Stage 3: SKETCH_INTELLIGENCE & COLOR REASONING
            # ---------------------------------------------------------
            rec = record_stage_start(PipelineStage.SKETCH_INTELLIGENCE, "Predicting object identity, semantics & extracting color palette")
            intelligence = self.stage_executor.execute_sketch_intelligence(
                image_path=processed_path,
                category_override=config.category_override,
                prompt=getattr(config, "prompt", None)
            )
            
            # Apply explicit user color overrides if provided
            if getattr(config, "primary_color_rgb", None):
                intelligence["primary_color_rgb"] = config.primary_color_rgb
                intelligence["is_colorful"] = True
            if getattr(config, "secondary_color_rgb", None):
                intelligence["secondary_color_rgb"] = config.secondary_color_rgb

            predicted_cat = intelligence.get("predicted_category", "chair")
            predicted_obj = intelligence.get("predicted_object", predicted_cat)
            confidence = intelligence.get("top_confidence", 0.5)
            geo_tags = intelligence.get("geometric_tags", [])
            color_status = f"Colors: {intelligence.get('primary_color_hex', 'N/A')}" if intelligence.get("is_colorful") else "Monochrome"
            record_stage_complete(
                rec,
                f"Predicted: '{predicted_obj}' ({predicted_cat}, conf: {confidence:.2f}) | {color_status}",
                metadata={"intelligence": intelligence}
            )

            # ---------------------------------------------------------
            # Stage 4: MODEL_SELECTION
            # ---------------------------------------------------------
            rec = record_stage_start(PipelineStage.MODEL_SELECTION, "Evaluating adaptive routing rules for reconstruction")
            selected_model, selection_reason = self.stage_executor.select_reconstruction_model(
                user_preference=config.preferred_model,
                category=predicted_cat,
                confidence=confidence,
                geometric_tags=geo_tags,
                quality_preset=config.quality_preset
            )
            record_stage_complete(
                rec,
                f"Selected model: {selected_model} ({selection_reason})",
                metadata={"selected_model": selected_model, "reason": selection_reason}
            )

            # ---------------------------------------------------------
            # Stage 5: RECONSTRUCTING_3D
            # ---------------------------------------------------------
            rec = record_stage_start(PipelineStage.RECONSTRUCTING_3D, f"Generating 3D asset via {selected_model}")
            rec_resp, fallback_telemetry = self.stage_executor.execute_reconstruction(
                primary_model=selected_model,
                image_path=processed_path,
                job_dir=job_dir,
                quality_preset=config.quality_preset,
                export_formats=config.export_formats,
                semantic_metadata=intelligence,
                allow_fallback=config.allow_fallback
            )
            primary_mesh_path = rec_resp.mesh_path
            record_stage_complete(
                rec,
                f"Generated mesh with {rec_resp.vertices} vertices, {rec_resp.faces} faces ({rec_resp.inference_time_seconds:.2f}s)",
                artifacts=rec_resp.downloads,
                metadata={
                    "model_used": rec_resp.model_name,
                    "inference_time": rec_resp.inference_time_seconds,
                    "fallback_telemetry": fallback_telemetry,
                    "mesh_stats": {"vertices": rec_resp.vertices, "faces": rec_resp.faces}
                }
            )

            # ---------------------------------------------------------
            # Stage 6: MESH_VALIDATION
            # ---------------------------------------------------------
            rec = record_stage_start(PipelineStage.MESH_VALIDATION, "Validating mesh topology, finiteness and manifold bounds")
            from app.reconstruction.mesh_validation import MeshValidator
            val_report = MeshValidator.validate_file(primary_mesh_path)
            record_stage_complete(
                rec,
                f"Mesh topology verified: watertight={val_report.get('is_watertight', False)}",
                metadata={"validation_report": val_report}
            )

            # ---------------------------------------------------------
            # Stage 7: GEOMETRY_ANALYSIS & QUALITY EVALUATION
            # ---------------------------------------------------------
            rec = record_stage_start(PipelineStage.GEOMETRY_ANALYSIS, "Evaluating multi-view silhouettes and geometric defects")
            geom_report = self.stage_executor.execute_geometry_intelligence(
                mesh_path=primary_mesh_path,
                asset_id=job_id,
                sketch_path=processed_path
            )
            overall_quality = geom_report.get("overall_score", 70.0)
            record_stage_complete(
                rec,
                f"Quality evaluated: Overall Score = {overall_quality:.1f}/100",
                metadata={"geometry_report": geom_report}
            )

            # ---------------------------------------------------------
            # Stage 8: MESH_REFINEMENT
            # ---------------------------------------------------------
            refined_mesh_path = None
            if config.auto_refine:
                rec = record_stage_start(PipelineStage.MESH_REFINEMENT, "Applying volume-preserving smoothing & quadric decimation")
                comp_report, refined_downloads = self.stage_executor.execute_refinement(
                    mesh_path=primary_mesh_path,
                    preset=config.refine_preset,
                    asset_id=job_id,
                    job_dir=job_dir,
                    export_formats=config.export_formats
                )
                refined_mesh_path = refined_downloads.get("glb") or refined_downloads.get("obj")
                # Prefix refined downloads to distinguish
                refined_artifacts = {f"refined_{k}": v for k, v in refined_downloads.items()}
                record_stage_complete(
                    rec,
                    f"Refinement complete: reduction = {comp_report.get('face_reduction_percent', 0):.1f}%",
                    artifacts=refined_artifacts,
                    metadata={"refinement_report": comp_report}
                )

            # ---------------------------------------------------------
            # Stage 9: PBR_TEXTURING
            # ---------------------------------------------------------
            base_for_texturing = refined_mesh_path or primary_mesh_path
            pbr_mesh_path = None
            tex_artifacts = {}
            mat_metadata = {}

            if getattr(config, "enable_pbr", True):
                rec = record_stage_start(PipelineStage.PBR_TEXTURING, "Synthesizing AI PBR texture maps and glTF material")
                try:
                    pbr_mesh_path, tex_paths, mat_metadata = self.stage_executor.execute_pbr_texturing(
                        mesh_path=base_for_texturing,
                        category=predicted_cat,
                        style=getattr(config, "visual_style", "realistic"),
                        material_override=getattr(config, "material_override", None),
                        job_dir=job_dir,
                        color_palette=intelligence
                    )
                    tex_artifacts = {f"texture_{k}": v for k, v in tex_paths.items()}
                    record_stage_complete(
                        rec,
                        f"PBR textures baked: {mat_metadata.get('display_name')}",
                        artifacts={"pbr_glb": pbr_mesh_path, **tex_artifacts},
                        metadata={"material": mat_metadata}
                    )
                except Exception as pbr_err:
                    print(f"[Orchestrator] PBR texturing notice: {pbr_err}")
                    record_stage_complete(rec, f"PBR fallback: {pbr_err}", metadata={"pbr_error": str(pbr_err)})

            final_presentation_mesh = pbr_mesh_path or refined_mesh_path or primary_mesh_path

            # ---------------------------------------------------------
            # Stage 10: EXPORTING_ASSETS
            # ---------------------------------------------------------
            rec = record_stage_start(PipelineStage.EXPORTING_ASSETS, "Exporting production formats (GLB, GLTF, OBJ, STL, 3MF, USDZ)")
            from app.packaging import MultiFormatExporter
            exported_all = MultiFormatExporter.export_all_formats(
                mesh=trimesh.load(final_presentation_mesh, force="mesh"),
                output_dir=str(job_dir / "exports"),
                base_filename=f"{job_id}_export",
                formats=config.export_formats
            )

            final_artifacts = {
                "final_mesh": final_presentation_mesh,
                "primary_mesh": primary_mesh_path,
                "primary_glb": rec_resp.downloads.get("glb"),
                "primary_obj": rec_resp.downloads.get("obj"),
                **exported_all
            }
            if refined_mesh_path:
                final_artifacts["refined_glb"] = refined_downloads.get("glb")
                final_artifacts["refined_obj"] = refined_downloads.get("obj")
            if pbr_mesh_path:
                final_artifacts["pbr_glb"] = pbr_mesh_path

            record_stage_complete(rec, "All export assets generated and indexed successfully", artifacts=final_artifacts)

            # ---------------------------------------------------------
            # Stage 11: ASSET_PACKAGING & PRINTABILITY DIAGNOSTICS
            # ---------------------------------------------------------
            pkg_info = {}
            if getattr(config, "enable_packaging", True):
                rec = record_stage_start(PipelineStage.ASSET_PACKAGING, "Assembling complete distribution bundle (.zip)")
                try:
                    pkg_info = self.stage_executor.execute_asset_packaging(
                        mesh_path=final_presentation_mesh,
                        category=predicted_cat,
                        job_id=job_id,
                        job_dir=job_dir,
                        texture_paths=tex_paths if 'tex_paths' in locals() else {},
                        untextured_mesh_path=primary_mesh_path,
                        geometry_metrics=geom_report,
                        material_metadata=mat_metadata,
                        export_formats=config.export_formats
                    )
                    record_stage_complete(
                        rec,
                        f"Asset bundle created ({pkg_info.get('zip_size_bytes', 0) / 1024:.1f} KB)",
                        artifacts={"bundle_zip": pkg_info.get("zip_path")},
                        metadata={
                            "printability": pkg_info.get("printability"),
                            "lods": pkg_info.get("lods")
                        }
                    )
                except Exception as pkg_err:
                    print(f"[Orchestrator] Packaging notice: {pkg_err}")
                    record_stage_complete(rec, f"Packaging skipped: {pkg_err}", metadata={"packaging_error": str(pkg_err)})

            # ---------------------------------------------------------
            # Final Completion & Telemetry
            # ---------------------------------------------------------
            job_tracker.current_stage = PipelineStage.COMPLETED
            job_tracker.status = "completed"
            job_tracker.total_duration_seconds = round(time.time() - start_time, 3)
            job_tracker.metrics = {
                "total_duration_seconds": job_tracker.total_duration_seconds,
                "peak_vram_mb": job_tracker.peak_vram_mb,
                "overall_quality_score": overall_quality,
                "predicted_category": predicted_cat,
                "model_used": rec_resp.model_name,
                "fallback_occurred": fallback_telemetry.get("fallback_triggered", False),
                "original_vertices": rec_resp.vertices,
                "original_faces": rec_resp.faces,
                "material": mat_metadata,
                "printability": pkg_info.get("printability", {}),
                "lods": pkg_info.get("lods", {})
            }
            ExecutionLogger.log_stage_event(job_id, "completed", f"Pipeline completed successfully in {job_tracker.total_duration_seconds}s!")


        except PipelineException as pe:
            job_tracker.current_stage = pe.stage
            job_tracker.status = "failed" if pe.stage != PipelineStage.CANCELLED else "cancelled"
            job_tracker.error = pe.message
            job_tracker.total_duration_seconds = round(time.time() - start_time, 3)
            ExecutionLogger.log_stage_event(job_id, pe.stage.value, f"Pipeline terminated: {pe.message}")

        except Exception as e:
            job_tracker.current_stage = PipelineStage.FAILED
            job_tracker.status = "failed"
            job_tracker.error = f"Unhandled exception: {str(e)}"
            job_tracker.total_duration_seconds = round(time.time() - start_time, 3)
            ExecutionLogger.log_stage_event(job_id, "failed", f"Unhandled pipeline failure: {e}")

        finally:
            ExecutionLogger.cleanup_gpu_memory()
            job_tracker.updated_at = time.time()

        return job_tracker

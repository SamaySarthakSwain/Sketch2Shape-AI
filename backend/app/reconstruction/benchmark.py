"""
Reconstruction Benchmark Engine
Benchmarks identical sketches across multiple reconstruction models.
Measures latency, memory usage, vertex & face counts, watertightness, and output file sizes.
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import torch

from app.reconstruction.reconstruction_config import ReconstructionRequest
from app.reconstruction.model_registry import model_registry
from app.reconstruction.mesh_validation import MeshValidator


class ReconstructionBenchmark:
    """
    Automated benchmarking harness for 3D reconstruction models.
    """

    @classmethod
    def run_benchmark(
        cls,
        image_paths: List[str],
        models_to_test: Optional[List[str]] = None,
        output_dir: Optional[str] = None,
        quality_preset: str = "fast",
    ) -> Dict[str, Any]:
        """
        Executes comparative benchmarks across multiple input sketches and models.
        """
        if output_dir is None:
            output_dir = str(Path(__file__).resolve().parent.parent.parent.parent / "experiments" / "reconstruction")
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        if models_to_test is None:
            models_to_test = ["procedural", "instantmesh"]

        benchmark_results = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "tested_models": models_to_test,
            "images": [Path(p).name for p in image_paths],
            "runs": []
        }

        print("\n=======================================================")
        print(" STARTING 3D RECONSTRUCTION BENCHMARK SUITE")
        print("=======================================================")

        for img_path in image_paths:
            img_file = Path(img_path)
            if not img_file.exists():
                print(f"[Benchmark] Skipping missing file: {img_path}")
                continue

            for model_name in models_to_test:
                adapter = model_registry.get_model(model_name)
                if adapter is None or not adapter.is_available():
                    print(f"[Benchmark] Model '{model_name}' is not available. Recording skip.")
                    benchmark_results["runs"].append({
                        "image": img_file.name,
                        "model": model_name,
                        "available": False,
                        "status": "unavailable"
                    })
                    continue

                print(f"\n[Benchmark] Testing Model='{model_name}' on Image='{img_file.name}'...")
                
                # Reset GPU stats if available
                if torch.cuda.is_available():
                    torch.cuda.reset_peak_memory_stats()
                    torch.cuda.empty_cache()

                sub_out_dir = out_path / f"bench_{model_name}_{img_file.stem}"
                sub_out_dir.mkdir(parents=True, exist_ok=True)

                req = ReconstructionRequest(
                    image_path=str(img_file),
                    output_dir=str(sub_out_dir),
                    model_name=model_name,
                    quality_preset=quality_preset,
                    export_formats=["glb", "obj"],
                    preprocess_first=False
                )

                t0 = time.perf_counter()
                resp = adapter.reconstruct(req)
                t1 = time.perf_counter()
                elapsed_sec = round(t1 - t0, 3)

                peak_vram_mb = 0.0
                if torch.cuda.is_available():
                    peak_vram_mb = round(torch.cuda.max_memory_allocated() / (1024 * 1024), 2)

                glb_size_bytes = 0
                obj_size_bytes = 0
                if resp.success and resp.formats:
                    glb_p = resp.formats.get("glb")
                    obj_p = resp.formats.get("obj")
                    if glb_p and Path(glb_p).exists():
                        glb_size_bytes = Path(glb_p).stat().st_size
                    if obj_p and Path(obj_p).exists():
                        obj_size_bytes = Path(obj_p).stat().st_size

                run_entry = {
                    "image": img_file.name,
                    "model": model_name,
                    "available": True,
                    "success": resp.success,
                    "latency_seconds": elapsed_sec,
                    "peak_vram_mb": peak_vram_mb,
                    "vertices": resp.vertices,
                    "faces": resp.faces,
                    "is_watertight": resp.quality_report.get("is_watertight", False),
                    "glb_size_bytes": glb_size_bytes,
                    "obj_size_bytes": obj_size_bytes,
                    "error": resp.error
                }
                benchmark_results["runs"].append(run_entry)
                print(f"  -> Result: Success={resp.success} | Latency={elapsed_sec}s | Verts={resp.vertices} | Watertight={run_entry['is_watertight']}")

        # Save benchmark report
        report_file = out_path / "model_comparison.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(benchmark_results, f, indent=2)
        print(f"\n[Benchmark] Complete. Report saved to {report_file}")

        return benchmark_results

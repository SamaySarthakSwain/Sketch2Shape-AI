"""
Benchmark Execution & Timing Analysis for Sketch2Shape AI
Measures exact execution times across each stage for different sketch types.
"""

import time
import cv2
import numpy as np
from app.preprocessing.sketch_processor import SketchPreprocessor
from app.sketch_intelligence.analyzer import SketchAnalyzer
from app.reconstruction.procedural_engine import ProceduralReconstructionEngine
from app.mesh.validator import MeshValidator
from app.mesh.exporter import MeshExporter
import trimesh
import tempfile
from pathlib import Path

def create_synthetic_sketch(shape_type="vase"):
    canvas = np.ones((512, 512), dtype=np.uint8) * 255
    cx, cy = 256, 256
    if shape_type == "vase":
        cv2.ellipse(canvas, (cx, cy + 40), (80, 130), 0, 0, 360, 0, thickness=6)
        cv2.rectangle(canvas, (cx - 35, cy - 140), (cx + 35, cy - 60), 0, thickness=6)
    elif shape_type == "car":
        cv2.rectangle(canvas, (cx - 120, cy), (cx + 120, cy + 60), 0, thickness=6)
        cv2.ellipse(canvas, (cx, cy - 10), (70, 40), 0, 180, 360, 0, thickness=6)
        cv2.circle(canvas, (cx - 70, cy + 60), 25, 0, thickness=6)
        cv2.circle(canvas, (cx + 70, cy + 60), 25, 0, thickness=6)
    elif shape_type == "chair":
        cv2.line(canvas, (cx - 50, cy - 120), (cx - 50, cy + 30), 0, thickness=8)
        cv2.line(canvas, (cx - 50, cy + 30), (cx + 60, cy + 30), 0, thickness=8)
        cv2.line(canvas, (cx - 45, cy + 30), (cx - 45, cy + 140), 0, thickness=8)
        cv2.line(canvas, (cx + 55, cy + 30), (cx + 55, cy + 140), 0, thickness=8)
    return canvas

def benchmark():
    preprocessor = SketchPreprocessor(target_size=512)
    analyzer = SketchAnalyzer()
    engine = ProceduralReconstructionEngine()
    validator = MeshValidator()
    
    test_shapes = ["vase", "car", "chair"]
    results = []

    print("\n================ BENCHMARK TIMING BREAKDOWN ================\n")

    for shape in test_shapes:
        raw_img = create_synthetic_sketch(shape)
        
        # 1. Preprocessing Timing
        t0 = time.perf_counter()
        prep_data = preprocessor.process(raw_img)
        t_prep = (time.perf_counter() - t0) * 1000

        # 2. Sketch Intelligence Timing
        raw_mask = preprocessor.load_image(prep_data["binary_mask_b64"])
        if len(raw_mask.shape) == 3:
            raw_mask = raw_mask[:, :, 0]
        
        t0 = time.perf_counter()
        intel_data = analyzer.analyze(raw_mask, prep_data["bounding_box"])
        t_intel = (time.perf_counter() - t0) * 1000

        # 3. 3D Reconstruction Timing
        depth_raw = preprocessor.load_image(prep_data["depth_map_b64"])
        if len(depth_raw.shape) == 3:
            depth_raw = depth_raw[:, :, 0]

        t0 = time.perf_counter()
        mesh = engine.generate_mesh(raw_mask, depth_raw, intel_data)
        t_recon = (time.perf_counter() - t0) * 1000

        # 4. Mesh Validation & Repair Timing
        t0 = time.perf_counter()
        repaired_mesh, report = validator.repair_and_normalize(mesh)
        t_val = (time.perf_counter() - t0) * 1000

        # 5. Multi-format Export Timing (GLB, OBJ, STL, PLY)
        with tempfile.TemporaryDirectory() as tmp_dir:
            t0 = time.perf_counter()
            MeshExporter.export_all_formats(repaired_mesh, tmp_dir, "benchmark_model")
            t_export = (time.perf_counter() - t0) * 1000

        total_pipeline_time = t_prep + t_intel + t_recon + t_val + t_export

        print(f"Shape: {shape.upper()} ({intel_data['classification']['category']})")
        print(f"  - OpenCV Preprocessing:      {t_prep:6.2f} ms")
        print(f"  - Sketch Intelligence:       {t_intel:6.2f} ms")
        print(f"  - 3D Mesh Reconstruction:    {t_recon:6.2f} ms")
        print(f"  - Topology Validation & Fix: {t_val:6.2f} ms")
        print(f"  - Multi-format Export (x4):  {t_export:6.2f} ms")
        print(f"  -------------------------------------------")
        print(f"  -> TOTAL LATENCY:            {total_pipeline_time:6.2f} ms ({total_pipeline_time/1000:.3f} s)")
        print(f"  -> Faces: {len(repaired_mesh.faces)}, Watertight: {report['is_watertight']}, Euler (chi): {report['euler_characteristic']}\n")

if __name__ == "__main__":
    benchmark()

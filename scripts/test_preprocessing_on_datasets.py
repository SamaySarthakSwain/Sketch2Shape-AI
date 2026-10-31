"""
Comprehensive Dataset Testing and Performance Benchmarking for Sketch Preprocessing Engine
Tests the pipeline on samples from Google QuickDraw and TU-Berlin datasets.
Measures latency, memory usage, resolution scaling, and exports 3x3 diagnostic grids.
"""

import os
import sys
import io
import time
import json
import tracemalloc
from pathlib import Path
from typing import Dict, Any, List
import numpy as np
import cv2
import pyarrow.parquet as pq

# Ensure UTF-8 stdout on Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Ensure backend is on PYTHONPATH
workspace_dir = Path(r"C:\Sketch2Shape-AI")
backend_dir = workspace_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.preprocessing import (
    SketchPreprocessingPipeline,
    SketchVisualizer,
    ImageLoader,
    ImageValidator,
    ImageEnhancer,
    SketchDenoiser,
    EdgeDetector,
    SketchThresholder,
    ContourAnalyzer,
    StrokeAnalyzer,
    SymmetryAnalyzer,
    ShapeAnalyzer,
    ForegroundExtractor,
    SketchNormalizer,
)


def render_quickdraw_drawing(drawing: list, size: int = 512, stroke_width: int = 3) -> np.ndarray:
    """Renders raw QuickDraw vector strokes onto a white canvas."""
    canvas = np.full((size, size, 3), 255, dtype=np.uint8)
    
    # QuickDraw coordinates are [0, 255]
    scale = (size - 32) / 255.0
    offset = 16

    for stroke in drawing:
        x_coords, y_coords = stroke[0], stroke[1]
        points = []
        for x, y in zip(x_coords, y_coords):
            px = int(x * scale + offset)
            py = int(y * scale + offset)
            points.append((px, py))
        
        if len(points) == 1:
            cv2.circle(canvas, points[0], stroke_width, (0, 0, 0), -1)
        elif len(points) > 1:
            pts = np.array(points, dtype=np.int32).reshape((-1, 1, 2))
            cv2.polylines(canvas, [pts], isClosed=False, color=(0, 0, 0), thickness=stroke_width, lineType=cv2.LINE_AA)
            
    return canvas


def test_quickdraw_samples(output_dir: Path) -> List[Dict[str, Any]]:
    print("\n--- Testing on Google QuickDraw Samples ---")
    qd_dir = workspace_dir / "datasets" / "quickdraw" / "raw"
    test_categories = ["airplane", "chair", "car", "apple", "cup", "bicycle"]
    results = []
    
    pipeline = SketchPreprocessingPipeline(target_size=512)

    for cat in test_categories:
        file_path = qd_dir / f"{cat}.ndjson"
        if not file_path.exists():
            print(f"Skipping {cat}: {file_path} not found")
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            line = f.readline()
            data = json.loads(line)

        canvas = render_quickdraw_drawing(data["drawing"], size=512, stroke_width=4)
        
        t0 = time.perf_counter()
        variants, report = pipeline.process(canvas)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        grid_path = output_dir / f"quickdraw_{cat}_grid.png"
        SketchVisualizer.save_debug_grid(variants, str(grid_path))
        
        recon_path = output_dir / f"quickdraw_{cat}_normalized.png"
        cv2.imwrite(str(recon_path), variants["final_reconstruction_input"])

        print(f"  [QuickDraw: {cat:<10}] {elapsed_ms:6.2f} ms | Stroke w={report.stroke_analysis['average_width_estimate']:.1f}px | Endpoints={report.stroke_analysis['endpoint_count']:2d} | Symm={report.symmetry['score']:.2f}")

        results.append({
            "dataset": "QuickDraw",
            "category": cat,
            "latency_ms": round(elapsed_ms, 2),
            "stroke_width": report.stroke_analysis["average_width_estimate"],
            "endpoints": report.stroke_analysis["endpoint_count"],
            "junctions": report.stroke_analysis["junction_count"],
            "symmetry_score": report.symmetry["score"],
            "compactness": report.shape_analysis["compactness"],
            "orientation_deg": report.shape_analysis["orientation_degrees"],
            "grid_output": str(grid_path.relative_to(workspace_dir)),
        })

    return results


def test_tu_berlin_samples(output_dir: Path) -> List[Dict[str, Any]]:
    print("\n--- Testing on TU-Berlin Real Sketch Samples ---")
    tu_dir = workspace_dir / "datasets" / "tu_berlin" / "raw"
    parquet_files = sorted(list(tu_dir.glob("*.parquet")))
    results = []

    if not parquet_files:
        print("No TU-Berlin parquet files found.")
        return results

    table = pq.read_table(str(parquet_files[0]))
    pipeline = SketchPreprocessingPipeline(target_size=512)

    # Test 6 distinct samples from the partition
    indices = [0, 10, 25, 50, 75, 100]
    for idx in indices:
        if idx >= table.num_rows:
            break
        row = table.slice(idx, 1).to_pydict()
        img_bytes = row["image"][0]["bytes"]
        label = row["label"][0]

        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)

        t0 = time.perf_counter()
        variants, report = pipeline.process(img)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        grid_path = output_dir / f"tu_berlin_sample_{idx}_grid.png"
        SketchVisualizer.save_debug_grid(variants, str(grid_path))

        recon_path = output_dir / f"tu_berlin_sample_{idx}_normalized.png"
        cv2.imwrite(str(recon_path), variants["final_reconstruction_input"])

        print(f"  [TU-Berlin: Idx {idx:<3}] {elapsed_ms:6.2f} ms | Label={label:3d} | Stroke w={report.stroke_analysis['average_width_estimate']:.1f}px | Contours={report.contour_count:2d} | Symm={report.symmetry['score']:.2f}")

        results.append({
            "dataset": "TU-Berlin",
            "sample_index": idx,
            "label": label,
            "latency_ms": round(elapsed_ms, 2),
            "stroke_width": report.stroke_analysis["average_width_estimate"],
            "endpoints": report.stroke_analysis["endpoint_count"],
            "junctions": report.stroke_analysis["junction_count"],
            "symmetry_score": report.symmetry["score"],
            "compactness": report.shape_analysis["compactness"],
            "grid_output": str(grid_path.relative_to(workspace_dir)),
        })

    return results


def benchmark_module_breakdown(size: int = 512) -> Dict[str, float]:
    print(f"\n--- Benchmarking Sub-Module Latency Breakdown ({size}x{size}) ---")
    
    # Generate test sketch canvas with synthetic drawing
    canvas = np.full((size, size, 3), 255, dtype=np.uint8)
    cv2.circle(canvas, (size // 2, size // 2), size // 4, (0, 0, 0), thickness=5)
    cv2.rectangle(canvas, (size // 4, size // 4), (size * 3 // 4, size * 3 // 4), (0, 0, 0), thickness=4)
    cv2.line(canvas, (0, 0), (size, size), (0, 0, 0), thickness=3)

    enhancer = ImageEnhancer()
    denoiser = SketchDenoiser()
    edge_detector = EdgeDetector()
    thresholder = SketchThresholder()
    contour_analyzer = ContourAnalyzer()
    stroke_analyzer = StrokeAnalyzer()
    symmetry_analyzer = SymmetryAnalyzer()
    shape_analyzer = ShapeAnalyzer()
    foreground_extractor = ForegroundExtractor()
    normalizer = SketchNormalizer(target_size=512)

    # 1. Image loading & validation
    t0 = time.perf_counter()
    bgr, alpha = ImageLoader.load(canvas)
    val = ImageValidator.validate_array(bgr, alpha)
    gray = ImageLoader.to_grayscale(bgr)
    t_val = (time.perf_counter() - t0) * 1000.0

    # 2. Enhancement
    t0 = time.perf_counter()
    enhanced, _ = enhancer.enhance(gray)
    t_enh = (time.perf_counter() - t0) * 1000.0

    # 3. Denoising
    t0 = time.perf_counter()
    denoised = denoiser.denoise_for_reconstruction(enhanced, method="bilateral")
    t_den = (time.perf_counter() - t0) * 1000.0

    # 4. Edge Detection
    t0 = time.perf_counter()
    edge_map, _ = edge_detector.detect_and_measure(denoised)
    t_edge = (time.perf_counter() - t0) * 1000.0

    # 5. Thresholding
    t0 = time.perf_counter()
    binary = thresholder.binarize(denoised, method="adaptive_gaussian", apply_morphology=True)
    t_thresh = (time.perf_counter() - t0) * 1000.0

    # 6. Foreground Extraction
    t0 = time.perf_counter()
    clean_mask, _ = foreground_extractor.extract_foreground(bgr, binary)
    t_fg = (time.perf_counter() - t0) * 1000.0

    # 7. Contour Analysis
    t0 = time.perf_counter()
    _, _, contours = contour_analyzer.analyze_contours(clean_mask)
    main_c = contours[0] if contours else None
    t_cont = (time.perf_counter() - t0) * 1000.0

    # 8. Stroke Analysis
    t0 = time.perf_counter()
    skeleton, dist_t, stroke_m = stroke_analyzer.analyze_strokes(clean_mask)
    t_stroke = (time.perf_counter() - t0) * 1000.0

    # 9. Symmetry Analysis
    t0 = time.perf_counter()
    symm_m = symmetry_analyzer.analyze_symmetry(clean_mask)
    t_symm = (time.perf_counter() - t0) * 1000.0

    # 10. Shape Analysis
    t0 = time.perf_counter()
    shape_m = shape_analyzer.analyze_shape(clean_mask, main_c)
    t_shape = (time.perf_counter() - t0) * 1000.0

    # 11. Normalization
    t0 = time.perf_counter()
    norm_rgb, norm_rgba, norm_mask = normalizer.normalize(bgr, clean_mask)
    t_norm = (time.perf_counter() - t0) * 1000.0

    breakdown = {
        "Image Validation & Conversion": round(t_val, 2),
        "CLAHE / Contrast Enhancement": round(t_enh, 2),
        "Bilateral Denoising": round(t_den, 2),
        "Auto-Canny Edge Detection": round(t_edge, 2),
        "Adaptive Thresholding & Morphology": round(t_thresh, 2),
        "Foreground Extraction & Filtering": round(t_fg, 2),
        "Contour Topology & Hierarchy": round(t_cont, 2),
        "Stroke Skeleton & Distance Transform": round(t_stroke, 2),
        "Reflectional Symmetry (IoU)": round(t_symm, 2),
        "Shape Moments & PCA Orientation": round(t_shape, 2),
        "Reconstruction Normalization (512x512)": round(t_norm, 2),
    }

    total_sum = sum(breakdown.values())
    for module, ms in breakdown.items():
        pct = (ms / total_sum) * 100.0
        print(f"  {module:<38}: {ms:6.2f} ms ({pct:4.1f}%)")
    print(f"  {'Total Cumulative Pipeline':<38}: {total_sum:6.2f} ms")

    return breakdown


def benchmark_resolution_scaling() -> List[Dict[str, Any]]:
    print("\n--- Benchmarking Resolution Scaling & Memory Footprint ---")
    resolutions = [128, 256, 512, 1024, 2048]
    pipeline = SketchPreprocessingPipeline(target_size=512)
    scaling_results = []

    for res in resolutions:
        # Create synthetic sketch at resolution
        canvas = np.full((res, res, 3), 255, dtype=np.uint8)
        cv2.circle(canvas, (res // 2, res // 2), res // 3, (0, 0, 0), thickness=max(2, res // 100))
        cv2.rectangle(canvas, (res // 5, res // 5), (res * 4 // 5, res * 4 // 5), (0, 0, 0), thickness=max(2, res // 150))
        
        tracemalloc.start()
        t0 = time.perf_counter()
        variants, report = pipeline.process(canvas)
        latency_ms = (time.perf_counter() - t0) * 1000.0
        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        peak_mb = peak_mem / (1024 * 1024)
        print(f"  Resolution {res:>4}x{res:<4} | Latency: {latency_ms:7.2f} ms | Peak RAM: {peak_mb:5.2f} MB")

        scaling_results.append({
            "resolution": f"{res}x{res}",
            "width": res,
            "height": res,
            "latency_ms": round(latency_ms, 2),
            "peak_memory_mb": round(peak_mb, 2)
        })

    return scaling_results


def main():
    print("==================================================================")
    print(" SKETCH2SHAPE AI: OPENCV PREPROCESSING ENGINE BENCHMARK SUITE    ")
    print("==================================================================")

    output_dir = workspace_dir / "outputs" / "preprocessing_tests"
    output_dir.mkdir(parents=True, exist_ok=True)

    qd_results = test_quickdraw_samples(output_dir)
    tu_results = test_tu_berlin_samples(output_dir)
    breakdown = benchmark_module_breakdown(size=512)
    scaling = benchmark_resolution_scaling()

    benchmark_summary = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "quickdraw_tests": qd_results,
        "tu_berlin_tests": tu_results,
        "latency_breakdown_512": breakdown,
        "resolution_scaling": scaling
    }

    summary_file = output_dir / "benchmark_results.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(benchmark_summary, f, indent=2)

    print(f"\nAll tests completed. Benchmark results saved to: {summary_file}")
    print(f"Visual diagnostic grids saved to: {output_dir}")


if __name__ == "__main__":
    main()

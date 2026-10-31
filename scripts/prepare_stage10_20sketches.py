"""
Prepare 20 Benchmark Sketches for Stage 10 Production Integration Benchmark
Extracts authentic sketch samples across 20 distinct categories from test datasets
and saves them as standard black-on-white PNGs ready for pipeline evaluation.
"""

import json
from pathlib import Path
import numpy as np
from PIL import Image

BASE_DIR = Path(r"C:\Sketch2Shape-AI")
OUTPUT_DIR = BASE_DIR / "datasets" / "benchmark_20sketches"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load class mapping
with open(BASE_DIR / "models" / "sketch_intelligence" / "class_mapping.json", "r") as f:
    mapping = json.load(f)

class_to_idx = mapping["class_to_idx"]
idx_to_class = {int(k): v for k, v in mapping["idx_to_class"].items()}

# Load test labels & arrays
y_test = np.load(BASE_DIR / "datasets" / "sketch_intelligence" / "y_test.npy")
X_test = np.load(BASE_DIR / "datasets" / "sketch_intelligence" / "X_test.npy", mmap_mode="r")

target_categories = [
    "chair", "car", "airplane", "cup", "apple",
    "bicycle", "table", "wine_glass", "sword", "tree",
    "house", "guitar", "book", "eyeglasses", "hat",
    "alarm_clock", "bench", "hammer", "mushroom", "cell_phone"
]

benchmarks = []

for cat in target_categories:
    idx = class_to_idx[cat]
    # Find all sample indices for this class
    matches = np.where(y_test == idx)[0]
    if len(matches) == 0:
        print(f"Warning: No samples found for {cat}")
        continue

    # Pick sample #5 to ensure good stroke density
    sample_idx = matches[min(5, len(matches) - 1)]
    sample_img = X_test[sample_idx]  # 128x128, 255=stroke, 0=bg

    # Invert so 0=stroke (black), 255=bg (white)
    inverted = 255 - sample_img
    
    # Resize to 512x512 with bicubic / nearest for clean presentation
    pil_img = Image.fromarray(inverted).convert("RGB").resize((512, 512), Image.Resampling.NEAREST)
    
    out_path = OUTPUT_DIR / f"{cat}_sketch.png"
    pil_img.save(str(out_path))

    benchmarks.append({
        "category": cat,
        "class_idx": idx,
        "sample_idx": int(sample_idx),
        "file_path": str(out_path),
        "relative_path": f"datasets/benchmark_20sketches/{cat}_sketch.png"
    })
    print(f"Extracted [{cat}] -> {out_path.name}")

# Save benchmark manifest
manifest_path = OUTPUT_DIR / "benchmark_manifest.json"
with open(manifest_path, "w") as f:
    json.dump(benchmarks, f, indent=2)

print(f"\nPrepared {len(benchmarks)} benchmark sketches in {OUTPUT_DIR}")

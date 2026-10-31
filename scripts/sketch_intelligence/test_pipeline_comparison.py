"""
Stage 6: Comparative Evaluation of Raw vs Stage 5 Preprocessed Sketches
Tests the Sketch Intelligence Classifier on:
- 6 Mandatory Categories: Chair, Car, Airplane, Bicycle, Cup, Apple
- Ambiguous Sketches
- Blank Images
- Noisy Sketches
- Unseen TU-Berlin Sketches
Evaluates classification accuracy, confidence, and geometric prior extraction on both
(1) Raw Unprocessed Images, and (2) Stage 5 Preprocessed Images.
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List
import numpy as np
import cv2

# Ensure backend is on PYTHONPATH
BASE_DIR = Path(r"C:\Sketch2Shape-AI")
BACKEND_DIR = BASE_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.sketch_intelligence.classifier import SketchIntelligenceEngine

DATASET_DIR = BASE_DIR / "datasets" / "sketch_intelligence"
EXPERIMENTS_DIR = BASE_DIR / "experiments" / "sketch_intelligence"
MODELS_DIR = BASE_DIR / "models" / "sketch_intelligence"


def create_test_samples(class_mapping: dict) -> List[Dict[str, Any]]:
    """Creates a diverse evaluation suite covering standard, edge-case, and benchmark samples."""
    samples = []
    class_to_idx = class_mapping["class_to_idx"]

    # Load test split
    X_test = np.load(DATASET_DIR / "X_test.npy", mmap_mode="r")
    y_test = np.load(DATASET_DIR / "y_test.npy")

    # Load TU-Berlin test split
    tu_X = np.load(DATASET_DIR / "tu_berlin_X_test.npy", mmap_mode="r")
    tu_y = np.load(DATASET_DIR / "tu_berlin_y_test.npy")

    # 1. Mandatory 6 categories from QuickDraw test set
    target_cats = ["chair", "car", "airplane", "bicycle", "cup", "apple"]
    for cat in target_cats:
        c_idx = class_to_idx[cat]
        matches = np.where(y_test == c_idx)[0]
        if len(matches) > 0:
            sample_img = X_test[matches[0]]
            # Convert 128x128 stroke image to 512x512 white background sketch
            canvas_512 = 255 - cv2.resize(sample_img, (512, 512), interpolation=cv2.INTER_NEAREST)
            canvas_bgr = cv2.cvtColor(canvas_512, cv2.COLOR_GRAY2BGR)
            samples.append({
                "name": f"QuickDraw_{cat}",
                "category": cat,
                "type": "standard_sketch",
                "image": canvas_bgr,
                "expected_category": cat
            })

    # 2. Ambiguous sketch: A simple oval / rounded rectangle
    ambiguous_canvas = np.full((512, 512, 3), 255, dtype=np.uint8)
    cv2.ellipse(ambiguous_canvas, (256, 256), (180, 100), 0, 0, 360, (0, 0, 0), thickness=4)
    samples.append({
        "name": "Ambiguous_Oval",
        "category": "ambiguous",
        "type": "ambiguous_geometric",
        "image": ambiguous_canvas,
        "expected_category": "ambiguous"
    })

    # 3. Blank image: Pure white canvas
    blank_canvas = np.full((512, 512, 3), 255, dtype=np.uint8)
    samples.append({
        "name": "Blank_Image",
        "category": "blank",
        "type": "blank_input",
        "image": blank_canvas,
        "expected_category": "none"
    })

    # 4. Noisy sketch: Chair with heavy salt-and-pepper and background grain
    chair_idx = class_to_idx["chair"]
    chair_sample = X_test[np.where(y_test == chair_idx)[0][1]]
    noisy_512 = 255 - cv2.resize(chair_sample, (512, 512), interpolation=cv2.INTER_NEAREST)
    noise = np.random.normal(0, 25, noisy_512.shape).astype(np.int16)
    noisy_img = np.clip(noisy_512.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    # Add random speckles
    for _ in range(150):
        rx, ry = np.random.randint(0, 512, 2)
        cv2.circle(noisy_img, (rx, ry), np.random.randint(2, 6), 0, -1)
    noisy_bgr = cv2.cvtColor(noisy_img, cv2.COLOR_GRAY2BGR)
    samples.append({
        "name": "Noisy_Chair",
        "category": "chair",
        "type": "noisy_corrupted",
        "image": noisy_bgr,
        "expected_category": "chair"
    })

    # 5. Unseen TU-Berlin sketches (Airplane & Cup)
    airplane_idx = class_to_idx["airplane"]
    tu_matches = np.where(tu_y == airplane_idx)[0]
    if len(tu_matches) > 0:
        tu_airplane = tu_X[tu_matches[0]]
        tu_canvas = 255 - cv2.resize(tu_airplane, (512, 512), interpolation=cv2.INTER_AREA)
        tu_bgr = cv2.cvtColor(tu_canvas, cv2.COLOR_GRAY2BGR)
        samples.append({
            "name": "TU_Berlin_Airplane",
            "category": "airplane",
            "type": "external_benchmark",
            "image": tu_bgr,
            "expected_category": "airplane"
        })

    cup_idx = class_to_idx["cup"]
    tu_cup_matches = np.where(tu_y == cup_idx)[0]
    if len(tu_cup_matches) > 0:
        tu_cup = tu_X[tu_cup_matches[0]]
        tu_canvas = 255 - cv2.resize(tu_cup, (512, 512), interpolation=cv2.INTER_AREA)
        tu_bgr = cv2.cvtColor(tu_canvas, cv2.COLOR_GRAY2BGR)
        samples.append({
            "name": "TU_Berlin_Cup",
            "category": "cup",
            "type": "external_benchmark",
            "image": tu_bgr,
            "expected_category": "cup"
        })

    return samples


def main():
    print("==================================================================")
    print(" SKETCH2SHAPE AI: RAW VS STAGE 5 PREPROCESSED COMPARISON SUITE   ")
    print("==================================================================")

    with open(MODELS_DIR / "class_mapping.json", "r", encoding="utf-8") as f:
        class_mapping = json.load(f)

    engine = SketchIntelligenceEngine()
    test_samples = create_test_samples(class_mapping)

    comparison_results = []

    print(f"\nEvaluating {len(test_samples)} diverse test cases under both modalities...\n")

    for s in test_samples:
        name = s["name"]
        img = s["image"]
        expected = s["expected_category"]
        stype = s["type"]

        print(f"--- [Test Sample: {name} ({stype})] ---")

        # 1. Raw Evaluation (bypass_preprocessing = True)
        try:
            raw_res = engine.analyze(img, bypass_preprocessing=True)
            raw_pred = raw_res["predicted_category"]
            raw_conf = raw_res["top_confidence"]
            raw_ambiguous = raw_res["is_ambiguous"]
            raw_time = raw_res["processing_time_ms"]
        except Exception as e:
            raw_pred = f"ERROR: {e}"
            raw_conf = 0.0
            raw_ambiguous = True
            raw_time = 0.0

        # 2. Preprocessed Evaluation (bypass_preprocessing = False)
        try:
            prep_res = engine.analyze(img, bypass_preprocessing=False)
            prep_pred = prep_res["predicted_category"]
            prep_conf = prep_res["top_confidence"]
            prep_ambiguous = prep_res["is_ambiguous"]
            prep_tags = prep_res["geometric_tags"]
            prep_desc = prep_res["semantic_description"]
            prep_hints = prep_res["reconstruction_hints"]
            prep_time = prep_res["processing_time_ms"]
        except Exception as e:
            prep_pred = f"REJECTED/ERROR: {e}"
            prep_conf = 0.0
            prep_ambiguous = True
            prep_tags = []
            prep_desc = "None"
            prep_hints = {}
            prep_time = 0.0

        print(f"  Raw Input    : Pred='{raw_pred}' (Conf: {raw_conf:.2f}, Ambiguous: {raw_ambiguous}) in {raw_time} ms")
        print(f"  Preprocessed : Pred='{prep_pred}' (Conf: {prep_conf:.2f}, Ambiguous: {prep_ambiguous}) in {prep_time} ms")
        if prep_tags:
            print(f"  Tags Extracted: {prep_tags}")
            print(f"  Description   : {prep_desc}")

        comparison_results.append({
            "sample_name": name,
            "sample_type": stype,
            "expected_category": expected,
            "raw_mode": {
                "predicted": raw_pred,
                "confidence": raw_conf,
                "is_ambiguous": raw_ambiguous,
                "latency_ms": raw_time
            },
            "preprocessed_mode": {
                "predicted": prep_pred,
                "confidence": prep_conf,
                "is_ambiguous": prep_ambiguous,
                "geometric_tags": prep_tags,
                "semantic_description": prep_desc,
                "reconstruction_hints": prep_hints,
                "latency_ms": prep_time
            }
        })
        print()

    # Save comparison report
    EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)
    out_file = EXPERIMENTS_DIR / "preprocessing_impact_comparison.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(comparison_results, f, indent=2)

    print(f"Comparison report saved to: {out_file}")


if __name__ == "__main__":
    main()

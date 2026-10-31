"""
Stage 6: Dataset Preparation for Sketch Intelligence Engine
Parses Google QuickDraw simplified NDJSON files incrementally for 50 3D-relevant categories.
Renders vector strokes to 128x128 grayscale images, deduplicates, and creates stratified
70% train / 15% validation / 15% test splits.
Also extracts external evaluation sketches from TU-Berlin for the mapped categories.
"""

import os
import sys
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Any
import numpy as np
import cv2
import pyarrow.parquet as pq
from sklearn.model_selection import train_test_split

# Ensure UTF-8 stdout on Windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE_DIR = Path(r"C:\Sketch2Shape-AI")
QD_RAW_DIR = BASE_DIR / "datasets" / "quickdraw" / "raw"
TU_RAW_DIR = BASE_DIR / "datasets" / "tu_berlin" / "raw"
TU_META_DIR = BASE_DIR / "datasets" / "tu_berlin" / "metadata"

OUT_DATASET_DIR = BASE_DIR / "datasets" / "sketch_intelligence"
OUT_MODELS_DIR = BASE_DIR / "models" / "sketch_intelligence"

# 50 Selected High-Value 3D & Common Object Categories with 1-to-1 TU-Berlin mapping
TARGET_CATEGORIES = [
    # 6 Mandatory test classes
    ("airplane", "airplane"),
    ("apple", "apple"),
    ("bicycle", "bicycle"),
    ("car", "car (sedan)"),
    ("chair", "chair"),
    ("cup", "cup"),
    # 44 Additional representative 3D categories
    ("alarm_clock", "alarm clock"),
    ("axe", "axe"),
    ("banana", "banana"),
    ("baseball_bat", "baseball bat"),
    ("basket", "basket"),
    ("bathtub", "bathtub"),
    ("bed", "bed"),
    ("bench", "bench"),
    ("book", "book"),
    ("bridge", "bridge"),
    ("bus", "bus"),
    ("butterfly", "butterfly"),
    ("cactus", "cactus"),
    ("cake", "cake"),
    ("calculator", "calculator"),
    ("camera", "camera"),
    ("candle", "candle"),
    ("cannon", "cannon"),
    ("canoe", "canoe"),
    ("castle", "castle"),
    ("cell_phone", "cell phone"),
    ("couch", "couch"),
    ("crown", "crown"),
    ("door", "door"),
    ("eyeglasses", "eyeglasses"),
    ("fan", "fan"),
    ("fish", "fish"),
    ("flashlight", "flashlight"),
    ("fork", "fork"),
    ("guitar", "guitar"),
    ("hammer", "hammer"),
    ("hat", "hat"),
    ("helicopter", "helicopter"),
    ("house", "house"),
    ("knife", "knife"),
    ("mushroom", "mushroom"),
    ("piano", "piano"),
    ("scissors", "scissors"),
    ("shoe", "shoe"),
    ("spoon", "spoon"),
    ("sword", "sword"),
    ("table", "table"),
    ("tree", "tree"),
    ("wine_glass", "wineglass"),
]


def render_drawing_to_128(drawing: list, target_size: int = 128, stroke_width: int = 2) -> np.ndarray:
    """
    Renders QuickDraw vector strokes to a 128x128 grayscale image.
    Strokes = 255 (high intensity foreground), Background = 0.
    """
    canvas = np.zeros((target_size, target_size), dtype=np.uint8)
    scale = (target_size - 16) / 255.0
    offset = 8

    for stroke in drawing:
        pts = []
        for x, y in zip(stroke[0], stroke[1]):
            pts.append((int(x * scale + offset), int(y * scale + offset)))
        if len(pts) > 1:
            pts_arr = np.array(pts, dtype=np.int32).reshape((-1, 1, 2))
            cv2.polylines(canvas, [pts_arr], False, 255, stroke_width, cv2.LINE_AA)
        elif len(pts) == 1:
            cv2.circle(canvas, pts[0], stroke_width, 255, -1)

    return canvas


def compute_drawing_hash(drawing: list) -> str:
    """Computes a SHA-256 hash of stroke coordinates for exact deduplication."""
    serialized = json.dumps(drawing, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def load_quickdraw_subset(samples_per_class: int = 1000) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    print(f"\n[1/3] Ingesting QuickDraw dataset ({len(TARGET_CATEGORIES)} categories, max {samples_per_class} samples each)...")
    t0 = time.time()

    images_list = []
    labels_list = []
    category_names = [qd for qd, _ in TARGET_CATEGORIES]
    class_to_idx = {name: i for i, name in enumerate(category_names)}
    idx_to_class = {i: name for i, name in enumerate(category_names)}

    total_valid = 0
    total_duplicates_removed = 0

    for idx, (qd_name, _) in enumerate(TARGET_CATEGORIES):
        file_path = QD_RAW_DIR / f"{qd_name}.ndjson"
        if not file_path.exists():
            raise FileNotFoundError(f"QuickDraw file not found: {file_path}")

        seen_hashes = set()
        class_samples = 0

        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                except Exception:
                    continue

                if not data.get("recognized", True):
                    continue

                drawing = data.get("drawing", [])
                if not drawing:
                    continue

                # Deduplication check
                d_hash = compute_drawing_hash(drawing)
                if d_hash in seen_hashes:
                    total_duplicates_removed += 1
                    continue
                seen_hashes.add(d_hash)

                img = render_drawing_to_128(drawing, target_size=128, stroke_width=2)
                images_list.append(img)
                labels_list.append(idx)
                class_samples += 1

                if class_samples >= samples_per_class:
                    break

        total_valid += class_samples
        if (idx + 1) % 10 == 0 or idx == len(TARGET_CATEGORIES) - 1:
            print(f"  Processed {idx + 1}/{len(TARGET_CATEGORIES)} classes: {total_valid} images (removed {total_duplicates_removed} duplicates)")

    elapsed = time.time() - t0
    images = np.array(images_list, dtype=np.uint8)
    labels = np.array(labels_list, dtype=np.int64)

    meta = {
        "num_classes": len(category_names),
        "total_samples": int(len(images)),
        "samples_per_class": samples_per_class,
        "duplicates_filtered": total_duplicates_removed,
        "extraction_duration_sec": round(elapsed, 2),
        "class_to_idx": class_to_idx,
        "idx_to_class": idx_to_class,
    }

    print(f"QuickDraw ingestion complete in {elapsed:.2f}s: {images.shape[0]} total samples.")
    return images, labels, meta


def extract_tu_berlin_eval_set(class_to_idx: Dict[str, int]) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    print(f"\n[2/3] Extracting TU-Berlin external evaluation set for mapped categories...")
    t0 = time.time()

    # Load TU-Berlin class label ID mapping
    with open(TU_META_DIR / "tu_berlin_class_names.json", "r", encoding="utf-8") as f:
        tu_class_names = json.load(f)
    tu_name_to_id = {v: int(k) for k, v in tu_class_names.items()}

    # Create map from TU-Berlin label ID -> QuickDraw unified class index
    tu_id_to_unified_idx = {}
    mapping_manifest = {}
    for qd_name, tu_name in TARGET_CATEGORIES:
        if tu_name in tu_name_to_id:
            tu_id = tu_name_to_id[tu_name]
            unified_idx = class_to_idx[qd_name]
            tu_id_to_unified_idx[tu_id] = unified_idx
            mapping_manifest[qd_name] = {
                "unified_index": unified_idx,
                "quickdraw_name": qd_name,
                "tu_berlin_name": tu_name,
                "tu_berlin_id": tu_id
            }

    # Read TU-Berlin parquet files
    parquet_files = sorted(list(TU_RAW_DIR.glob("*.parquet")))
    eval_images = []
    eval_labels = []

    for pf in parquet_files:
        table = pq.read_table(str(pf))
        label_col = table["label"].to_pylist()
        img_col = table["image"].to_pylist()

        for row_img, row_label in zip(img_col, label_col):
            if row_label in tu_id_to_unified_idx:
                raw_bytes = row_img["bytes"]
                nparr = np.frombuffer(raw_bytes, np.uint8)
                bgr = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
                if bgr is None:
                    continue

                # Resize to 128x128 and invert polarity (in TU-Berlin, strokes are black 0, bg is 255)
                # We invert so strokes are 255 and bg is 0, matching the classifier representation
                resized = cv2.resize(bgr, (128, 128), interpolation=cv2.INTER_AREA)
                inverted = 255 - resized

                eval_images.append(inverted)
                eval_labels.append(tu_id_to_unified_idx[row_label])

    eval_images = np.array(eval_images, dtype=np.uint8)
    eval_labels = np.array(eval_labels, dtype=np.int64)
    elapsed = time.time() - t0

    print(f"Extracted {len(eval_images)} TU-Berlin benchmark sketches across {len(mapping_manifest)} mapped classes in {elapsed:.2f}s.")
    return eval_images, eval_labels, mapping_manifest


def main():
    print("==================================================================")
    print(" SKETCH2SHAPE AI: DATASET EXTRACTION & STRATIFIED PARTITIONING    ")
    print("==================================================================")

    OUT_DATASET_DIR.mkdir(parents=True, exist_ok=True)
    OUT_MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Ingest QuickDraw
    images, labels, meta = load_quickdraw_subset(samples_per_class=1000)

    # 2. Stratified 70% Train, 15% Val, 15% Test Split
    print("\n[3/3] Creating stratified splits (70% Train, 15% Val, 15% Test, Seed=42)...")
    train_idx, temp_idx = train_test_split(
        np.arange(len(labels)),
        test_size=0.30,
        random_state=42,
        stratify=labels
    )
    val_idx, test_idx = train_test_split(
        temp_idx,
        test_size=0.50,
        random_state=42,
        stratify=labels[temp_idx]
    )

    X_train, y_train = images[train_idx], labels[train_idx]
    X_val, y_val = images[val_idx], labels[val_idx]
    X_test, y_test = images[test_idx], labels[test_idx]

    print(f"  Training Set   : {len(X_train)} samples ({len(X_train)/len(labels)*100:.1f}%)")
    print(f"  Validation Set : {len(X_val)} samples ({len(X_val)/len(labels)*100:.1f}%)")
    print(f"  Testing Set    : {len(X_test)} samples ({len(X_test)/len(labels)*100:.1f}%)")

    # 3. Extract TU-Berlin external benchmark set
    tu_images, tu_labels, mapping_manifest = extract_tu_berlin_eval_set(meta["class_to_idx"])

    # 4. Save artifacts
    print("\nSaving dataset splits to disk...")
    np.save(OUT_DATASET_DIR / "X_train.npy", X_train)
    np.save(OUT_DATASET_DIR / "y_train.npy", y_train)
    np.save(OUT_DATASET_DIR / "X_val.npy", X_val)
    np.save(OUT_DATASET_DIR / "y_val.npy", y_val)
    np.save(OUT_DATASET_DIR / "X_test.npy", X_test)
    np.save(OUT_DATASET_DIR / "y_test.npy", y_test)

    np.save(OUT_DATASET_DIR / "tu_berlin_X_test.npy", tu_images)
    np.save(OUT_DATASET_DIR / "tu_berlin_y_test.npy", tu_labels)

    # Save class mapping to models directory
    class_mapping_data = {
        "num_classes": len(TARGET_CATEGORIES),
        "target_categories": [qd for qd, _ in TARGET_CATEGORIES],
        "class_to_idx": meta["class_to_idx"],
        "idx_to_class": meta["idx_to_class"],
        "tu_berlin_mapping": mapping_manifest,
        "split_sizes": {
            "train": len(X_train),
            "val": len(X_val),
            "test": len(X_test),
            "tu_berlin_eval": len(tu_images)
        }
    }
    with open(OUT_MODELS_DIR / "class_mapping.json", "w", encoding="utf-8") as f:
        json.dump(class_mapping_data, f, indent=2)

    print(f"Class mapping and metadata saved to: {OUT_MODELS_DIR / 'class_mapping.json'}")
    print(f"All dataset partitions saved to: {OUT_DATASET_DIR}")
    print("Dataset preparation successfully completed!")


if __name__ == "__main__":
    main()

# 📁 Complete Dataset Inventory & Schema Architecture

**Document:** `docs/complete_dataset_inventory.md`  
**Platform:** Sketch2Shape AI  
**Author:** Lead AI/ML Autonomous Engineer  
**Stage:** Step 4 of 12 – Complete Multi-Dataset Ingestion  
**Status:** **ACTIVE / VERIFIED**

---

## 1. Directory Structure

```text
C:\Sketch2Shape-AI\datasets\
├── quickdraw/
│   ├── raw/                       # Simplified NDJSON files for all 345 categories (~22.5 GB)
│   │   ├── airplane.ndjson
│   │   ├── alarm_clock.ndjson
│   │   ├── apple.ndjson
│   │   └── ... [345 categories]
│   ├── processed/                 # Rasterized 28x28 / 64x64 stroke matrices for training
│   └── metadata/
│       ├── categories.txt         # Official list of 345 categories
│       ├── quickdraw_manifest.json# Per-file byte counts, verification, and sample counts
│       └── missing_categories.json# Error logs for failed/missing categories (0 failures)
├── tu_berlin/
│   ├── raw/                       # 20,080 human sketches in 3 parquet partitions (563.5 MB)
│   │   ├── train-00000-of-00002-cf60531eb207325d.parquet (278.96 MB)
│   │   ├── train-00001-of-00002-92131dc5d116063a.parquet (278.89 MB)
│   │   └── test-00000-of-00001-4c87e761e3fce046.parquet (5.64 MB)
│   ├── processed/                 # Extracted sample sketches by category
│   └── metadata/
│       ├── categories.txt         # 250 distinct categories (80 sketches per category)
│       └── tu_berlin_manifest.json# Category mapping and benchmark specifications
├── objaverse/
│   ├── metadata/                  # Full 818,299 model catalog and curated selections (86.7 MB)
│   │   ├── object-paths.json.gz   # Compressed catalog map (18.89 MB)
│   │   ├── object-paths.json      # Full 798,759 model UID to download path mapping
│   │   ├── curated_selection.json # Benchmark models filtered by categories & licenses
│   │   └── objaverse_manifest.json# Master Objaverse catalog manifest
│   └── selected_assets/           # High-precision validated 3D GLB models
│       ├── cup_fL2C0ucY.glb       (24 vertices, 12 faces)
│       ├── mug_yda6pYgu.glb       (53,004 vertices, 105,888 faces)
│       ├── mug_muGr4Jke.glb       (63,703 vertices, 110,006 faces)
│       ├── general_object_8476c417.glb (19,008 vertices, 14,337 faces)
│       └── general_object_8ff7f1f2.glb (4,346 vertices, 6,700 faces)
├── shapenet/
│   ├── metadata/                  # Taxonomy synset mappings and terms of use (1.2 MB)
│   │   ├── shapenet_taxonomy.json # 55 core categories with WordNet synset offsets & counts
│   │   ├── shapenet_access_policy.md # Compliance and registration conditions
│   │   └── shapenet_manifest.json # Master ShapeNet manifest
│   └── selected_assets/           # Optional authenticated research asset cache
├── manifests/
│   └── dataset_master_manifest.json # Unified cross-dataset catalog manifest
└── reports/
    ├── master_verification_report.json # Automated integrity audit results
    └── storage_consumption_report.json # Real-time disk capacity and footprint monitor
```

---

## 2. Dataset Schema Definitions

### 2.1 Google Quick, Draw! (Simplified NDJSON)
Each line represents one complete human sketch as a JSON object:

```json
{
  "key_id": "5123456789012345",
  "word": "airplane",
  "recognized": true,
  "timestamp": "2017-03-24 14:23:45.12345 UTC",
  "countrycode": "US",
  "drawing": [
    [
      [12, 14, 18, 25, 35],
      [40, 42, 45, 48, 50]
    ],
    [
      [100, 102, 105, 110],
      [80, 82, 85, 90]
    ]
  ]
}
```
* **`drawing` Format:** Array of strokes. Each stroke consists of two arrays: `[x_coordinates, y_coordinates]`. Coordinates are normalized on a $256 \times 256$ pixel grid, pre-simplified with the Ramer–Douglas–Peucker algorithm with an epsilon of 2.0.

### 2.2 TU-Berlin Sketch Dataset (Parquet Format)
Columns in `train` and `test` partitions:
* **`image`:** Dictionary containing raw PNG bytes (`bytes`) and format string (`path`).
* **`label`:** String category identifier (e.g. `airplane`, `alarm clock`, `apple`, `butterfly`, `camel`, etc. across 250 classes).

### 2.3 Objaverse 1.0 (GLB Format & Catalog)
* **`object-paths.json`:** Key-value map from Sketchfab Model UID $\rightarrow$ relative Hugging Face download path:
  `"fL2C0ucY89a1...": "glbs/000-050/fL2C0ucY89a1....glb"`
* **Asset Format:** Binary GLTF (`.glb`) containing geometry (vertices, normals, indices), PBR materials, and embedded textures.

### 2.4 ShapeNetCore Taxonomy Metadata
* **`synsetId`:** 8-digit WordNet synset identifier (e.g., `02691156` for `airplane`, `03001627` for `chair`).
* **`name`:** English category label.
* **`children`:** Sub-category synset IDs.
* **`numInstances`:** Verified 3D CAD models present in the ShapeNetCore repository.

---

## 3. Automation Scripts Catalog

| Script | Purpose | Execution Command |
| :--- | :--- | :--- |
| `scripts/download_all_quickdraw.py` | Multithreaded resumable downloader for all 345 QuickDraw categories with line verification | `python scripts/download_all_quickdraw.py` |
| `scripts/download_tu_berlin.py` | Downloader for the 250-category TU-Berlin sketch benchmark from verified mirror | `python scripts/download_tu_berlin.py` |
| `scripts/download_objaverse_metadata.py` | Full 798K+ model catalog & curated category filtering | `python scripts/download_objaverse_metadata.py` |
| `scripts/download_objaverse_assets.py` | Downloads & validates selected 3D GLB assets with Trimesh | `python scripts/download_objaverse_assets.py [count]` |
| `scripts/download_shapenet.py` | Taxonomy mapping & academic compliance setup | `python scripts/download_shapenet.py` |
| `scripts/verify_datasets.py` | Master verification audit across all four datasets | `python scripts/verify_datasets.py` |
| `scripts/calculate_dataset_storage.py` | Disk storage footprint & safety margin monitor | `python scripts/calculate_dataset_storage.py` |

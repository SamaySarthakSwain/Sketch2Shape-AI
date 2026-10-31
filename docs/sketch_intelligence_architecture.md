# Sketch Intelligence & Semantic Recognition Architecture

## 1. Overview

The **Sketch Intelligence Engine** (`backend/app/sketch_intelligence/`) constitutes Stage 6 of the Sketch2Shape AI system. It bridges low-level geometric and stroke analysis (from Stage 5 OpenCV preprocessing) with high-level semantic category recognition, calibrated uncertainty quantification, and 3D reconstruction conditioning for downstream generative models (**InstantMesh** and **Hunyuan3D**).

```
                            +-----------------------------------+
                            |  Input Sketch (User / Benchmark)  |
                            +-----------------+-----------------+
                                              |
                                              v
                            +-----------------------------------+
                            |    Stage 5 Preprocessing Engine   |
                            |  (Bilateral, CLAHE, Contours,     |
                            |   Skeleton, Symmetry, Moments)    |
                            +-----------------+-----------------+
                                              |
                   +--------------------------+--------------------------+
                   |                                                     |
                   v                                                     v
    +------------------------------+                      +------------------------------+
    |   Canonical 128x128 Tensor   |                      |  Stage 5 Quantitative Report |
    |   (Grayscale Stroke Mask)    |                      |  (Symmetry, PCA, Compactness)|
    +--------------+---------------+                      +--------------+---------------+
                   |                                                     |
                   v                                                     v
    +------------------------------+                      +------------------------------+
    |  Deep Sketch Classifier      |                      |  Geometric Feature Tagger    |
    |  (ResNet18-Adapted / CNN)    |                      |  (Documented Heuristics)     |
    +--------------+---------------+                      +--------------+---------------+
                   |                                                     |
                   v                                                     |
    +------------------------------+                                     |
    |  Uncertainty Estimator       |                                     |
    |  Top-5, Softmax, Conf. Gap,  |                                     |
    |  Ambiguity Detection         |                                     |
    +--------------+---------------+                                     |
                   |                                                     |
                   +--------------------------+--------------------------+
                                              |
                                              v
                            +-----------------------------------+
                            |  Semantic Description Generator   |
                            |  Natural Language Summary & Hints |
                            +-----------------+-----------------+
                                              |
                                              v
                            +-----------------------------------+
                            |  3D Reconstruction Conditioning   |
                            |  Decoupled Metadata for 3D Engine |
                            +-----------------------------------+
```

---

## 2. Directory & Module Organization

```
backend/app/sketch_intelligence/
├── __init__.py                     # Public interface exports
├── models.py                       # LightweightCNN & ResNet18Sketch PyTorch architectures
├── classifier.py                   # High-level SketchIntelligenceEngine coordinator
├── uncertainty.py                  # Epistemic uncertainty & confidence-gap quantifier
├── geometry_tags.py                # Heuristic geometric feature tagging engine
├── semantic_generator.py           # Deterministic natural language & structural priors
└── reconstruction_conditioning.py  # Decoupled 3D metadata conditioning payload builder

backend/app/routes/
└── intelligence.py                 # FastAPI endpoints (/analyze, /health)

scripts/sketch_intelligence/
├── prepare_dataset.py              # Incremental QuickDraw & TU-Berlin ingestor & splitter
├── train_and_compare.py            # Comparative training, AMP, evaluation & confusion matrix
└── test_pipeline_comparison.py     # Evaluation on raw vs preprocessed sketches

models/sketch_intelligence/
├── best_model.pth                  # Saved weights of the top-performing architecture
├── model_config.json               # Architecture hyperparameters, device & latency
├── class_mapping.json              # 50 target classes & TU-Berlin alignment map
├── training_history.json           # Train/Val loss, top-1 & top-5 accuracy curves
├── evaluation_metrics.json         # Macro precision, recall, F1, and TU-Berlin benchmark
├── confusion_matrix.png            # 50x50 normalized confusion matrix plot
└── model_comparison.json           # Head-to-head parameter, latency & accuracy comparison

experiments/sketch_intelligence/
├── training_run_summary.json       # Detailed training run snapshot
└── preprocessing_impact_comparison.json # Raw vs Preprocessed empirical benchmark
```

---

## 3. Dataset & Taxonomy Alignment

### 3.1 Google QuickDraw (Training Split)
- **50 Targeted Categories:** 6 mandatory test classes (`chair`, `car`, `airplane`, `bicycle`, `cup`, `apple`) plus 44 representative 3D everyday objects, furniture, tools, and structures.
- **1,000 Samples per Category:** 50,000 total verified vector drawings rendered to $128 \times 128$ stroke images.
- **Deduplication:** SHA-256 hash computed over serialized stroke coordinate tuples to eliminate duplicate sketches.
- **Stratified Split (Seed 42):**
  - **Training:** 35,000 samples (70%)
  - **Validation:** 7,500 samples (15%)
  - **Testing:** 7,500 samples (15%)

### 3.2 TU-Berlin (External Evaluation Benchmark)
- **100% Unseen External Dataset:** 4,000 real hand-drawn human sketches across the exact 50 mapped classes (80 sketches per category).
- Strictly separated from training and validation to verify generalization to genuine human strokes.

---

## 4. Deep Learning Architectures

### Architecture A: Lightweight Custom CNN
- **Parameters:** ~664,082 (~0.66M)
- **Structure:** 4 convolutional blocks (1 -> 32 -> 64 -> 128 -> 256), each with BatchNorm, ReLU, and MaxPool2d(2, 2), followed by AdaptiveAvgPool2d(2, 2), Dropout(0.35), and FC-256-Classifier.
- **Optimized for:** Ultra-fast, edge-capable CPU/mobile inference with sub-millisecond execution.

### Architecture B: ResNet18-Adapted
- **Parameters:** ~11,195,890 (~11.2M)
- **Adaptation:** First convolutional layer modified from 3-channel RGB to 1-channel grayscale input (`in_channels=1, kernel_size=7, stride=2, padding=3`). Output classification head adapted to 50 classes.
- **Optimized for:** Deep residual representation, multi-scale receptive field, and high generalization across varied artistic styles.

---

## 5. Uncertainty Quantification & Ambiguity State

Softmax confidence scores are explicitly treated as **uncalibrated relative scores**. To capture true epistemic ambiguity, the system evaluates:
1. **Top-1 Confidence ($p_1$):** Maximum softmax probability.
2. **Confidence Gap ($\Delta$):** Difference between rank-1 and rank-2 candidates:
   $$\Delta = p_1 - p_2$$
3. **Ambiguity Classification:**
   - **Ambiguous (`is_ambiguous = True`, `uncertainty_level = "high"`):** Triggered when $p_1 < 0.40$ OR $\Delta < 0.15$.
   - **Moderate (`is_ambiguous = False`, `uncertainty_level = "moderate"`):** Triggered when $0.40 \le p_1 < 0.70$ and $\Delta \ge 0.15$.
   - **Low Uncertainty (`is_ambiguous = False`, `uncertainty_level = "low"`):** Triggered when $p_1 \ge 0.70$ and $\Delta \ge 0.30$.
4. **Plausible Alternatives:** Returns all candidate classes with $p_k \ge \max(0.08, 0.25 \cdot p_1)$.

---

## 6. Geometric Feature Tagging Heuristics

All thresholds are derived from physical geometry and documented:

| Tag | Condition / Threshold | Physical Interpretation |
|---|---|---|
| `approximately_symmetric` | Centroid-centered IoU $\ge 0.60$ | High bilateral reflectional symmetry |
| `predominantly_horizontal` | Dominant PCA angle $|\theta| \le 20^\circ$ | Longitudinal horizontal mass axis |
| `predominantly_vertical` | Dominant PCA angle $|\theta| \ge 70^\circ$ | Upright vertical structural axis |
| `elongated` | Aspect Ratio $W/H \ge 1.70$ or $\le 0.58$ | Slender, non-isometric geometry |
| `circular_structure` | Isoperimetric Compactness $4\pi A / P^2 \ge 0.65$ | Circular or disk-shaped boundary |
| `thin_structure` | Stroke Density $\le 0.05$ or Width $\le 3.5\text{px}$ | Delicate, wireframe, or spindly strokes |
| `complex_contour` | Contour Complexity $P / P_{\text{hull}} \ge 1.75$ | Detailed, tortuous, or branching boundary |
| `multiple_components` | Connected Components Count $\ge 3$ | Disconnected structural sub-elements |
| `enclosed_region` | Internal Hole Count $\ge 1$ or Depth $\ge 2$ | Closed loop cavities (e.g. windows, holes) |

---

## 7. Decoupled 3D Reconstruction Conditioning Interface

```json
{
  "category": "chair",
  "semantic_prompt": "A single 3D chair, isolated, centered, complete object, clean geometry.",
  "geometry_constraints": {
    "symmetry_prior": true,
    "orientation": "vertical",
    "component_count": 3
  },
  "uncertainty": {
    "is_ambiguous": false,
    "top_prediction_confidence": 0.9124
  }
}
```

This decoupled payload guarantees that future diffusion models or geometric extruders can enforce planar reflection symmetry, canonical yaw/pitch rotations, and multi-mesh isolation without tampering with InstantMesh's raw image triplane representation.

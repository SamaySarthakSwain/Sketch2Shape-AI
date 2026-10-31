# OpenCV Sketch Preprocessing & Stroke Analysis Engine Architecture

## 1. System Overview

The **Sketch2Shape AI Preprocessing Engine** (`backend/app/preprocessing/`) is an advanced, modular computer vision pipeline built with OpenCV, NumPy, and SciPy. Its primary objective is to transform raw, noisy, hand-drawn 2D sketches (raster sketches, tablet uploads, vector drawings, transparent PNGs) into canonical, geometrically quantified representations optimized for downstream multi-view diffusion and 3D reconstruction models (specifically **InstantMesh** and **Hunyuan3D**).

```
                        +----------------------------+
                        |  Raw Input Image / Sketch  |
                        +--------------+-------------+
                                       |
                                       v
                        +----------------------------+
                        |   ImageLoader & Validator  |
                        +--------------+-------------+
                                       |
                   +-------------------+-------------------+
                   |                                       |
                   v                                       v
    +-----------------------------+         +-----------------------------+
    |   Image Enhancement         |         |   Foreground Extraction     |
    |   (CLAHE & Illum. Corr.)    |         |   (Alpha / Binarization)    |
    +--------------+--------------+         +--------------+--------------+
                   |                                       |
                   v                                       v
    +-----------------------------+         +-----------------------------+
    |   Bilateral Denoising       |         |   Connected Components      |
    |   & Edge Detection          |         |   Speckle Noise Filtering   |
    +--------------+--------------+         +--------------+--------------+
                   |                                       |
                   +-------------------+-------------------+
                                       |
                                       v
                        +----------------------------+
                        |   Adaptive Binarization    |
                        |   (255 = stroke, 0 = bg)   |
                        +--------------+-------------+
                                       |
                   +-------------------+-------------------+
                   |                   |                   |
                   v                   v                   v
     +-------------------+   +-------------------+   +-------------------+
     | Contour Topology  |   | Stroke Skeleton & |   | Symmetry & Shape  |
     | Area, Solidity,   |   | Distance Xform    |   | Centroid Moments, |
     | Hierarchy Depth   |   | Graph Analysis    |   | PCA Orientation   |
     +---------+---------+   +---------+---------+   +---------+---------+
               |                       |                       |
               +-------------------+---+-----------------------+
                                   |
                                   v
                    +-----------------------------+
                    |  Reconstruction Normalizer  |
                    |  512x512 Canvas, Centered,  |
                    |  12% Padding, White BG      |
                    +--------------+--------------+
                                   |
                                   v
                    +-----------------------------+
                    |  9 Output Image Variants &  |
                    |  Structured JSON Metrics    |
                    +-----------------------------+
```

---

## 2. Module Directory Structure

```
backend/app/preprocessing/
├── __init__.py                  # Clean public exports for all modules and schemas
├── schemas.py                   # Strongly typed dataclasses for metrics and reports
├── image_loader.py              # Multi-source image decoding and background compositing
├── image_validation.py          # Format, dimension, size, and blank-sketch checks
├── enhancement.py               # Contrast stretching, CLAHE, and illumination correction
├── denoising.py                 # Bilateral, Gaussian, Median, and Non-Local Means filters
├── edge_detection.py            # Auto-Canny (Otsu median), Sobel, Laplacian, Scharr
├── thresholding.py              # Adaptive Gaussian/Mean thresholding and morphology
├── foreground_extraction.py     # Connected-component analysis and alpha cutout
├── contour_analysis.py          # Outer envelopes, internal holes, hierarchy depth, solidity
├── skeletonization.py           # 1-pixel centerline thinning (Guo-Hall / Zhang-Suen)
├── stroke_analysis.py           # Distance transform width, graph endpoints/junctions
├── symmetry_analysis.py         # Centroid-centered bilateral reflection symmetry (IoU)
├── shape_analysis.py            # PCA orientation angle, compactness, eccentricity
├── normalization.py             # Canonical 512x512 reconstruction tensor generation
├── visualization.py             # 9-panel diagnostic visualizer and base64 export
└── preprocessing_pipeline.py    # Master end-to-end execution pipeline
```

---

## 3. The 12 Pipeline Phases

### Phase 1: Ingestion & Format Normalization (`image_loader.py`)
- Accepts inputs from local disk paths, raw byte arrays, base64 data URLs, PIL images, and NumPy arrays.
- Inspects channel depth (1, 3, or 4 channels). For 4-channel RGBA inputs, it isolates the alpha channel as an exact transparency mask.
- Composites transparent sketches over a uniform matte canvas (default: pure white `(255, 255, 255)`).

### Phase 2: Input Validation (`image_validation.py`)
- Rejects images outside standard dimensions ($16 \le \text{width, height} \le 8192$ pixels).
- Rejects payload sizes exceeding 50 MB.
- Calculates image variance: images with $\text{Var}(I) < 1.0$ (blank or uniform white/black canvases) are rejected immediately to prevent downstream crash loops.

### Phase 3: Contrast Enhancement (`enhancement.py`)
- Analyzes intensity histograms.
- Applies **Contrast Limited Adaptive Histogram Equalization (CLAHE)** with `clipLimit=2.5, tileGridSize=(8, 8)` to amplify faint pencil and pen strokes without blowing out paper texture.
- Corrects non-uniform illumination and vignetting using morphological top-hat background estimation:
  $$\hat{I} = I - (I \circ B)$$
  where $B$ is a large structuring element ($51 \times 51$).

### Phase 4: Noise Reduction (`denoising.py`)
- Applies **Bilateral Filtering** ($d=7, \sigma_c=50, \sigma_s=50$) to smooth sensor noise and paper grain while preserving step edges.
- Provides optional Non-Local Means (NLM) filtering for heavily degraded scan inputs.

### Phase 5: Edge Detection (`edge_detection.py`)
- Computes **Auto-Canny** edge maps by estimating adaptive upper/lower thresholds from intensity distribution:
  $$T_{\text{lower}} = \max(0, (1 - \sigma) \cdot M), \quad T_{\text{upper}} = \min(255, (1 + \sigma) \cdot M)$$
  where $M$ is the median grayscale intensity and $\sigma = 0.33$.
- Measures quantitative edge density:
  $$\rho_{\text{edge}} = \frac{\sum E(x, y)}{W \times H}$$

### Phase 6: Adaptive Thresholding & Morphology (`thresholding.py`)
- Implements Adaptive Gaussian and Adaptive Mean thresholding ($C=5, \text{blockSize}=15$).
- Analyzes corner intensities to detect stroke polarity automatically. If the background is bright, the polarity is inverted so that **255 represents stroke foreground** and **0 represents background**.
- Applies morphological closing ($3 \times 3$ ellipse) to fuse micro-discontinuities in hurried strokes.

### Phase 7: Foreground Extraction (`foreground_extraction.py`)
- Executes 8-way connected-component labeling.
- Measures the pixel area of every connected island; components smaller than 25 pixels are filtered out as paper speckle noise.
- Generates an exact RGBA cutout.

### Phase 8: Contour Topology & Hierarchy (`contour_analysis.py`)
- Extracts full hierarchy with `cv2.RETR_TREE` and `cv2.CHAIN_APPROX_SIMPLE`.
- Computes convex hull, contour perimeter ($P$), area ($A$), bounding box, and bounding rectangle.
- Measures **Solidity** ($A / A_{\text{hull}}$) and **Extent** ($A / A_{\text{bbox}}$).
- Measures maximum tree hierarchy depth to identify multi-nested features (e.g., holes, eyes, wheels).

### Phase 9: Stroke Topology & Graph Analysis (`stroke_analysis.py`, `skeletonization.py`)
- Generates a 1-pixel wide centerline using morphological thinning.
- Computes exact Euclidean Distance Transform ($L_2$) on the binary foreground mask.
- Evaluates stroke width along the skeleton:
  $$W_{\text{stroke}} = 2.0 \times \text{mean}(DT(\text{skeleton}))$$
- Executes $3 \times 3$ neighbor convolution across the skeleton to detect topological **endpoints** (degree 1) and **junctions** (degree $\ge 3$).

### Phase 10: Reflectional Symmetry (`symmetry_analysis.py`)
- Translates the sketch mask so its centroid coincides exactly with the canvas center.
- Flips the mask horizontally and vertically, computing the Intersection-over-Union (IoU):
  $$\text{IoU}(M, M') = \frac{|M \cap M'|}{|M \cup M'|}$$
- Reports calibrated reflection symmetry scores for 3D alignment.

### Phase 11: Shape Analysis & PCA Orientation (`shape_analysis.py`)
- Extracts spatial moments ($\mu_{20}, \mu_{02}, \mu_{11}$).
- Constructs the 2D covariance matrix and performs **Principal Component Analysis (PCA)** to find the dominant orientation vector:
  $$\theta = \frac{1}{2} \arctan\left(\frac{2 \mu_{11}}{\mu_{20} - \mu_{02}}\right)$$
- Computes circular compactness (isoperimetric quotient):
  $$C = \frac{4 \pi A}{P^2}$$
- Computes eccentricity from inertia eigenvalues.

### Phase 12: Reconstruction Normalization (`normalization.py`)
- Computes the tight bounding box around all stroke pixels.
- Crops the foreground sketch and places it on a canonical **$512 \times 512$** canvas.
- Applies isotropic scaling preserving the original aspect ratio, with a guaranteed **12% safety margin** (padding).
- Exports standard 3-channel RGB (white background) and 4-channel RGBA (transparent) tensors ready for instant neural inference.

---

## 4. Nine Output Image Representations

Every execution of `SketchPreprocessingPipeline.process()` produces nine distinct diagnostic and inference representations:

1. `original_image`: Unaltered user input (BGR).
2. `enhanced_image`: Contrast-stretched, illumination-corrected grayscale.
3. `denoised_image`: Bilateral-filtered image with crisp stroke boundaries.
4. `binary_image`: Clean binary foreground mask ($255 = \text{stroke}$).
5. `edge_image`: Canny edge map highlighting structural boundaries.
6. `contour_visualization`: Color-coded contours (green = outer, red = internal holes).
7. `skeleton_image`: 1-pixel topological centerline graph.
8. `foreground_mask`: Centered, padded binary mask at $512 \times 512$.
9. `final_reconstruction_input`: Canonical $512 \times 512$ RGB image on white background for InstantMesh / Hunyuan3D.

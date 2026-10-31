# Sketch2Shape AI — End-to-End User Workflow Guide

## 1. Introduction

Sketch2Shape AI transforms rapid hand-drawn 2D concepts into interactive, watertight 3D models with real-time semantic intelligence and multi-model neural reconstruction. This document details the end-to-end user journey across all features of the interactive studio.

---

## 2. Step-by-Step User Journey

```
+----------------------------------------------------------------------------------------------------+
| 1. Input Conception  -->  2. Semantic Intelligence  -->  3. Model & Presets  -->  4. 3D Inspection |
|   - Draw on canvas         - Auto-categorization         - InstantMesh (AI)        - OrbitControls |
|   - Upload image           - Uncertainty gauge           - Procedural (Instant)    - Wireframe mode|
|   - Sample library         - Geometric prior tags        - Quality setting         - GLB/OBJ Export|
+----------------------------------------------------------------------------------------------------+
```

### Step 1: Providing the 2D Sketch
Users have three convenient options to input their sketch:
1. **Interactive HTML5 Drawing Canvas:**
   - Click the "Draw Sketch" tab on the left panel.
   - Select drawing tools: Freehand Pencil or Eraser.
   - Adjust the stroke width using the interactive slider (1px to 32px).
   - Use "Undo" / "Redo" buttons to refine strokes, or "Clear Canvas" to restart.
   - Drawing automatically streams to the semantic intelligence engine.
2. **File Upload (Drag-and-Drop):**
   - Click the "Upload File" tab on the left panel.
   - Drag and drop any PNG, JPEG, WEBP, or SVG image into the target zone, or click to browse files.
   - Instant file validation ensures size is within limits (< 20MB) and format is supported.
   - Uploaded sketches are immediately displayed in high-resolution preview.
3. **Quick-Load Sample Benchmark Library:**
   - Choose from 6 pre-verified benchmark sketches:
     - **Chair:** Classic furniture benchmark with 4 legs and backrest.
     - **Car:** Aerodynamic vehicle profile with wheels.
     - **Airplane:** Swept-wing aircraft with fuselage and vertical stabilizer.
     - **Cup:** Cylindrical tableware with handle.
     - **Bicycle:** Lightweight frame with two wheels and handlebars.
     - **Apple:** Organic spherical fruit with stem.
   - Clicking any benchmark automatically loads the normalized sketch, triggers classification, and sets optimal reconstruction parameters.

---

### Step 2: Inspecting Semantic Intelligence & Feature Tagging
As soon as a sketch is provided:
- The **ResNet-18 Adapted Sketch Intelligence Engine** analyzes the sketch in under 150 milliseconds.
- **Predicted Category & Confidence:** The primary object class (e.g., "Chair", 94.2%) is highlighted with a color-coded confidence badge.
- **Top-5 Probability Distribution:** The bar chart visualizes alternative semantic classes, indicating whether the sketch is ambiguous or unambiguous.
- **Geometric Prior Tags:** Automated feature extraction highlights structural properties:
  - `bilateral_symmetry`: Indicates reflective symmetry along vertical axis.
  - `multiple_components`: Identifies distinct disconnected parts (e.g. wheels, legs).
  - `rotational_symmetry`: Detects circular or radial profile.
  - `thin_structure`: Flags delicate features requiring reinforced mesh boundaries.
- **Manual Category Override:** If the user sketched a unique or stylized variation, they can select a manual category override from the searchable dropdown without modifying their original sketch.

---

### Step 3: Configuring the 3D Reconstruction Engine
Users configure synthesis parameters tailored to their hardware and fidelity requirements:
1. **Model Selection:**
   - **Auto (Intelligent Routing):** Automatically pairs the sketch category and geometry with the optimal engine.
   - **InstantMesh (TencentARC):** Primary deep diffusion + LRM triplane neural engine, producing rich multi-view geometric reconstructions.
   - **Procedural SDF & Revolution Engine:** Zero-VRAM, sub-second engine producing guaranteed watertight meshes ($\chi=2$) with analytical topology. Ideal for rapid iteration or lower-power hardware.
   - **Tencent Hunyuan3D-2:** Flagged with high-VRAM requirement (requires $\ge 6\text{ GB}$ VRAM); triggers Colab Pro integration if selected.
   - **TripoSR:** High-speed feedforward transformer model.
2. **Quality Presets:**
   - **Fast (Low Latency):** Optimized for instant previews.
   - **Balanced (Default):** Optimal trade-off between inference speed and surface detail.
   - **High Quality (Maximum Detail):** High-density Marching Cubes grid and maximum polygon resolution.
   - **Real-Time (Procedural):** Sub-second generation.
3. **OpenCV Preprocessing Toggle:**
   - Enabled by default: Applies bilateral denoising, Otsu adaptive thresholding, morphological stroke enhancement, and bounding-box normalization before passing to neural weights.
4. **Export Formats:**
   - Multi-select checkboxes for **GLB** (Binary GLTF with materials) and **OBJ** (Wavefront OBJ + MTL).

---

### Step 4: 3D Synthesis & Real-Time Progress Tracking
When the user clicks **"Generate 3D Asset"**:
- The status bar reflects honest, real-time pipeline stages:
  1. `uploading`: Encoding and ingesting sketch tensor.
  2. `analyzing`: Evaluating stroke geometry and symmetry.
  3. `generating`: Running multi-view diffusion and triplane reconstruction.
  4. `processing`: Executing Trimesh Laplacian smoothing and topological repair.
  5. `exporting`: Packaging watertight GLB and OBJ files.
  6. `completed`: Instantly rendering the 3D model in the WebGL viewport.

---

### Step 5: Interactive 3D Inspection & Telemetry
The right-hand studio panel provides full interactive control:
- **OrbitControls Navigation:**
  - Left click + drag: Rotate camera freely around model pivot.
  - Right click + drag: Pan camera laterally and vertically.
  - Scroll wheel: Zoom in/out with soft damping limits.
- **Viewport Toolbar:**
  - **Turntable (Auto-Rotate):** Smoothly orbits the camera for presentation.
  - **Wireframe Mode:** Renders underlying triangle mesh edges to inspect topology and polygon distribution.
  - **Ground Grid:** Toggles coordinate ground grid to inspect orientation and scale.
  - **Reset Camera:** Restores canonical perspective view.
  - **Fullscreen:** Expands viewport to full display resolution.
- **Real Mesh Diagnostics Panel:**
  - Shows verified metrics directly from Python Trimesh:
    - **Vertices & Faces:** Exact polygon count (e.g. 4,802 vertices, 9,600 faces).
    - **Watertight Status:** Validates 2-manifold closed surface with zero border edges.
    - **Euler Characteristic ($\chi$):** Topological sanity metric ($\chi=2$ denotes spherical topology).
    - **Bounding Box Dimensions:** Real physical dimensions in world coordinates $(X, Y, Z)$.
    - **Inference Latency:** Precise backend generation duration in seconds.

---

### Step 6: Multi-Format Asset Export & Download
- The **Export Panel** unlocks immediate download buttons:
  - **Download GLB:** Single binary package compatible with Blender, Unity, Unreal Engine, WebGL, Apple QuickLook, and Three.js.
  - **Download OBJ:** Standard Wavefront OBJ format compatible with CAD and legacy 3D DCC tools.
- Displays exact on-disk file size in kilobytes before downloading.

---

### Step 7: Local History & Session Replay
- Every generation is automatically recorded in the local history drawer.
- Users can click the **History** button in the navigation bar to slide open past models.
- Each history card displays:
  - Sketch thumbnail.
  - Recognized category and confidence.
  - Generation timestamp.
  - Exact polygon counts.
  - "View in 3D" button to reload the model into the active 3D viewport without re-running inference.
  - Direct download shortcut.

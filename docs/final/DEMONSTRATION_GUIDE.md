# Sketch2Shape AI — Hackathon Demonstration & Presentation Guide

---

### Demonstration Overview

This guide provides a structured, time-efficient demonstration script designed for hackathon judges, technical evaluators, and investors. It provides two demonstration workflows:
* **Track A:** **1-Click Curated Demonstration Mode** (Instantaneous, zero risk, guaranteed high visual polish).
* **Track B:** **Live Interactive Generation** (Live end-to-end AI execution demonstrating genuine real-time capabilities).

---

### Track A: 1-Click Curated Demonstration Mode (Recommended 2-Minute Flow)

#### Objective
Showcase the visual fidelity, tactile PBR textures, camera gizmo, lighting rigs, and additive manufacturing verification without network or hardware delays.

#### Step 1: Open the Application
1. Navigate to `http://localhost:5173`.
2. Notice the clean, dark-mode professional studio identity and hero section.
3. Click **"Start Creating in Studio"** to enter the workspace.

#### Step 2: Load Curated Demo Presets
1. Locate the **"Hackathon Demonstration Mode"** banner at the top of the workspace.
2. Click **"Executive Oak Armchair"**:
   * Observe the 3D model immediately render in the Three.js viewport on the right.
   * Note the high-resolution wood grain micro-texture, anisotropic highlights, and clear geometry.
3. Switch lighting to **"Cinematic Dramatic"** or **"Studio Softbox"** using the lighting toolbar below the viewer.
4. Click the **"Normal Map"** shading button to inspect the tangent-space surface vectors, then return to **"PBR Textures"**.
5. Click the **"Front"**, **"Isometric"**, and **"Top"** gizmo buttons to demonstrate smooth orbital camera navigation.
6. Toggle **"Auto Rotate"** to start presentation turntable spinning.

#### Step 3: Inspect Additive Manufacturing Diagnostics
1. Scroll down the right column to the **"3D Printability Diagnostics & Slicer Verification"** card.
2. Highlight the real-world metrics:
   * **Watertight:** `Yes (0 open boundary edges)`
   * **Manifold:** `Yes (0 non-manifold edges)`
   * **Printability Score:** `85 / 100 (Ready for FDM/SLA slicers)`
   * **Physical Scale:** `63.2 x 100.0 x 80.5 mm`
   * **Estimated Volume:** `5.6 cm³`
3. Click **"Download Full Distribution Bundle (.zip)"**:
   * Inspect the downloaded ZIP archive containing all 6 formats (**GLB, GLTF, OBJ, STL, 3MF, USDZ**), multi-resolution LODs, and individual PBR texture PNGs.

#### Step 4: Inspect Organic Model & Vehicle
1. Click **"Crimson Cyber Coupe"** to view metallic car paint with clearcoat specular reflections.
2. Click **"Honeycrisp Red Apple"** to view organic sub-surface skin textures with stippled lenticel micro-pores.

---

### Track B: Live Interactive Generation (Real-Time Proof Flow)

#### Objective
Demonstrate that the backend pipeline is genuinely functional, taking live user input, understanding semantics, and synthesizing a 3D asset in real time.

#### Step 1: Provide Input
1. In the left column under **"2D Sketch Source"**, choose either:
   * **"Draw":** Use the HTML5 canvas to quickly draw a chair (a horizontal seat, vertical backrest, and 4 downward lines).
   * **"Upload":** Select one of the authentic benchmark sketches from `datasets/benchmark_20sketches/cup_sketch.png`.

#### Step 2: Live AI Understanding
1. Observe the **"Sketch Intelligence & Semantic Recognition"** panel:
   * Displays the predicted category (e.g., `cup` or `chair`) with confidence $> 95\%$.
   * Displays geometric metrics (aspect ratio, horizontal symmetry, contour closure).

#### Step 3: Generate 3D Asset
1. In the **"Reconstruction Engine"** controls:
   * Leave engine on **"Auto (Adaptive Selection)"**.
   * Select Quality Preset: **"High"**.
2. Click the primary button: **"Generate 3D Asset"**.
3. Watch the **Visual Generation Pipeline Tracker** animate through all 7 stages:
   * *Input Ingestion $\rightarrow$ OpenCV Preprocessing $\rightarrow$ Semantic Intelligence $\rightarrow$ 3D Geometry $\rightarrow$ Mesh Validation $\rightarrow$ PBR Texturing $\rightarrow$ Asset Packaging*.
4. In under $10\text{ seconds}$, the fully textured PBR model loads into the 3D viewer.

#### Step 4: Decoupled Dynamic Retexturing (Key Technical Differentiator)
1. In the **"Material & Visual Style Customizer"** panel:
   * Select a new material swatch (e.g., **"24K Polished Gold"** or **"Aircraft Aluminum"**).
   * Select aesthetic style: **"Futuristic"**.
   * Click **"Re-Bake PBR Texture"**.
2. Point out to the judges that the model re-textures in **$< 0.8\text{ seconds}$**:
   * Explain: *"Unlike traditional AI tools that force a full 3-minute regeneration, our decoupled architecture bakes glTF 2.0 PBR materials directly onto existing manifold geometry in sub-second latency."*

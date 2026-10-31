# Sketch2Shape AI — Limitations & Future Roadmap

---

### 1. Transparent Architectural Limitations

In alignment with senior engineering principles, this section documents the boundary conditions and known technical constraints of the current system:

1. **Hardware Constraints on Local Neural Inference (InstantMesh):**
   * *Limitation:* On consumer laptops with physical $4.0\text{ GB}$ VRAM (NVIDIA RTX 3050), executing Zero123++ diffusion multi-view synthesis and LRM reconstruction requires ~4.5 minutes ($254\text{ seconds}$). This is caused by sequential layer evaluation and CPU-GPU tensor swapping necessary to avoid CUDA out-of-memory errors.
   * *Workaround:* The hybrid architecture provides the procedural geometric engine ($< 1\text{s}$) for rapid ideation and supports cloud AI APIs for instant remote neural execution.
2. **Procedural Geometry Category Boundaries:**
   * *Limitation:* While the procedural engine provides 100% watertight, instant geometry, its structured parametric templates currently cover 10 core categories (Chair, Car, Airplane, Cup, Apple, Bicycle, Table, House, Tree, Bottle). Unlisted or abstract shapes rely on silhouette revolution or neural reconstruction.
3. **Tri-Planar UV Texture Seam Artifacts:**
   * *Limitation:* Tri-Planar box projection projects textures from three orthogonal axes ($X, Y, Z$). While effective for cubical furniture and vehicles, surfaces oriented at $45^\circ$ oblique angles may exhibit subtle blend transitions.
4. **Extreme 2D Ambiguity:**
   * *Limitation:* A single 2D stroke cannot fully disambiguate depth or hidden surface topology (e.g., whether a circle represents a sphere, a disk, or a cylinder). The semantic classifier resolves this using QuickDraw class priors, but highly abstract doodles can result in ambiguous predictions.

---

### 2. Strategic Future Engineering Roadmap

1. **Next-Generation Lightweight Feedforward Models (TripoSR / Hunyuan3D-2mini):**
   * Integrate Stability AI's TripoSR or Tencent's Hunyuan3D-2mini to deliver 5-second neural inference directly on workstations equipped with 6GB+ VRAM.
2. **Seamless Automatic UV Parameterization (Xatlas Integration):**
   * Integrate C++ `xatlas` bindings to compute conformal, distortion-minimized UV charts that eliminate tri-planar seams.
3. **Interactive 3D Surface Sketching:**
   * Allow users to draw additional contour strokes directly on the rotating 3D model in Three.js to sculpt and refine local geometry dynamically.
4. **Native Mobile WebXR & Instant USDZ QuickLook:**
   * Enable 1-click mobile AR preview on iOS and Android devices directly from the browser without installing external software.

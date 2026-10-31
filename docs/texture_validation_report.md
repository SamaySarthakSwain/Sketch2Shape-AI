# Sketch2Shape AI — Texture & Material Validation Report

## 1. Executive Summary

Stage 9 implements transparent material, UV coordinate, and texture inspection under [`backend/app/geometry_intelligence/texture_analyzer.py`](file:///C:/Sketch2Shape-AI/backend/app/geometry_intelligence/texture_analyzer.py). 

Rather than simulating fictitious textures or assuming an untextured mesh is UV-mapped, the engine distinguishes three discrete visual modes:
1. **Fully Textured (`uv_mapped`):** Continuous 2D bitmap texture mapped via $(U, V)$ vertex coordinates.
2. **Vertex-Colored (`vertex_colored`):** Discrete point-wise RGBA color attributes embedded directly on mesh vertices.
3. **Untextured Sculpture (`untextured_clay`):** Pure geometric topology rendered with standard PBR clay materials (`metalness: 0.1`, `roughness: 0.4`).

---

## 2. Model Texture Classification

| Asset | Source Engine | Visual Mode | Vertex Colors | UV Mapping | Texture Image | Official Diagnostic Statement |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Chair** | InstantMesh | `vertex_colored` | ✅ Yes (RGBA) | ❌ None | ❌ None | *"Vertex-colored mesh; no conventional UV texture map detected."* |
| **Car** | InstantMesh | `vertex_colored` | ✅ Yes (RGBA) | ❌ None | ❌ None | *"Vertex-colored mesh; no conventional UV texture map detected."* |
| **Airplane** | InstantMesh | `vertex_colored` | ✅ Yes (RGBA) | ❌ None | ❌ None | *"Vertex-colored mesh; no conventional UV texture map detected."* |
| **Chair** | Procedural | `untextured_clay` | ❌ None | ❌ None | ❌ None | *"Untextured clay sculpture; standard PBR diffuse lighting applied."* |
| **Car** | Procedural | `untextured_clay` | ❌ None | ❌ None | ❌ None | *"Untextured clay sculpture; standard PBR diffuse lighting applied."* |
| **Airplane** | Procedural | `untextured_clay` | ❌ None | ❌ None | ❌ None | *"Untextured clay sculpture; standard PBR diffuse lighting applied."* |
| **Cup** | Procedural | `untextured_clay` | ❌ None | ❌ None | ❌ None | *"Untextured clay sculpture; standard PBR diffuse lighting applied."* |
| **Bicycle** | Procedural | `untextured_clay` | ❌ None | ❌ None | ❌ None | *"Untextured clay sculpture; standard PBR diffuse lighting applied."* |
| **Apple** | Procedural | `untextured_clay` | ❌ None | ❌ None | ❌ None | *"Untextured clay sculpture; standard PBR diffuse lighting applied."* |

---

## 3. Vertex Color vs UV Texture Map Technical Analysis

### InstantMesh Vertex Colors:
* InstantMesh queries its triplane neural synthesizer at each extracted vertex coordinate:
  $$\text{RGB}_v = \text{MLP}_{\text{texture}}(\text{Triplane}, v)$$
* Colors are stored as `COLOR_0` float attributes in GLTF / GLB binary buffers.
* Because vertex colors do not require UV unwrapping or parameterization, there are no UV seams or texture distortion artifacts.
* However, detail is bound by vertex density. On coarse meshes, vertex colors appear as smooth gradients across facets.

### GLB Material Preservation:
* All exported GLB files embed the vertex color attributes in the accessor `COLOR_0` (type `VEC4`, componentType `5121` UNSIGNED_BYTE).
* In Three.js and our WebGL viewer, `vertexColors: true` is enabled by default, ensuring vertex-colored models render accurately without requiring external PNG texture files.

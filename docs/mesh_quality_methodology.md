# Sketch2Shape AI — 3D Mesh Quality Scoring Methodology

## 1. Quality Scoring Philosophy

A single scalar metric cannot evaluate a 3D asset. A mesh can be 100% watertight yet look like an 8-vertex cube; conversely, a visually detailed sculpture might contain non-manifold edges that crash 3D slicing software.

The Sketch2Shape AI Quality Scorer generates an **interpretable, multi-domain quality score (0–100)** broken down into six independent, mathematically defined subscores:

$$\text{Overall Score} = w_{topo} S_{topo} + w_{geom} S_{geom} + w_{surf} S_{surf} + w_{multi} S_{multi} + w_{tex} S_{tex} + w_{exp} S_{exp}$$

When multi-view analysis is available:
$$[w_{topo}, w_{geom}, w_{surf}, w_{multi}, w_{tex}, w_{exp}] = [0.25, 0.20, 0.15, 0.20, 0.10, 0.10]$$

When multi-view is unavailable, the weights re-normalize proportionally across the remaining domains. **Missing metrics are explicitly marked unavailable (`None`), never silently assigned 100.**

---

## 2. Mathematical Definition of Subscores

### 2.1 Topology Subscore ($S_{topo} \in [0, 100]$)
Evaluates combinatorial manifoldness and watertightness:

$$S_{topo} = \max\Big(0, 100 - 35 \cdot \mathbb{I}(\neg \text{watertight}) - \min(30, 4 \cdot N_{nm}) - \min(15, 2 \cdot N_{degen}) - \min(10, N_{dup})\Big)$$

* $\mathbb{I}(\neg \text{watertight})$: 1 if mesh contains open boundary edges ($E_{boundary} > 0$), 0 otherwise.
* $N_{nm}$: Number of non-manifold edges.
* $N_{degen}$: Number of zero-area or duplicate-vertex faces.
* $N_{dup}$: Number of coincident unmerged vertices.
* **Under-Tessellation Penalty:** If $V < 16$ or $F < 24$ (e.g. minimal 8-vertex bounding cuboid), $S_{topo}$ is capped at 35.0 to reflect volume capture failure.

---

### 2.2 Geometry & Spatial Subscore ($S_{geom} \in [0, 100]$)
Evaluates symmetry, protrusion sanity, and spatial bounds:

$$S_{geom} = \text{clip}\Big(50 + 35 \cdot \text{Sym}_X + 15 \cdot \mathbb{I}(\text{No Protrusion}) - 15 \cdot \mathbb{I}(\text{Extreme Aspect Ratio}), 0, 100\Big)$$

* **Bilateral Symmetry ($\text{Sym}_X$):**
  $$\text{Sym}_X = \exp\left(-6.0 \cdot \frac{\bar{d}_{KD}}{\text{diag}_{bounds}}\right) \in [0, 1]$$
* **Protrusion Flag:** Activated if any vertex distance from centroid deviates beyond $Q_{75} + 3.0 \cdot \text{IQR}$ while representing $<2\%$ of vertices.
* **Extreme Aspect Ratio:** Flagged if $X/Y > 8.0$ or $X/Y < 0.1$.

---

### 2.3 Surface Subscore ($S_{surf} \in [0, 100]$)
Evaluates normal orientation, facet winding, and surface smoothness:

$$S_{surf} = \max\Big(0, 100 - 40 \cdot \mathbb{I}(\neg \text{winding consistent}) - \min\left(35, 70 \cdot \frac{N_{inv}}{F}\right) - \min(25, 20 \cdot (\sigma_{rough} - 0.8)^+)\Big)$$

* $N_{inv}$: Number of face normals directed inward toward the object centroid.
* $\sigma_{rough}$: Standard deviation of Laplacian coordinate displacements.

---

### 2.4 Multi-View Consistency Subscore ($S_{multi} \in [0, 100]$)
Evaluates silhouette alignment with the 2D input sketch and cross-view continuity:

$$S_{multi} = \text{clip}\Big(0.60 \cdot (\text{IoU}_{front} \times 100) + 0.40 \cdot (\text{Continuity} \times 100) - 12 \cdot \mathbb{I}(\text{Asymmetry}), 0, 100\Big)$$

* **Front Silhouette IoU:**
  $$\text{IoU}_{front} = \frac{|\text{Mask}_{front} \cap \text{Mask}_{sketch}|}{|\text{Mask}_{front} \cup \text{Mask}_{sketch}|}$$
* **Cross-View Continuity:**
  $$\text{Continuity} = \frac{\min_{v \in \text{Views}} \text{Occupancy}(v)}{\max_{v \in \text{Views}} \text{Occupancy}(v)}$$
* **Asymmetry Flag:** Activated if left-view and horizontally flipped right-view silhouette IoU $< 0.45$.

---

### 2.5 Texture Subscore ($S_{tex} \in [0, 100]$)
Evaluates material representation fidelity:
* **UV Mapped with Texture Image ($\ge 1024^2$):** $100$
* **UV Mapped with Standard Texture ($512^2$):** $95$
* **Vertex-Colored Mesh:** $70$ (point-wise color attributes preserved)
* **Untextured Clay Sculpture:** $55$ (clean neutral baseline)
* **UV Parameterized without Texture Image:** $40$

---

### 2.6 Export Integrity Subscore ($S_{exp} \in [0, 100]$)
* Base score = 100.
* If any non-finite coordinates (NaN/Inf): Set to 0 (corrupt file).
* If $F < 15$: Deduct 35 pts.
* If isolated floating shards detected: Deduct $5 \times N_{shards}$ (up to 15 pts).

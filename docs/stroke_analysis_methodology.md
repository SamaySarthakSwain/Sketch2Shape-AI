# Mathematical Methodology: Sketch Stroke Topology & Geometric Analysis

## 1. Introduction

Unlike standard natural image processing, sketch understanding operates on sparse, high-frequency, binary or quasi-binary curves. To reconstruct accurate 3D geometry from a 2D sketch, downstream neural networks (e.g., InstantMesh OSG Decoder) rely on consistent scale, canonical orientation, and clean boundary definitions. Furthermore, knowledge of stroke topology (width, endpoints, junction intersections, symmetry) provides key geometric priors for 3D extrusion, surface normals, and rotational axes.

This document details the mathematical formulations and algorithms implemented in `backend/app/preprocessing/`.

---

## 2. Stroke Width Estimation via Euclidean Distance Transform

### 2.1 Formulation
Given a binary foreground sketch mask $M(x, y) \in \{0, 1\}$, where $M(x, y) = 1$ denotes a stroke pixel and $0$ denotes background, the 2D Euclidean Distance Transform ($L_2$) assigns to every pixel the Euclidean distance to the nearest background pixel:

$$D(x, y) = \min_{(u, v) \notin M} \sqrt{(x - u)^2 + (y - v)^2}$$

### 2.2 Skeleton Sampling
A naive average over all foreground pixels underestimates stroke thickness because edge pixels naturally have $D(x, y) \approx 0.5$. To measure true stroke thickness accurately:
1. Thin the binary mask $M$ into a 1-pixel wide topological skeleton $S(x, y) \in \{0, 1\}$ using Zhang-Suen / Guo-Hall iterative morphological thinning.
2. Sample the distance transform values strictly along the skeleton points:
   $$\mathcal{R} = \{ D(x, y) \mid S(x, y) = 1 \}$$
3. The local stroke radius at skeleton point $(x, y)$ is $R = D(x, y)$. Because the skeleton runs along the medial axis of the stroke, the full stroke diameter (width in pixels) is twice the radius:
   $$W_{\text{stroke}} = 2.0 \cdot \frac{1}{|\mathcal{R}|} \sum_{r \in \mathcal{R}} r$$

This yields sub-pixel precision and robust stroke width estimation regardless of stroke length or curved trajectories.

---

## 3. Stroke Graph Topology: Endpoints and Junctions

### 3.1 8-Neighbor Convolution Kernel
To understand sketch complexity, connectivity, and segmentation, the skeleton $S$ is treated as a planar graph $G = (V, E)$, where pixels are vertices and 8-connectivity defines edges.

We define a 2D spatial convolution kernel $K$ over an 8-connected neighborhood $\mathcal{N}_8(x, y)$:

$$K = \begin{bmatrix} 1 & 1 & 1 \\ 1 & 0 & 1 \\ 1 & 1 & 1 \end{bmatrix}$$

Applying $K$ to the skeleton image normalized to $\{0, 1\}$ produces the vertex degree map $N(x, y)$:

$$N(x, y) = \sum_{i=-1}^{1} \sum_{j=-1}^{1} K(i + 1, j + 1) \cdot S(x + i, y + j)$$

### 3.2 Classification Rules
For any skeleton pixel $(x, y)$ where $S(x, y) = 1$:
- **Isolated Point:** $N(x, y) = 0$ (noise or single-pixel dot).
- **Endpoint (Degree 1):** $N(x, y) = 1$. These mark stroke beginnings and terminations.
- **Continuous Path (Degree 2):** $N(x, y) = 2$. Internal stroke body.
- **Junction / Intersection (Degree $\ge 3$):** $N(x, y) \ge 3$. Marks T-junctions, cross-intersections, and multi-stroke joints.

### 3.3 Line Continuity Scoring
We define a normalized continuity metric:
$$C_{\text{line}} = \max\left(0, 1.0 - \frac{N_{\text{endpoints}}}{2 \times \max(1, N_{\text{junctions}} + N_{\text{components}})}\right)$$
Continuous closed loops (e.g., mugs, spheres, circles) exhibit $C_{\text{line}} \approx 1.0$, whereas fragmented, hatched sketches exhibit $C_{\text{line}} < 0.4$.

---

## 4. Principal Component Analysis (PCA) & Orientation

### 4.1 Spatial Moments
The spatial moments of order $(p + q)$ for a binary image $M(x, y)$ are defined as:
$$m_{pq} = \sum_{x} \sum_{y} x^p y^q M(x, y)$$

The centroid coordinates $(\bar{x}, \bar{y})$ are:
$$\bar{x} = \frac{m_{10}}{m_{00}}, \quad \bar{y} = \frac{m_{01}}{m_{00}}$$

The central moments $\mu_{pq}$, which are invariant to spatial translation, are:
$$\mu_{pq} = \sum_{x} \sum_{y} (x - \bar{x})^p (y - \bar{y})^q M(x, y)$$

### 4.2 2D Covariance Tensor and Principal Angle
The spatial distribution of stroke mass forms a 2D covariance tensor:
$$\Sigma = \frac{1}{m_{00}} \begin{bmatrix} \mu_{20} & \mu_{11} \\ \mu_{11} & \mu_{02} \end{bmatrix}$$

The primary eigenvector of $\Sigma$ corresponds to the dominant orientation axis of the sketch. The orientation angle $\theta \in [-90^\circ, +90^\circ]$ is calculated analytically:
$$\theta = \frac{1}{2} \text{atan2}\left(2 \mu_{11}, \mu_{20} - \mu_{02}\right) \times \frac{180}{\pi}$$

### 4.3 Eccentricity
The eigenvalues $\lambda_1 \ge \lambda_2$ of the covariance matrix are:
$$\lambda_{1, 2} = \frac{(\mu_{20} + \mu_{02}) \pm \sqrt{(\mu_{20} - \mu_{02})^2 + 4 \mu_{11}^2}}{2 m_{00}}$$

The eccentricity $\epsilon \in [0, 1)$ measures elongation:
$$\epsilon = \sqrt{1 - \frac{\lambda_2}{\lambda_1}}$$
- $\epsilon \approx 0$: Circular or square sketch.
- $\epsilon \to 1$: Elongated linear sketch (e.g., pencil, sword, stick).

---

## 5. Centroid-Centered Reflectional Symmetry

### 5.1 Centroid Alignment
To evaluate bilateral symmetry independently of user translation offset:
1. Extract foreground bounding box and centroid $(\bar{x}, \bar{y})$.
2. Create an expanded bounding canvas of dimension $D = \max(W, H) + 20$.
3. Translate the foreground mask such that its centroid $(\bar{x}, \bar{y})$ lies exactly at the center $(D/2, D/2)$ of the canvas, yielding canonical mask $M_{\text{centered}}$.

### 5.2 Reflection & IoU Metric
We compute the reflected masks:
$$M_{\text{horiz}}(x, y) = M_{\text{centered}}(D - x, y)$$
$$M_{\text{vert}}(x, y) = M_{\text{centered}}(x, D - y)$$

The reflectional symmetry score is defined as the Intersection-over-Union (Jaccard Index) between the original and reflected masks:
$$S_H = \frac{|M_{\text{centered}} \cap M_{\text{horiz}}|}{|M_{\text{centered}} \cup M_{\text{horiz}}|}, \quad S_V = \frac{|M_{\text{centered}} \cap M_{\text{vert}}|}{|M_{\text{centered}} \cup M_{\text{vert}}|}$$

Overall symmetry score is:
$$S = \max(S_H, S_V)$$
Man-made objects (bottles, cars, chairs, vases) demonstrate high vertical reflection symmetry ($S_V \ge 0.70$), which downstream 3D reconstruction uses to constrain bilateral mesh generation.

---

## 6. Contour Compactness and Complexity

### 6.1 Compactness (Isoperimetric Quotient)
For a contour of area $A$ and perimeter $P$:
$$C = \frac{4 \pi A}{P^2}$$
- $C = 1.0$: Perfect Euclidean circle.
- $C \ll 1.0$: Complex, branching, or tortuous sketch contours.

### 6.2 Contour Complexity
Contour complexity measures the ratio of the perimeter of the smoothed polygon approximation ($P_{\text{approx}}$ via Douglas-Peucker algorithm with $\epsilon = 0.02 P$) to the convex hull perimeter:
$$\text{Complexity} = \frac{P}{P_{\text{hull}}}$$
Values near $1.0$ indicate smooth convex primitives; values $> 2.0$ indicate high frequency detail or ragged strokes.

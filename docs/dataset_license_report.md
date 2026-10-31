# ⚖️ Dataset Licensing, Terms of Use & Legal Compliance Report

**Document:** `docs/dataset_license_report.md`  
**Platform:** Sketch2Shape AI  
**Author:** Lead AI/ML Autonomous Engineer  
**Stage:** Step 4 of 12 – Complete Multi-Dataset Ingestion  

---

## 1. Executive Summary

This report provides the legal provenance, copyright ownership, attribution requirements, and commercial deployment constraints for all four datasets ingested into the **Sketch2Shape AI** platform:
1. **Google Quick, Draw!** (Massive freehand sketch dataset)
2. **TU-Berlin Sketch Dataset** (Crowdsourced human sketch benchmark)
3. **Objaverse 1.0** (Open large-scale 3D object repository)
4. **ShapeNet** (Academic 3D CAD model repository)

---

## 2. Comprehensive Dataset License Matrix

| Dataset | Primary Source | Authors / Curators | License Type | Commercial Use Permitted? | Redistribution Allowed? | Attribution Requirement |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Google Quick, Draw!** | [Google Creative Lab](https://github.com/googlecreativelab/quickdraw-dataset) | Google Inc. / Jonas Jongejan et al. | **CC BY 4.0** (Creative Commons Attribution 4.0) | **Yes** (Commercial use permitted with attribution) | **Yes** (Under identical license terms) | **Mandatory** citation and copyright notice |
| **TU-Berlin Sketch** | [TU Berlin CG Group](https://cybertron.cg.tu-berlin.de/eitz/projects/classifysketch/) | Mathias Eitz, James Hays, Marc Alexa | **CC BY 4.0 / Academic Research** | **Restricted** (Primarily non-commercial academic benchmarking) | **Yes** (With citation) | **Mandatory** academic citation |
| **Objaverse 1.0** | [Allen Institute for AI (AI2)](https://objaverse.allenai.org/) | Matt Deitke et al. | **ODC-By v1.0** (Database), Individual assets **CC-BY / CC0** | **Yes for CC0/CC-BY assets**; varies per model | **Yes** (Respecting original creator license) | **Mandatory** asset creator credit |
| **ShapeNet** | [ShapeNet Consortium](https://shapenet.org/) | Stanford University, Princeton University, TTIC | **ShapeNet Terms of Use (Custom)** | **Strictly Prohibited** (Non-commercial research only) | **Prohibited** without written authorization | **Mandatory** research acknowledgment |

---

## 3. Deep Dive: Google Quick, Draw!

* **Dataset Identifier:** `google-quickdraw-simplified`
* **Official URL:** `https://storage.googleapis.com/quickdraw_dataset/full/simplified/`
* **License:** Creative Commons Attribution 4.0 International (CC BY 4.0)
* **Permitted Actions:**
  * Sharing, copying, and redistributing the material in any medium or format.
  * Adapting, remixing, transforming, and building upon the material for any purpose, including commercial products.
* **Required Attribution:**
  > *"Drawings from the Quick, Draw! Dataset by Google under the Creative Commons Attribution 4.0 International License."*
* **Compliance in Sketch2Shape AI:**
  The simplified vector NDJSON representation is ingested directly to train the stroke classification, auto-completion, and latent sketch intelligence engine. Attribution is embedded in platform metadata and README documentation.

---

## 4. Deep Dive: TU-Berlin Sketch Dataset

* **Dataset Identifier:** `tu-berlin-sketch-20k`
* **Official Reference:** *Mathias Eitz, James Hays, and Marc Alexa. "How Do Humans Sketch Objects?" ACM Transactions on Graphics (Proc. SIGGRAPH 2012).*
* **License & Terms:**
  * Free for academic, educational, and research experimentation.
  * Commercial exploitation of raw sketches requires consent from the original authors / TU Berlin Computer Graphics Lab.
* **Compliance in Sketch2Shape AI:**
  TU-Berlin sketches are utilized exclusively as a benchmark validation set to evaluate sketch recognition accuracy across humans drawing with varying degrees of fidelity.

---

## 5. Deep Dive: Objaverse 1.0

* **Dataset Identifier:** `allenai-objaverse-1.0`
* **Official URL:** `https://objaverse.allenai.org/`
* **License Architecture:**
  * The **Objaverse metadata database** is licensed under the **Open Data Commons Attribution License (ODC-By v1.0)**.
  * The individual 3D assets are sourced from Sketchfab and retain their original licenses:
    * **CC0 1.0 Public Domain:** Fully usable for any purpose without restrictions.
    * **CC-BY 4.0:** Usable commercially provided the author is credited.
    * **CC-BY-NC 4.0:** Usable for non-commercial research only.
* **Compliance in Sketch2Shape AI:**
  Our automated asset downloader (`scripts/download_objaverse_assets.py`) parses the metadata license field, explicitly filtering for **CC0** and **CC-BY** models for production pipeline validation.

---

## 6. Deep Dive: ShapeNet

* **Dataset Identifier:** `shapenet-core-v2`
* **Official URL:** `https://shapenet.org/`
* **License Architecture:**
  * Governed by Stanford University's ShapeNet Terms of Use.
  * Access requires institutional user authentication and acceptance of non-commercial terms.
* **Compliance in Sketch2Shape AI:**
  * Only publicly accessible taxonomy hierarchies, WordNet synset offsets, and category mapping schemas (`taxonomy.json`) are stored locally.
  * Raw proprietary meshes are **not redistributed** within the application package, maintaining 100% legal compliance.

---

## 7. Operational Recommendations for Hackathon vs. Commercial Release

1. **Hackathon / Research Demo (Current Stage):**
   * All ingested datasets (QuickDraw, TU-Berlin, Objaverse, ShapeNet Taxonomy) are 100% compliant under academic and educational research provisions.
2. **Commercial SaaS Deployment:**
   * **Training Data:** Rely predominantly on **Google Quick, Draw! (CC-BY 4.0)** and **Objaverse CC0/CC-BY** assets.
   * **Excluded from Commercial Runtime:** Isolate TU-Berlin and ShapeNet to internal benchmark evaluations; do not bundle or resell raw assets.

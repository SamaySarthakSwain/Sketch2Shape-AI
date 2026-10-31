"""
Sketch Intelligence Module for Sketch2Shape AI
Performs geometric analysis, symmetry calculation, aspect ratio classification,
shape category recognition, and prompt synthesis for 3D reconstruction.
"""

import cv2
import numpy as np
from typing import Dict, Any, List, Optional


class SketchAnalyzer:
    def __init__(self):
        # Known semantic categories with characteristic shape features
        self.categories = {
            "vase_pottery": {
                "aspect_ratio_range": (1.2, 3.5),
                "rotational_symmetry_score": 0.70,
                "solidity_min": 0.55,
                "prompt_template": "a ceramic vase pottery sculpture, elegant smooth surface, 3d model, clean geometry",
                "recommended_mode": "rotational_symmetric"
            },
            "cup_mug": {
                "aspect_ratio_range": (0.7, 1.3),
                "rotational_symmetry_score": 0.50,
                "solidity_min": 0.50,
                "prompt_template": "a ceramic drinking mug cup with handle, clean design, 3d asset",
                "recommended_mode": "hybrid"
            },
            "bottle": {
                "aspect_ratio_range": (2.0, 5.0),
                "rotational_symmetry_score": 0.75,
                "solidity_min": 0.60,
                "prompt_template": "a glass drink bottle with slender neck, smooth container, 3d model",
                "recommended_mode": "rotational_symmetric"
            },
            "chair_furniture": {
                "aspect_ratio_range": (1.1, 2.5),
                "rotational_symmetry_score": 0.40,
                "solidity_min": 0.25,
                "prompt_template": "a modern designer chair furniture, four legs, supportive backrest, clean 3d mesh",
                "recommended_mode": "extrusion_symmetric"
            },
            "car_vehicle": {
                "aspect_ratio_range": (0.3, 0.7),
                "rotational_symmetry_score": 0.45,
                "solidity_min": 0.65,
                "prompt_template": "a streamlined sports car automobile vehicle, wheels, chassis, 3d model",
                "recommended_mode": "bilateral_symmetric"
            },
            "aircraft_plane": {
                "aspect_ratio_range": (0.6, 1.8),
                "rotational_symmetry_score": 0.70,
                "solidity_min": 0.30,
                "prompt_template": "a sleek airplane aircraft with wings and tail, aerodynamic 3d model",
                "recommended_mode": "bilateral_symmetric"
            },
            "table": {
                "aspect_ratio_range": (0.5, 1.1),
                "rotational_symmetry_score": 0.50,
                "solidity_min": 0.35,
                "prompt_template": "a sturdy wooden desk table with flat top surface and sturdy legs, 3d model",
                "recommended_mode": "extrusion_symmetric"
            },
            "sword_weapon": {
                "aspect_ratio_range": (3.0, 8.0),
                "rotational_symmetry_score": 0.65,
                "solidity_min": 0.20,
                "prompt_template": "a fantasy steel sword blade weapon with hilt and crossguard, game asset 3d model",
                "recommended_mode": "bilateral_symmetric"
            },
            "generic_object": {
                "aspect_ratio_range": (0.1, 10.0),
                "rotational_symmetry_score": 0.0,
                "solidity_min": 0.0,
                "prompt_template": "a smooth 3d solid object sculpture, clean manifold mesh, product design",
                "recommended_mode": "hybrid"
            }
        }

    def compute_symmetry(self, binary_mask: np.ndarray) -> Dict[str, float]:
        """
        Calculates horizontal and vertical reflection symmetry scores [0.0 - 1.0].
        A value near 1.0 indicates near-perfect symmetry across that axis.
        """
        h, w = binary_mask.shape
        # Vertical axis reflection (left vs right)
        flipped_lr = cv2.flip(binary_mask, 1)
        intersection_v = cv2.bitwise_and(binary_mask, flipped_lr)
        union_v = cv2.bitwise_or(binary_mask, flipped_lr)
        count_union_v = cv2.countNonZero(union_v)
        sym_vertical = float(cv2.countNonZero(intersection_v) / max(count_union_v, 1))

        # Horizontal axis reflection (top vs bottom)
        flipped_ud = cv2.flip(binary_mask, 0)
        intersection_h = cv2.bitwise_and(binary_mask, flipped_ud)
        union_h = cv2.bitwise_or(binary_mask, flipped_ud)
        count_union_h = cv2.countNonZero(union_h)
        sym_horizontal = float(cv2.countNonZero(intersection_h) / max(count_union_h, 1))

        return {
            "vertical_symmetry": round(sym_vertical, 4),
            "horizontal_symmetry": round(sym_horizontal, 4),
            "dominant_symmetry": "vertical" if sym_vertical >= sym_horizontal else "horizontal"
        }

    def analyze_geometry(self, binary_mask: np.ndarray, bbox: List[int]) -> Dict[str, Any]:
        """
        Extracts geometric descriptors including moments, aspect ratio, solidity,
        compactness, and hull convexity.
        """
        x, y, w, h = bbox
        aspect_ratio = float(h / max(w, 1))

        contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return {
                "aspect_ratio": 1.0,
                "solidity": 0.0,
                "compactness": 0.0,
                "contour_count": 0,
                "extent": 0.0,
                "center_of_mass": [256, 256]
            }

        largest_cnt = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest_cnt)
        hull = cv2.convexHull(largest_cnt)
        hull_area = cv2.contourArea(hull)

        solidity = float(area / max(hull_area, 1.0))
        perimeter = cv2.arcLength(largest_cnt, True)
        compactness = float((4 * np.pi * area) / max(perimeter**2, 1.0))
        extent = float(area / max(w * h, 1.0))

        # Moments & Center of mass
        M = cv2.moments(largest_cnt)
        if M["m00"] != 0:
            cx = float(M["m10"] / M["m00"])
            cy = float(M["m01"] / M["m00"])
        else:
            cx, cy = float(x + w / 2), float(y + h / 2)

        return {
            "aspect_ratio": round(aspect_ratio, 3),
            "solidity": round(solidity, 3),
            "compactness": round(compactness, 3),
            "extent": round(extent, 3),
            "contour_count": len(contours),
            "center_of_mass": [round(cx, 1), round(cy, 1)],
            "bounding_dimensions": {"width": w, "height": h}
        }

    def predict_category(
        self,
        geometry: Dict[str, Any],
        symmetry: Dict[str, float],
        user_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Predicts the object class and synthesis hints using extracted geometry and symmetry.
        Allows user prompt override if provided.
        """
        if user_hint and user_hint.strip():
            hint_clean = user_hint.strip().lower()
            # Match against known tags
            for cat, meta in self.categories.items():
                if any(word in hint_clean for word in cat.split("_")):
                    return {
                        "category": cat,
                        "confidence": 0.95,
                        "prompt": f"{user_hint}, 3d asset, clean manifold geometry",
                        "recommended_mode": meta["recommended_mode"],
                        "source": "user_hint"
                    }
            # Generic user prompt
            return {
                "category": "custom_user_prompt",
                "confidence": 0.90,
                "prompt": f"{user_hint}, 3d asset, high quality model",
                "recommended_mode": "hybrid",
                "source": "user_hint"
            }

        aspect = geometry["aspect_ratio"]
        solidity = geometry["solidity"]
        v_sym = symmetry["vertical_symmetry"]

        scores = {}
        for cat, meta in self.categories.items():
            if cat == "generic_object":
                scores[cat] = 0.25 # baseline fallback
                continue

            score = 0.0
            min_ar, max_ar = meta["aspect_ratio_range"]
            if min_ar <= aspect <= max_ar:
                score += 0.40
            else:
                diff = min(abs(aspect - min_ar), abs(aspect - max_ar))
                score += max(0.0, 0.40 - diff * 0.15)

            sym_diff = abs(v_sym - meta["rotational_symmetry_score"])
            score += max(0.0, 0.35 - sym_diff * 0.5)

            if solidity >= meta["solidity_min"]:
                score += 0.25
            else:
                score += max(0.0, 0.25 - (meta["solidity_min"] - solidity))

            scores[cat] = round(score, 3)

        # Pick top category
        best_cat = max(scores, key=scores.get)
        confidence = scores[best_cat]
        meta = self.categories[best_cat]

        return {
            "category": best_cat,
            "confidence": min(1.0, confidence),
            "prompt": meta["prompt_template"],
            "recommended_mode": meta["recommended_mode"],
            "all_scores": scores,
            "source": "geometry_heuristic"
        }

    def analyze(
        self,
        binary_mask: np.ndarray,
        bbox: List[int],
        user_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """Runs complete intelligence analysis on the preprocessed sketch."""
        symmetry = self.compute_symmetry(binary_mask)
        geometry = self.analyze_geometry(binary_mask, bbox)
        classification = self.predict_category(geometry, symmetry, user_hint)

        return {
            "symmetry": symmetry,
            "geometry": geometry,
            "classification": classification,
            "synthesis_prompt": classification["prompt"],
            "recommended_3d_mode": classification["recommended_mode"]
        }

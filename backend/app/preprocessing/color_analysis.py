"""
OpenCV Color and Palette Extraction Engine
Analyzes 2D sketches and images for color vibrancy, foreground stroke palette,
and dominant color clusters for faithful 3D asset material tinting.
"""

import cv2
import numpy as np
from typing import Dict, Any, List, Tuple, Optional


class ColorAnalyzer:
    @staticmethod
    def rgb_to_hex(r: int, g: int, b: int) -> str:
        return f"#{int(r):02X}{int(g):02X}{int(b):02X}"

    @classmethod
    def analyze_image_colors(cls, image_bgr: np.ndarray) -> Dict[str, Any]:
        """
        Analyzes a BGR image to determine whether it is colorful,
        extracts dominant RGB/hex colors, and identifies foreground palette.
        """
        if image_bgr is None or image_bgr.size == 0:
            return cls._default_grayscale_result()

        h, w, c = image_bgr.shape
        if c == 4:
            # Drop alpha if present
            image_bgr = image_bgr[:, :, :3]

        # Convert to HSV and RGB
        hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
        rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

        # 1. Background Masking:
        # Typical sketch paper is near white (V > 220, S < 30) or near black (V < 30).
        # We define colorful foreground pixels as having saturation > 35 (out of 255)
        # and brightness in reasonable range (30 < V < 245).
        s_channel = hsv[:, :, 1]
        v_channel = hsv[:, :, 2]

        color_mask = (s_channel > 35) & (v_channel > 30) & (v_channel < 250)
        num_color_pixels = int(np.count_nonzero(color_mask))
        total_pixels = h * w
        color_ratio = num_color_pixels / max(total_pixels, 1)

        # Non-background pixels (any stroke: colorful OR black/dark strokes)
        stroke_mask = (v_channel < 235) | (s_channel > 30)
        num_stroke_pixels = int(np.count_nonzero(stroke_mask))

        is_colorful = bool(num_color_pixels > 250 and (color_ratio > 0.005 or num_color_pixels / max(num_stroke_pixels, 1) > 0.05))

        dominant_colors: List[Dict[str, Any]] = []

        if is_colorful:
            # Extract RGB values of colorful pixels
            colored_rgb = rgb[color_mask]
            
            # Subsample if large
            if len(colored_rgb) > 5000:
                indices = np.random.choice(len(colored_rgb), 5000, replace=False)
                colored_rgb = colored_rgb[indices]

            # K-means clustering (up to 3 clusters)
            colored_float = np.float32(colored_rgb)
            k = min(3, max(1, len(colored_float) // 100))
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
            _, labels, centers = cv2.kmeans(colored_float, k, None, criteria, 5, cv2.KMEANS_PP_CENTERS)

            # Sort clusters by frequency
            unique, counts = np.unique(labels, return_counts=True)
            sorted_indices = np.argsort(-counts)

            for idx in sorted_indices:
                cnt = counts[idx]
                center_rgb = centers[idx].astype(int)
                r, g, b = int(center_rgb[0]), int(center_rgb[1]), int(center_rgb[2])
                hex_code = cls.rgb_to_hex(r, g, b)
                color_name = cls._approximate_color_name(r, g, b)
                pct = round((cnt / len(labels)) * 100, 1)
                dominant_colors.append({
                    "name": color_name,
                    "hex": hex_code,
                    "rgb": [r, g, b],
                    "percentage": pct
                })

            primary_rgb = dominant_colors[0]["rgb"]
            primary_hex = dominant_colors[0]["hex"]
            secondary_rgb = dominant_colors[1]["rgb"] if len(dominant_colors) > 1 else [int(primary_rgb[0] * 0.7), int(primary_rgb[1] * 0.7), int(primary_rgb[2] * 0.7)]
            secondary_hex = dominant_colors[1]["hex"] if len(dominant_colors) > 1 else cls.rgb_to_hex(secondary_rgb[0], secondary_rgb[1], secondary_rgb[2])

        else:
            # Monochromatic / standard pencil or ink sketch
            primary_rgb = [30, 30, 35]
            primary_hex = "#1E1E23"
            secondary_rgb = [240, 240, 245]
            secondary_hex = "#F0F0F5"
            dominant_colors = [
                {"name": "Black / Dark Ink", "hex": primary_hex, "rgb": primary_rgb, "percentage": 100.0}
            ]

        return {
            "is_colorful": is_colorful,
            "color_pixel_count": num_color_pixels,
            "color_ratio": round(color_ratio, 4),
            "primary_color_rgb": primary_rgb,
            "primary_color_hex": primary_hex,
            "secondary_color_rgb": secondary_rgb,
            "secondary_color_hex": secondary_hex,
            "dominant_colors": dominant_colors
        }

    @classmethod
    def _approximate_color_name(cls, r: int, g: int, b: int) -> str:
        """Approximates natural language name for an RGB tuple."""
        # Simple color distance to reference spectrum
        references = {
            "Crimson Red": (220, 38, 38),
            "Scarlet Red": (239, 68, 68),
            "Fiery Orange": (249, 115, 22),
            "Amber Gold": (245, 158, 11),
            "Sunny Yellow": (234, 179, 8),
            "Lime Green": (132, 204, 22),
            "Emerald Green": (16, 185, 129),
            "Forest Green": (22, 101, 52),
            "Teal / Cyan": (20, 184, 166),
            "Sky Blue": (56, 189, 248),
            "Cobalt Blue": (37, 99, 235),
            "Navy Blue": (30, 58, 138),
            "Royal Purple": (147, 51, 234),
            "Deep Violet": (109, 40, 217),
            "Hot Pink": (236, 72, 153),
            "Rose Pink": (244, 63, 94),
            "Saddle Brown": (146, 64, 14),
            "Dark Walnut": (69, 26, 3),
            "Cool Slate": (100, 116, 139),
            "Charcoal Black": (30, 30, 30),
            "Clean White": (250, 250, 250),
        }

        best_name = "Custom Color"
        min_dist = float("inf")

        for name, ref_rgb in references.items():
            dist = (r - ref_rgb[0])**2 + (g - ref_rgb[1])**2 + (b - ref_rgb[2])**2
            if dist < min_dist:
                min_dist = dist
                best_name = name

        return best_name

    @classmethod
    def _default_grayscale_result(cls) -> Dict[str, Any]:
        return {
            "is_colorful": False,
            "color_pixel_count": 0,
            "color_ratio": 0.0,
            "primary_color_rgb": [30, 30, 30],
            "primary_color_hex": "#1E1E1E",
            "secondary_color_rgb": [245, 245, 245],
            "secondary_color_hex": "#F5F5F5",
            "dominant_colors": []
        }

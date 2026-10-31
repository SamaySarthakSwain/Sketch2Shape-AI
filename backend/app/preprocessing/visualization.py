"""
Visualization and Diagnostic Image Exporter Module
Renders all 9 intermediate and final pipeline representations:
1. Original image
2. Enhanced image
3. Denoised image
4. Binary image
5. Edge image
6. Contour visualization
7. Skeleton image
8. Foreground mask
9. Final reconstruction input
"""

import base64
from typing import Dict, Any, Optional
from pathlib import Path
import numpy as np
import cv2


class SketchVisualizer:
    @staticmethod
    def to_base64(img: np.ndarray, format: str = ".png") -> str:
        success, buffer = cv2.imencode(format, img)
        if not success:
            raise RuntimeError("Failed to encode image to base64")
        b64 = base64.b64encode(buffer).decode("utf-8")
        mime = "image/png" if format.lower() == ".png" else "image/jpeg"
        return f"data:{mime};base64,{b64}"

    @staticmethod
    def draw_graph_overlay(skeleton: np.ndarray, endpoints: list, junctions: list) -> np.ndarray:
        """Draws red dots for endpoints and blue dots for junctions over a 3-channel skeleton canvas."""
        overlay = cv2.cvtColor(skeleton, cv2.COLOR_GRAY2BGR)
        for ep in endpoints:
            cv2.circle(overlay, (ep[0], ep[1]), radius=3, color=(0, 0, 255), thickness=-1)
        for jn in junctions:
            cv2.circle(overlay, (jn[0], jn[1]), radius=3, color=(255, 0, 0), thickness=-1)
        return overlay

    @classmethod
    def save_debug_grid(cls, variants: Dict[str, np.ndarray], output_path: str):
        """Saves a multi-panel 3x3 diagnostic comparison image."""
        panels = []
        target_size = (256, 256)
        
        for name, img in variants.items():
            if img.ndim == 2:
                bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            elif img.shape[2] == 4:
                bgr = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
            else:
                bgr = img.copy()

            resized = cv2.resize(bgr, target_size, interpolation=cv2.INTER_AREA)
            # Label banner
            cv2.putText(resized, name, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            cv2.putText(resized, name, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            panels.append(resized)

        # Pad to multiple of 3 if needed
        while len(panels) < 9:
            panels.append(np.zeros((target_size[1], target_size[0], 3), dtype=np.uint8))

        row1 = np.hstack(panels[:3])
        row2 = np.hstack(panels[3:6])
        row3 = np.hstack(panels[6:9])
        grid = np.vstack([row1, row2, row3])

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(output_path, grid)
        return output_path

"""
Reconstruction Normalization Module
Centers the sketch object, applies uniform padding, preserves aspect ratio,
and renders canonical reconstruction-ready images (512x512) for InstantMesh and Hunyuan3D.
"""

from typing import Tuple, Optional
import numpy as np
import cv2


class SketchNormalizer:
    def __init__(
        self,
        target_size: int = 512,
        padding_ratio: float = 0.12,
        background_color: Tuple[int, int, int] = (255, 255, 255)
    ):
        self.target_size = target_size
        self.padding_ratio = padding_ratio
        self.background_color = background_color

    def normalize(
        self,
        bgr_image: np.ndarray,
        binary_mask: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Centers and normalizes the sketch object into a square canvas (target_size x target_size).
        Returns:
            reconstruction_rgb: 3-channel RGB image on white background, scaled and centered
            reconstruction_rgba: 4-channel RGBA image with alpha transparency
            normalized_mask: 1-channel binary mask corresponding to the centered object
        """
        # 1. Locate bounding box of non-zero mask pixels
        pts = cv2.findNonZero(binary_mask)
        if pts is None or len(pts) == 0:
            # Fallback if image is completely empty: return blank canvas
            blank_rgb = np.full((self.target_size, self.target_size, 3), self.background_color, dtype=np.uint8)
            blank_rgba = np.zeros((self.target_size, self.target_size, 4), dtype=np.uint8)
            blank_mask = np.zeros((self.target_size, self.target_size), dtype=np.uint8)
            return blank_rgb, blank_rgba, blank_mask

        bx, by, bw, bh = cv2.boundingRect(pts)
        cropped_bgr = bgr_image[by:by+bh, bx:bx+bw]
        cropped_mask = binary_mask[by:by+bh, bx:bx+bw]

        # 2. Compute scaling factor preserving aspect ratio with padding
        # Available drawing area after padding
        available_dim = int(self.target_size * (1.0 - 2.0 * self.padding_ratio))
        scale = float(available_dim) / float(max(bw, bh))

        new_w = max(1, int(round(bw * scale)))
        new_h = max(1, int(round(bh * scale)))

        # Resize with high-quality Lanczos / Area interpolation
        interp = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LANCZOS4
        resized_bgr = cv2.resize(cropped_bgr, (new_w, new_h), interpolation=interp)
        resized_mask = cv2.resize(cropped_mask, (new_w, new_h), interpolation=cv2.INTER_NEAREST)

        # 3. Canvas placement: center at (target_size // 2)
        pad_x = (self.target_size - new_w) // 2
        pad_y = (self.target_size - new_h) // 2

        # 4. Canvas creation: RGB (white background)
        rgb_canvas = np.full((self.target_size, self.target_size, 3), self.background_color, dtype=np.uint8)
        # Composite foreground strokes onto white canvas
        mask_norm = (resized_mask.astype(np.float32) / 255.0)[:, :, np.newaxis]
        bg_patch = rgb_canvas[pad_y:pad_y+new_h, pad_x:pad_x+new_w].astype(np.float32)
        fg_patch = cv2.cvtColor(resized_bgr, cv2.COLOR_BGR2RGB).astype(np.float32)
        composited = fg_patch * mask_norm + bg_patch * (1.0 - mask_norm)
        rgb_canvas[pad_y:pad_y+new_h, pad_x:pad_x+new_w] = np.clip(composited, 0, 255).astype(np.uint8)

        # 5. Canvas creation: RGBA
        rgba_canvas = np.zeros((self.target_size, self.target_size, 4), dtype=np.uint8)
        rgba_canvas[pad_y:pad_y+new_h, pad_x:pad_x+new_w, :3] = cv2.cvtColor(resized_bgr, cv2.COLOR_BGR2RGB)
        rgba_canvas[pad_y:pad_y+new_h, pad_x:pad_x+new_w, 3] = resized_mask

        # 6. Canvas creation: Binary Mask
        mask_canvas = np.zeros((self.target_size, self.target_size), dtype=np.uint8)
        mask_canvas[pad_y:pad_y+new_h, pad_x:pad_x+new_w] = resized_mask

        return rgb_canvas, rgba_canvas, mask_canvas

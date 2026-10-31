"""
Foreground Extraction and Connected Component Filtering Module
Isolates foreground sketch objects from background noise, scanner artifacts, and stray specks.
Supports optional rembg integration.
"""

from typing import Tuple, Optional
import numpy as np
import cv2


class ForegroundExtractor:
    def __init__(self, min_component_area: int = 15, use_rembg: bool = False):
        self.min_component_area = min_component_area
        self.use_rembg = use_rembg
        self._rembg_session = None

    def filter_small_components(self, binary_mask: np.ndarray) -> np.ndarray:
        """
        Removes isolated speckles and dust particles smaller than min_component_area
        while preserving all continuous drawing strokes.
        """
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary_mask, connectivity=8)
        clean_mask = np.zeros_like(binary_mask)

        # Label 0 is background
        for label_idx in range(1, num_labels):
            area = stats[label_idx, cv2.CC_STAT_AREA]
            if area >= self.min_component_area:
                clean_mask[labels == label_idx] = 255

        return clean_mask

    def extract_foreground(
        self,
        bgr_image: np.ndarray,
        binary_mask: np.ndarray,
        alpha_channel: Optional[np.ndarray] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Extracts clean foreground.
        Returns:
            clean_mask: filtered binary mask (255 = foreground, 0 = background)
            rgba_foreground: 4-channel RGBA image with transparent background
        """
        # 1. Connected component noise cleanup
        clean_mask = self.filter_small_components(binary_mask)

        # If original image had an alpha channel, incorporate it
        if alpha_channel is not None:
            clean_mask = cv2.bitwise_and(clean_mask, alpha_channel)

        # 2. Construct RGBA cutout
        h, w = bgr_image.shape[:2]
        rgba = np.zeros((h, w, 4), dtype=np.uint8)
        rgba[:, :, :3] = bgr_image
        rgba[:, :, 3] = clean_mask

        # 3. Optional rembg integration for complex paper backgrounds
        if self.use_rembg:
            try:
                import rembg
                from PIL import Image
                pil_img = Image.fromarray(cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB))
                rembg_out = rembg.remove(pil_img)
                rembg_np = np.array(rembg_out)
                if rembg_np.shape[2] == 4:
                    rembg_alpha = rembg_np[:, :, 3]
                    clean_mask = cv2.bitwise_or(clean_mask, rembg_alpha)
                    rgba[:, :, 3] = clean_mask
            except Exception as e:
                # Fall back gracefully to morphological mask
                pass

        return clean_mask, rgba

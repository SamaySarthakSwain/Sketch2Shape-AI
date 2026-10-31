"""
Robust Image Loader with Color Space and Transparency Handling
Loads images from file paths, raw bytes, base64 strings, PIL images, or numpy arrays.
Preserves original image representation.
"""

import io
import base64
from pathlib import Path
from typing import Any, Tuple, Optional, Union
import numpy as np
import cv2
from PIL import Image


class ImageLoader:
    @staticmethod
    def load(image_input: Union[str, bytes, Path, Image.Image, np.ndarray]) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Loads an input into:
        - bgr_image: standard 3-channel BGR uint8 image
        - alpha_channel: 1-channel uint8 mask if transparency present, else None
        Preserves original values.
        """
        raw_img = None

        if isinstance(image_input, (str, Path)):
            path_str = str(image_input)
            if path_str.startswith("data:image") or "," in path_str and len(path_str) > 200:
                # Base64 data URL or encoded string
                b64_part = path_str.split(",", 1)[1] if "," in path_str else path_str
                raw_bytes = base64.b64decode(b64_part)
                nparr = np.frombuffer(raw_bytes, np.uint8)
                raw_img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
            else:
                # File system path
                if not Path(path_str).exists():
                    raise FileNotFoundError(f"Image file does not exist: {path_str}")
                raw_img = cv2.imread(path_str, cv2.IMREAD_UNCHANGED)

        elif isinstance(image_input, bytes):
            nparr = np.frombuffer(image_input, np.uint8)
            raw_img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)

        elif isinstance(image_input, Image.Image):
            pil_arr = np.array(image_input)
            if pil_arr.ndim == 2:
                raw_img = pil_arr
            elif pil_arr.shape[2] == 3:
                raw_img = cv2.cvtColor(pil_arr, cv2.COLOR_RGB2BGR)
            elif pil_arr.shape[2] == 4:
                raw_img = cv2.cvtColor(pil_arr, cv2.COLOR_RGBA2BGRA)

        elif isinstance(image_input, np.ndarray):
            raw_img = image_input.copy()

        else:
            raise TypeError(f"Unsupported image input type: {type(image_input)}")

        if raw_img is None or raw_img.size == 0:
            raise ValueError("Failed to decode image: array is empty or corrupt.")

        # Decompose channels
        alpha_channel = None
        if raw_img.ndim == 2:
            # Grayscale -> 3 channel BGR
            bgr = cv2.cvtColor(raw_img, cv2.COLOR_GRAY2BGR)
        elif raw_img.shape[2] == 4:
            # BGRA
            alpha_channel = raw_img[:, :, 3].copy()
            bgr = raw_img[:, :, :3].copy()
        elif raw_img.shape[2] == 3:
            bgr = raw_img.copy()
        else:
            raise ValueError(f"Unexpected image dimensions: {raw_img.shape}")

        return bgr, alpha_channel

    @staticmethod
    def to_rgb(bgr: np.ndarray) -> np.ndarray:
        return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

    @staticmethod
    def to_grayscale(bgr: np.ndarray) -> np.ndarray:
        if bgr.ndim == 2:
            return bgr.copy()
        return cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    @staticmethod
    def composite_on_background(bgr: np.ndarray, alpha: Optional[np.ndarray], bg_color: Tuple[int, int, int] = (255, 255, 255)) -> np.ndarray:
        """Composites an image with alpha onto a solid background color (default white)."""
        if alpha is None:
            return bgr.copy()
        alpha_norm = (alpha.astype(np.float32) / 255.0)[:, :, np.newaxis]
        bg = np.full_like(bgr, bg_color, dtype=np.uint8).astype(np.float32)
        fg = bgr.astype(np.float32)
        out = fg * alpha_norm + bg * (1.0 - alpha_norm)
        return np.clip(out, 0, 255).astype(np.uint8)

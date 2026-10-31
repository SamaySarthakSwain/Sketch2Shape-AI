"""
OpenCV Sketch Preprocessing Pipeline for Sketch2Shape AI
Provides image cleanup, adaptive binarization, bounding box auto-crop,
stroke skeletonization, distance-transform depth cues, and normal map generation.
"""

import io
import base64
import numpy as np
import cv2
from PIL import Image
from typing import Dict, Any, Tuple, Optional


class SketchPreprocessor:
    def __init__(self, target_size: int = 512, padding_pct: float = 0.12):
        self.target_size = target_size
        self.padding_pct = padding_pct

    @staticmethod
    def load_image(image_input: Any) -> np.ndarray:
        """Loads an image from base64, bytes, or PIL Image into a BGR/BGRA numpy array."""
        if isinstance(image_input, str):
            if "," in image_input:
                image_input = image_input.split(",", 1)[1]
            raw_bytes = base64.b64decode(image_input)
            nparr = np.frombuffer(raw_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
        elif isinstance(image_input, bytes):
            nparr = np.frombuffer(image_input, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
        elif isinstance(image_input, Image.Image):
            img = cv2.cvtColor(np.array(image_input), cv2.COLOR_RGB2BGR)
        elif isinstance(image_input, np.ndarray):
            img = image_input.copy()
        else:
            raise ValueError(f"Unsupported image input type: {type(image_input)}")

        if img is None:
            raise ValueError("Failed to decode input image.")
        return img

    @staticmethod
    def to_base64(img_np: np.ndarray, format: str = ".png") -> str:
        """Converts an image array to base64 data URL string."""
        success, buffer = cv2.imencode(format, img_np)
        if not success:
            raise RuntimeError("Failed to encode image to base64")
        b64_str = base64.b64encode(buffer).decode("utf-8")
        mime = "image/png" if format == ".png" else "image/jpeg"
        return f"data:{mime};base64,{b64_str}"

    def standardize_strokes(self, img: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Extracts strokes from canvas or uploaded drawing.
        Handles alpha channels, dark mode canvases, and paper photos.
        Returns:
            binary_mask: 255 = stroke, 0 = background
            grayscale: Grayscale image
        """
        # Handle alpha channel (transparent canvas drawing)
        if len(img.shape) == 3 and img.shape[2] == 4:
            alpha = img[:, :, 3]
            bgr = img[:, :, :3]
            gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
            # If transparent background is present, non-transparent pixels with dark color or alpha > 0 are strokes
            mask = np.zeros_like(gray)
            mask[alpha > 30] = 255
            # If the drawing was drawn in dark strokes on transparent:
            stroke_mask = cv2.bitwise_and(255 - gray, mask)
            binary_mask = cv2.threshold(stroke_mask, 20, 255, cv2.THRESH_BINARY)[1]
            return binary_mask, gray
        elif len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img.copy()

        # Denoise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Detect if background is dark or bright
        mean_val = np.mean(blurred)
        if mean_val < 127:
            # White strokes on dark background
            binary_mask = cv2.threshold(blurred, 40, 255, cv2.THRESH_BINARY)[1]
        else:
            # Dark strokes on bright background (standard paper/canvas)
            # Use Otsu's thresholding combined with adaptive thresholding for robust lines
            otsu_thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
            adaptive_thresh = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 4
            )
            binary_mask = cv2.bitwise_or(otsu_thresh, adaptive_thresh)

        # Morphological opening to remove isolated noise specks
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, kernel, iterations=1)
        # Morphological close to bridge minor stroke gaps
        binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel, iterations=1)

        return binary_mask, gray

    def center_and_crop(self, stroke_mask: np.ndarray) -> Tuple[np.ndarray, Tuple[int, int, int, int]]:
        """
        Finds the bounding box of strokes and centers the sketch in a square target_size x target_size canvas.
        Returns:
            centered_mask: Target square image (255 = stroke, 0 = bg)
            bbox: (x, y, w, h) in original coords
        """
        coords = cv2.findNonZero(stroke_mask)
        if coords is None:
            # Blank canvas fallback
            blank = np.zeros((self.target_size, self.target_size), dtype=np.uint8)
            return blank, (0, 0, stroke_mask.shape[1], stroke_mask.shape[0])

        x, y, w, h = cv2.boundingRect(coords)
        cropped = stroke_mask[y:y+h, x:x+w]

        # Calculate target dimensions with padding
        avail_size = int(self.target_size * (1.0 - 2 * self.padding_pct))
        scale = min(avail_size / max(w, 1), avail_size / max(h, 1))

        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        resized = cv2.resize(cropped, (new_w, new_h), interpolation=cv2.INTER_AREA)

        # Place in center of square canvas
        centered = np.zeros((self.target_size, self.target_size), dtype=np.uint8)
        start_x = (self.target_size - new_w) // 2
        start_y = (self.target_size - new_h) // 2
        centered[start_y:start_y+new_h, start_x:start_x+new_w] = resized

        return centered, (int(x), int(y), int(w), int(h))

    def generate_depth_and_normals(self, centered_mask: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Computes synthetic pseudo-depth map using euclidean distance transform,
        and generates a high-fidelity 3-channel normal map (RGB).
        """
        # Distance transform inside closed shapes or from strokes
        # First fill small holes to create silhouette approximation
        contours, _ = cv2.findContours(centered_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        silhouette = np.zeros_like(centered_mask)
        if contours:
            cv2.drawContours(silhouette, contours, -1, 255, thickness=cv2.FILLED)

        # If silhouette is too sparse or empty, fallback to stroke distance
        combined_region = cv2.bitwise_or(silhouette, centered_mask)
        dist = cv2.distanceTransform(combined_region, cv2.DIST_L2, 5)

        # Normalize distance to 0 - 255 for depth
        max_dist = dist.max()
        if max_dist > 0:
            depth = ((dist / max_dist) ** 0.6 * 255.0).astype(np.uint8)
        else:
            depth = np.zeros_like(centered_mask)

        # Smooth depth map
        depth_smooth = cv2.GaussianBlur(depth, (9, 9), 0)

        # Compute surface gradients using Sobel operators
        sobel_x = cv2.Sobel(depth_smooth, cv2.CV_32F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(depth_smooth, cv2.CV_32F, 0, 1, ksize=3)

        # Normal vector components: N = [-dz/dx, -dz/dy, 1] normalized
        scale = 0.05
        nx = -sobel_x * scale
        ny = -sobel_y * scale
        nz = np.ones_like(nx)

        norm = np.sqrt(nx**2 + ny**2 + nz**2)
        norm[norm == 0] = 1.0

        nx = (nx / norm * 0.5 + 0.5) * 255.0
        ny = (ny / norm * 0.5 + 0.5) * 255.0
        nz = (nz / norm * 0.5 + 0.5) * 255.0

        normal_map = np.dstack([nz, ny, nx]).astype(np.uint8) # BGR order for OpenCV
        return depth_smooth, normal_map

    def process(self, image_input: Any) -> Dict[str, Any]:
        """
        Executes the full preprocessing pipeline.
        Returns clean standardized stroke image, depth map, normal map, and statistics.
        """
        raw_img = self.load_image(image_input)
        orig_h, orig_w = raw_img.shape[:2]

        # 1. Standardize strokes & isolate
        stroke_mask, _ = self.standardize_strokes(raw_img)

        # 2. Auto-crop & center
        centered_stroke, bbox = self.center_and_crop(stroke_mask)

        # 3. Clean rendering: crisp dark strokes on pure white background
        clean_render = 255 - centered_stroke
        clean_render_bgr = cv2.cvtColor(clean_render, cv2.COLOR_GRAY2BGR)

        # 4. Generate pseudo-depth & normal maps
        depth_map, normal_map = self.generate_depth_and_normals(centered_stroke)
        depth_colored = cv2.applyColorMap(depth_map, cv2.COLORMAP_VIRIDIS)

        # 5. Compute metrics
        stroke_pixels = int(cv2.countNonZero(centered_stroke))
        total_pixels = self.target_size * self.target_size
        density = float(stroke_pixels / max(total_pixels, 1))

        return {
            "success": True,
            "original_dimensions": [orig_w, orig_h],
            "target_size": self.target_size,
            "bounding_box": list(bbox),
            "stroke_density": round(density, 4),
            "stroke_pixels": stroke_pixels,
            "cleaned_image_b64": self.to_base64(clean_render_bgr),
            "binary_mask_b64": self.to_base64(centered_stroke),
            "depth_map_b64": self.to_base64(depth_colored),
            "normal_map_b64": self.to_base64(normal_map),
        }

"""
Integrated Sketch Preprocessing and Geometric Analysis Pipeline
Coordinates all 12 stages into a cohesive, measurable computer vision engine.
Produces 9 image variants and a comprehensive quantitative JSON report.
"""

import time
from typing import Dict, Any, Tuple, Optional, Union
from pathlib import Path
import numpy as np
from PIL import Image

from .schemas import PreprocessingReport, ImageDimensions
from .image_loader import ImageLoader
from .image_validation import ImageValidator
from .enhancement import ImageEnhancer
from .denoising import SketchDenoiser
from .edge_detection import EdgeDetector
from .thresholding import SketchThresholder
from .contour_analysis import ContourAnalyzer
from .stroke_analysis import StrokeAnalyzer
from .symmetry_analysis import SymmetryAnalyzer
from .shape_analysis import ShapeAnalyzer
from .foreground_extraction import ForegroundExtractor
from .normalization import SketchNormalizer
from .visualization import SketchVisualizer


class SketchPreprocessingPipeline:
    def __init__(
        self,
        target_size: int = 512,
        padding_ratio: float = 0.12,
        background_color: Tuple[int, int, int] = (255, 255, 255),
        use_rembg: bool = False
    ):
        self.target_size = target_size
        self.padding_ratio = padding_ratio
        self.background_color = background_color
        
        # Sub-modules
        self.enhancer = ImageEnhancer()
        self.denoiser = SketchDenoiser()
        self.edge_detector = EdgeDetector()
        self.thresholder = SketchThresholder()
        self.contour_analyzer = ContourAnalyzer()
        self.stroke_analyzer = StrokeAnalyzer()
        self.symmetry_analyzer = SymmetryAnalyzer()
        self.shape_analyzer = ShapeAnalyzer()
        self.foreground_extractor = ForegroundExtractor(use_rembg=use_rembg)
        self.normalizer = SketchNormalizer(
            target_size=target_size,
            padding_ratio=padding_ratio,
            background_color=background_color
        )

    def process(
        self,
        image_input: Union[str, bytes, Path, Image.Image, np.ndarray],
        return_base64: bool = False
    ) -> Tuple[Dict[str, Any], PreprocessingReport]:
        """
        Executes the complete 12-phase computer vision pipeline.
        Returns:
            variants: Dictionary containing the 9 image representations (numpy arrays or base64 data URLs)
            report: PreprocessingReport containing quantitative geometric measurements
        """
        t0 = time.time()

        # 1. Load image and handle transparency
        bgr_original, alpha_channel = ImageLoader.load(image_input)
        
        # 2. Validation
        val_res = ImageValidator.validate_array(bgr_original, alpha_channel)
        if not val_res.is_valid:
            raise ValueError(f"Input image failed validation: {val_res.error_message}")

        # If alpha is present, composite onto white canvas for standard processing
        bgr_composited = ImageLoader.composite_on_background(bgr_original, alpha_channel, self.background_color)
        gray = ImageLoader.to_grayscale(bgr_composited)

        # 3. Enhancement
        enhanced_gray, enhance_metrics = self.enhancer.enhance(gray, auto_select=True)

        # 4. Denoising
        denoised_gray = self.denoiser.denoise_for_reconstruction(enhanced_gray, method="bilateral")

        # 5. Edge Detection
        edge_map, edge_metrics = self.edge_detector.detect_and_measure(denoised_gray, preferred_method="canny")

        # Check if input is a high-quality color image or photographic asset
        is_high_quality_color = False
        if bgr_original.ndim == 3 and bgr_original.shape[2] == 3:
            hsv = cv2.cvtColor(bgr_original, cv2.COLOR_BGR2HSV)
            sat = hsv[:, :, 1]
            mean_sat = float(np.mean(sat))
            b_ch, g_ch, r_ch = cv2.split(bgr_original)
            color_diff = float(np.mean(np.abs(r_ch.astype(float) - g_ch.astype(float)) + np.abs(g_ch.astype(float) - b_ch.astype(float))))
            if mean_sat > 12.0 or color_diff > 6.0:
                is_high_quality_color = True

        if alpha_channel is not None and np.count_nonzero(alpha_channel > 10) > 100:
            # Alpha cutout provided in high-quality PNG
            clean_mask = alpha_channel
        elif is_high_quality_color:
            # Segment solid object from background preserving solid interior and colors
            corner_colors = [
                bgr_composited[0, 0],
                bgr_composited[0, -1],
                bgr_composited[-1, 0],
                bgr_composited[-1, -1]
            ]
            bg_color = np.median(corner_colors, axis=0)
            diff = np.linalg.norm(bgr_composited.astype(float) - bg_color, axis=2)
            raw_mask = (diff > 18.0).astype(np.uint8) * 255
            contours, _ = cv2.findContours(raw_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            clean_mask = np.zeros_like(raw_mask)
            for cnt in contours:
                if cv2.contourArea(cnt) > 200:
                    cv2.drawContours(clean_mask, [cnt], -1, 255, thickness=cv2.FILLED)
            if np.count_nonzero(clean_mask) < 100:
                clean_mask = np.full_like(raw_mask, 255)
        else:
            # 6. Adaptive Thresholding for black-and-white line sketches
            raw_binary = self.thresholder.binarize(denoised_gray, method="adaptive_gaussian", apply_morphology=True)

            # 7. Foreground Extraction & Noise Cleanup
            clean_mask, rgba_cutout = self.foreground_extractor.extract_foreground(
                bgr_composited, raw_binary, alpha_channel
            )

        # 8. Contour Intelligence
        contour_overlay, contour_metrics, valid_contours = self.contour_analyzer.analyze_contours(clean_mask)
        main_contour = valid_contours[0] if len(valid_contours) > 0 else None

        # 9. Stroke Analysis (Skeleton & Distance Transform)
        skeleton, dist_transform, stroke_metrics = self.stroke_analyzer.analyze_strokes(clean_mask)

        # 10. Bilateral Symmetry Analysis
        symmetry_metrics = self.symmetry_analyzer.analyze_symmetry(clean_mask)

        # 11. Shape Analysis & PCA Orientation
        shape_metrics = self.shape_analyzer.analyze_shape(clean_mask, main_contour)

        # 12. Reconstruction Normalization (Center, Pad, 512x512)
        reconstruction_rgb, reconstruction_rgba, normalized_mask = self.normalizer.normalize(
            bgr_composited, clean_mask
        )

        duration_ms = round((time.time() - t0) * 1000.0, 2)

        # Build 9 Image Variants
        variants = {
            "original_image": bgr_original,
            "enhanced_image": enhanced_gray,
            "denoised_image": denoised_gray,
            "binary_image": clean_mask,
            "edge_image": edge_map,
            "contour_visualization": contour_overlay,
            "skeleton_image": skeleton,
            "foreground_mask": normalized_mask,
            "final_reconstruction_input": reconstruction_rgb
        }

        # Build Structured Report
        report = PreprocessingReport(
            image_dimensions={
                "width": val_res.dimensions.width,
                "height": val_res.dimensions.height,
                "channels": val_res.dimensions.channels,
                "aspect_ratio": val_res.dimensions.aspect_ratio
            },
            foreground_occupancy=shape_metrics.foreground_occupancy,
            edge_density=edge_metrics.edge_density,
            contour_count=contour_metrics.contour_count,
            stroke_analysis={
                "average_width_estimate": stroke_metrics.average_width_estimate,
                "stroke_density": stroke_metrics.stroke_density,
                "total_stroke_length": stroke_metrics.total_stroke_length,
                "endpoint_count": stroke_metrics.endpoint_count,
                "junction_count": stroke_metrics.junction_count,
                "connected_components_count": stroke_metrics.connected_components_count,
                "line_continuity_score": stroke_metrics.line_continuity_score
            },
            shape_analysis={
                "bounding_box": list(shape_metrics.bounding_box),
                "aspect_ratio": shape_metrics.aspect_ratio,
                "centroid": list(shape_metrics.centroid),
                "compactness": shape_metrics.compactness,
                "complexity": shape_metrics.contour_complexity,
                "edge_density": shape_metrics.edge_density,
                "orientation_degrees": shape_metrics.orientation_degrees,
                "eccentricity": shape_metrics.eccentricity
            },
            symmetry={
                "horizontal": symmetry_metrics.horizontal_symmetry,
                "vertical": symmetry_metrics.vertical_symmetry,
                "estimated_axis_x": symmetry_metrics.estimated_axis_x,
                "estimated_axis_y": symmetry_metrics.estimated_axis_y,
                "score": symmetry_metrics.symmetry_score
            },
            metadata={
                "processing_time_ms": duration_ms,
                "contour_solidity": contour_metrics.solidity,
                "contour_extent": contour_metrics.extent,
                "hierarchy_depth": contour_metrics.hierarchy_depth,
                "enhancement": {
                    "contrast_before": enhance_metrics.contrast_std_before,
                    "contrast_after": enhance_metrics.contrast_std_after,
                    "illumination_corrected": enhance_metrics.illumination_corrected
                }
            }
        )

        if return_base64:
            b64_variants = {
                name: SketchVisualizer.to_base64(img)
                for name, img in variants.items()
            }
            return b64_variants, report

        return variants, report

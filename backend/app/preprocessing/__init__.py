"""
OpenCV Sketch Preprocessing & Stroke Analysis Package
Provides modular computer vision tools for sketch enhancement, morphology,
stroke topology extraction, and 3D reconstruction normalization.
"""

from .schemas import (
    ImageDimensions,
    ValidationResult,
    EnhancementMetrics,
    EdgeMetrics,
    ContourMetrics,
    StrokeMetrics,
    SymmetryMetrics,
    ShapeMetrics,
    PreprocessingReport
)
from .image_loader import ImageLoader
from .image_validation import ImageValidator
from .enhancement import ImageEnhancer
from .denoising import SketchDenoiser
from .edge_detection import EdgeDetector
from .thresholding import SketchThresholder
from .contour_analysis import ContourAnalyzer
from .stroke_analysis import StrokeAnalyzer
from .skeletonization import SketchSkeletonizer
from .symmetry_analysis import SymmetryAnalyzer
from .shape_analysis import ShapeAnalyzer
from .foreground_extraction import ForegroundExtractor
from .normalization import SketchNormalizer
from .visualization import SketchVisualizer
from .preprocessing_pipeline import SketchPreprocessingPipeline
from .sketch_processor import SketchPreprocessor

__all__ = [
    "ImageDimensions",
    "ValidationResult",
    "EnhancementMetrics",
    "EdgeMetrics",
    "ContourMetrics",
    "StrokeMetrics",
    "SymmetryMetrics",
    "ShapeMetrics",
    "PreprocessingReport",
    "ImageLoader",
    "ImageValidator",
    "ImageEnhancer",
    "SketchDenoiser",
    "EdgeDetector",
    "SketchThresholder",
    "ContourAnalyzer",
    "StrokeAnalyzer",
    "SketchSkeletonizer",
    "SymmetryAnalyzer",
    "ShapeAnalyzer",
    "ForegroundExtractor",
    "SketchNormalizer",
    "SketchVisualizer",
    "SketchPreprocessingPipeline",
    "SketchPreprocessor"
]

"""
Image Validation and Sanitization Module
Checks image formats, dimensions, channels, aspect ratio, and detects corrupt or blank images.
"""

from typing import Tuple, Optional, Union
from pathlib import Path
import numpy as np

from .schemas import ValidationResult, ImageDimensions


class ImageValidator:
    ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
    MIN_DIMENSION = 16
    MAX_DIMENSION = 8192
    MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB

    @classmethod
    def validate_file_path(cls, file_path: Union[str, Path]) -> Tuple[bool, Optional[str]]:
        path = Path(file_path)
        if not path.exists():
            return False, f"File does not exist: {path}"
        if path.suffix.lower() not in cls.ALLOWED_EXTENSIONS:
            return False, f"Unsupported file extension '{path.suffix}'. Allowed: {cls.ALLOWED_EXTENSIONS}"
        size = path.stat().st_size
        if size == 0:
            return False, "File is 0 bytes."
        if size > cls.MAX_FILE_SIZE_BYTES:
            return False, f"File size ({size / (1024*1024):.1f} MB) exceeds maximum allowed ({cls.MAX_FILE_SIZE_BYTES / (1024*1024):.1f} MB)."
        return True, None

    @classmethod
    def validate_array(
        cls,
        image_array: np.ndarray,
        alpha_channel: Optional[np.ndarray] = None,
        source_format: str = "png"
    ) -> ValidationResult:
        if image_array is None or not isinstance(image_array, np.ndarray) or image_array.size == 0:
            return ValidationResult(
                is_valid=False,
                format=source_format,
                dimensions=ImageDimensions(0, 0, 0, 0.0),
                file_size_bytes=0,
                has_alpha=False,
                is_grayscale=False,
                error_message="Image array is empty, None, or invalid type."
            )

        h, w = image_array.shape[:2]
        c = 1 if image_array.ndim == 2 else image_array.shape[2]
        has_alpha = alpha_channel is not None
        if has_alpha:
            c = 4

        aspect_ratio = float(w) / float(h) if h > 0 else 0.0
        dims = ImageDimensions(width=w, height=h, channels=c, aspect_ratio=round(aspect_ratio, 4))
        approx_bytes = image_array.nbytes + (alpha_channel.nbytes if has_alpha else 0)

        # Dimension checks
        if w < cls.MIN_DIMENSION or h < cls.MIN_DIMENSION:
            return ValidationResult(
                is_valid=False,
                format=source_format,
                dimensions=dims,
                file_size_bytes=approx_bytes,
                has_alpha=has_alpha,
                is_grayscale=(c == 1),
                error_message=f"Image dimension ({w}x{h}) is below minimum ({cls.MIN_DIMENSION}x{cls.MIN_DIMENSION})."
            )

        if w > cls.MAX_DIMENSION or h > cls.MAX_DIMENSION:
            return ValidationResult(
                is_valid=False,
                format=source_format,
                dimensions=dims,
                file_size_bytes=approx_bytes,
                has_alpha=has_alpha,
                is_grayscale=(c == 1),
                error_message=f"Image dimension ({w}x{h}) exceeds maximum ({cls.MAX_DIMENSION}x{cls.MAX_DIMENSION})."
            )

        # Blank / Uniform image check (zero variance)
        var = float(np.var(image_array))
        if var < 1e-4:
            return ValidationResult(
                is_valid=False,
                format=source_format,
                dimensions=dims,
                file_size_bytes=approx_bytes,
                has_alpha=has_alpha,
                is_grayscale=(c == 1),
                error_message="Image is uniform or completely blank (pixel variance near zero)."
            )

        return ValidationResult(
            is_valid=True,
            format=source_format,
            dimensions=dims,
            file_size_bytes=approx_bytes,
            has_alpha=has_alpha,
            is_grayscale=(c == 1),
            error_message=None
        )

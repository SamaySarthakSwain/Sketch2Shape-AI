"""
Denoising and Noise Filtering Module
Implements Gaussian Blur, Median Filter, Bilateral Edge-Preserving Filter, and Non-Local Means.
"""

from typing import Dict, Any, Tuple
import numpy as np
import cv2


class SketchDenoiser:
    def __init__(
        self,
        gaussian_ksize: int = 3,
        gaussian_sigma: float = 0.8,
        median_ksize: int = 3,
        bilateral_d: int = 5,
        bilateral_sigma_color: float = 40.0,
        bilateral_sigma_space: float = 40.0,
        nlm_h: float = 10.0,
        nlm_template_size: int = 7,
        nlm_search_size: int = 21
    ):
        self.gaussian_ksize = gaussian_ksize if gaussian_ksize % 2 == 1 else gaussian_ksize + 1
        self.gaussian_sigma = gaussian_sigma
        self.median_ksize = median_ksize if median_ksize % 2 == 1 else median_ksize + 1
        self.bilateral_d = bilateral_d
        self.bilateral_sigma_color = bilateral_sigma_color
        self.bilateral_sigma_space = bilateral_sigma_space
        self.nlm_h = nlm_h
        self.nlm_template_size = nlm_template_size
        self.nlm_search_size = nlm_search_size

    def gaussian(self, img: np.ndarray) -> np.ndarray:
        return cv2.GaussianBlur(img, (self.gaussian_ksize, self.gaussian_ksize), self.gaussian_sigma)

    def median(self, img: np.ndarray) -> np.ndarray:
        return cv2.medianBlur(img, self.median_ksize)

    def bilateral(self, img: np.ndarray) -> np.ndarray:
        return cv2.bilateralFilter(
            img,
            d=self.bilateral_d,
            sigmaColor=self.bilateral_sigma_color,
            sigmaSpace=self.bilateral_sigma_space
        )

    def non_local_means(self, img: np.ndarray) -> np.ndarray:
        if img.ndim == 2:
            return cv2.fastNlMeansDenoising(
                img,
                h=self.nlm_h,
                templateWindowSize=self.nlm_template_size,
                searchWindowSize=self.nlm_search_size
            )
        else:
            return cv2.fastNlMeansDenoisingColored(
                img,
                h=self.nlm_h,
                hColor=self.nlm_h,
                templateWindowSize=self.nlm_template_size,
                searchWindowSize=self.nlm_search_size
            )

    def compare_methods(self, gray: np.ndarray) -> Dict[str, np.ndarray]:
        """Generates denoised variants for algorithmic evaluation."""
        return {
            "original": gray.copy(),
            "gaussian": self.gaussian(gray),
            "median": self.median(gray),
            "bilateral": self.bilateral(gray),
            "non_local_means": self.non_local_means(gray)
        }

    def denoise_for_reconstruction(self, gray: np.ndarray, method: str = "bilateral") -> np.ndarray:
        """
        Bilateral filtering is the default for sketch reconstruction as it smooths
        uniform paper noise without blurring fine stroke boundaries.
        """
        method_lower = method.lower()
        if method_lower == "bilateral":
            return self.bilateral(gray)
        elif method_lower == "gaussian":
            return self.gaussian(gray)
        elif method_lower == "median":
            return self.median(gray)
        elif method_lower in ("nlm", "non_local_means"):
            return self.non_local_means(gray)
        else:
            return self.bilateral(gray)

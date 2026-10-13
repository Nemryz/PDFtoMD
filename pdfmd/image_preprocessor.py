"""Image preprocessor for enhancing scanned pages before OCR.

This module applies contrast enhancement, sharpness enhancement, noise reduction,
and binarization to improve OCR accuracy on low-quality scans.
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from pdfmd.types import PreprocessedImage

if TYPE_CHECKING:
    from PIL import Image

logger = logging.getLogger(__name__)


class ImagePreprocessor:
    """Preprocesses images to improve OCR accuracy."""

    def preprocess(
        self,
        img: Image.Image,
        steps: list[str] | None = None,
        enhance_contrast: float = 1.5,
        enhance_sharpness: float = 1.5,
    ) -> PreprocessedImage:
        """Apply preprocessing steps to an image.

        Args:
            img: Input PIL Image.
            steps: List of preprocessing steps to apply.
                   Options: 'contrast', 'sharpness', 'denoise', 'binarize'
                   If None, uses adaptive preprocessing based on image analysis.
            enhance_contrast: Contrast enhancement factor (1.0 = no change).
            enhance_sharpness: Sharpness enhancement factor (1.0 = no change).

        Returns:
            PreprocessedImage with the enhanced image and metadata.
        """
        start_time = time.time()
        applied_steps: list[str] = []

        # Adaptive preprocessing if no steps specified
        if steps is None:
            steps = self._analyze_and_select_steps(img)

        processed_img = img.copy()

        for step in steps:
            if step == "contrast":
                processed_img = self._enhance_contrast(processed_img, enhance_contrast)
                applied_steps.append("contrast")
            elif step == "sharpness":
                processed_img = self._enhance_sharpness(processed_img, enhance_sharpness)
                applied_steps.append("sharpness")
            elif step == "denoise":
                processed_img = self._denoise(processed_img)
                applied_steps.append("denoise")
            elif step == "binarize":
                processed_img = self._binarize(processed_img)
                applied_steps.append("binarize")
            else:
                logger.warning(f"Unknown preprocessing step: {step}")

        elapsed_ms = (time.time() - start_time) * 1000

        return PreprocessedImage(
            image=processed_img,
            steps_applied=applied_steps,
            processing_time_ms=elapsed_ms,
        )

    def _analyze_and_select_steps(self, img: Image.Image) -> list[str]:
        """Analyze image and select appropriate preprocessing steps.

        Returns:
            List of recommended preprocessing steps.
        """
        from PIL import ImageStat

        steps = []

        # Analyze contrast
        stat = ImageStat.Stat(img)
        if len(stat.stddev) >= 3:
            # Color image
            avg_std = sum(stat.stddev[:3]) / 3
        else:
            # Grayscale
            avg_std = stat.stddev[0]

        # Low contrast -> enhance
        if avg_std < 30:
            steps.append("contrast")
            logger.debug(
                f"Low contrast detected (stddev={avg_std:.1f}), adding contrast enhancement"
            )

        # Analyze noise using Laplacian variance
        try:
            import cv2
            import numpy as np

            # Convert to numpy array
            img_array = np.array(img.convert("L"))
            # Laplacian variance (low = noisy)
            laplacian = cv2.Laplacian(img_array, cv2.CV_64F)
            noise_metric = laplacian.var()

            if noise_metric < 100:
                steps.append("denoise")
                logger.debug(f"Noise detected (laplacian_var={noise_metric:.1f}), adding denoise")

                # Also add sharpening after denoising
                steps.append("sharpness")

        except ImportError:
            # OpenCV not available, skip noise analysis
            pass

        # Always add sharpness for scanned documents
        if "sharpness" not in steps:
            steps.append("sharpness")

        return steps

    def _enhance_contrast(
        self,
        img: Image.Image,
        factor: float = 1.5,
    ) -> Image.Image:
        """Enhance image contrast.

        Args:
            img: Input image.
            factor: Enhancement factor (1.0 = no change, >1 = more contrast).

        Returns:
            Enhanced image.
        """
        from PIL import ImageEnhance

        enhancer = ImageEnhance.Contrast(img)
        return enhancer.enhance(factor)

    def _enhance_sharpness(
        self,
        img: Image.Image,
        factor: float = 1.5,
    ) -> Image.Image:
        """Enhance image sharpness.

        Args:
            img: Input image.
            factor: Enhancement factor (1.0 = no change, >1 = sharper).

        Returns:
            Enhanced image.
        """
        from PIL import ImageEnhance

        enhancer = ImageEnhance.Sharpness(img)
        return enhancer.enhance(factor)

    def _denoise(self, img: Image.Image) -> Image.Image:
        """Reduce image noise using median filter.

        Args:
            img: Input image.

        Returns:
            Denoised image.
        """
        from PIL import ImageFilter

        return img.filter(ImageFilter.MedianFilter(size=3))

    def _binarize(self, img: Image.Image) -> Image.Image:
        """Binarize image using Otsu's thresholding.

        Args:
            img: Input image.

        Returns:
            Binarized image (black and white).
        """
        import numpy as np

        # Convert to grayscale if needed
        if img.mode != "L":
            img = img.convert("L")

        # Convert to numpy array
        img_array = np.array(img)

        # Simple Otsu's thresholding
        threshold = self._otsu_threshold(img_array)

        # Apply threshold
        binary = ((img_array > threshold) * 255).astype(np.uint8)

        # Convert back to PIL
        from PIL import Image as PILImage

        return PILImage.fromarray(binary)

    @staticmethod
    def _otsu_threshold(histogram: np.ndarray) -> int:
        """Calculate Otsu's threshold from histogram.

        Args:
            histogram: 2D array (grayscale image).

        Returns:
            Optimal threshold value.
        """
        import numpy as np

        # Calculate histogram
        hist, _ = np.histogram(histogram, bins=256, range=(0, 256))
        total = histogram.size

        # Otsu's method
        sum_total = np.sum(np.arange(256) * hist)
        sum_bg = 0
        weight_bg = 0
        max_variance = 0
        threshold = 0

        for i in range(256):
            weight_bg += hist[i]
            if weight_bg == 0:
                continue

            weight_fg = total - weight_bg
            if weight_fg == 0:
                break

            sum_bg += i * hist[i]
            mean_bg = sum_bg / weight_bg
            mean_fg = (sum_total - sum_bg) / weight_fg

            variance = weight_bg * weight_fg * (mean_bg - mean_fg) ** 2

            if variance > max_variance:
                max_variance = variance
                threshold = i

        return threshold


def _laplacian_variance(gray: Image.Image) -> float:
    """Compute Laplacian variance of a grayscale image (sharpness metric).

    Uses the standard 4-neighbourhood Laplacian kernel via numpy —
    no OpenCV dependency. High variance = sharp, low = blurry/uniform.

    Args:
        gray: Grayscale PIL Image.

    Returns:
        Laplacian variance (float).
    """
    import numpy as np

    arr = np.asarray(gray, dtype=np.float64)
    lap = -4.0 * arr[1:-1, 1:-1] + arr[:-2, 1:-1] + arr[2:, 1:-1] + arr[1:-1, :-2] + arr[1:-1, 2:]
    return float(lap.var())


def should_preprocess(image: Image.Image) -> bool:
    """Return True if the image would benefit from preprocessing (US-2).

    Gate logic — skip only when clearly good or clearly hopeless:
    - Blank/near-uniform images (stddev < 5): False — nothing to enhance.
    - Good-quality images (stddev >= 40 AND Laplacian variance >= 150):
      False — preprocessing adds cost without quality gain.
    - Everything else (low contrast, noise, blur): True.

    Args:
        image: PIL Image to evaluate (any mode).

    Returns:
        True if preprocessing should run, False to skip it.
    """
    from PIL import ImageStat

    gray = image.convert("L") if image.mode != "L" else image

    stat = ImageStat.Stat(gray)
    stddev = stat.stddev[0]

    # Blank / near-uniform page: no content to enhance
    if stddev < 5:
        return False

    # Good contrast AND sharp enough: skip preprocessing
    if stddev >= 40:
        if _laplacian_variance(gray) >= 150:
            return False

    # Low contrast, noise, or blur: preprocess
    return True


def preprocess_image(
    img: Image.Image,
    steps: list[str] | None = None,
) -> PreprocessedImage:
    """Convenience function for image preprocessing.

    Args:
        img: Input PIL Image.
        steps: Preprocessing steps (None for adaptive).

    Returns:
        PreprocessedImage with enhanced image.
    """
    preprocessor = ImagePreprocessor()
    return preprocessor.preprocess(img, steps=steps)

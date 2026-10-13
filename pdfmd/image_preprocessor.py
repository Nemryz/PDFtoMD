# Cleanup for scanned pages before OCR sees them.

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from pdfmd.types import PreprocessedImage

if TYPE_CHECKING:
    from PIL import Image

logger = logging.getLogger(__name__)


class ImagePreprocessor:
    # I run the requested steps in order and report what I actually applied.

    def preprocess(
        self,
        img: Image.Image,
        steps: list[str] | None = None,
        enhance_contrast: float = 1.5,
        enhance_sharpness: float = 1.5,
    ) -> PreprocessedImage:
        # Given no steps I decide for myself, based on what the image looks like.
        start_time = time.time()
        applied_steps: list[str] = []

        # No steps means pick from the analysis below.
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
        # I look at contrast and noise, then choose the steps that help this image.
        from PIL import ImageStat

        steps = []

        # Low contrast is the most common problem in scans.
        stat = ImageStat.Stat(img)
        if len(stat.stddev) >= 3:
            # I work in HSV because luminance alone hides washed out colour.
            avg_std = sum(stat.stddev[:3]) / 3
        else:
            # Grey has no saturation, so the check only means something for colour.
            avg_std = stat.stddev[0]

        # Flat histogram means the page needs stretching.
        if avg_std < 30:
            steps.append("contrast")
            logger.debug(
                f"Low contrast detected (stddev={avg_std:.1f}), adding contrast enhancement"
            )

        # The Laplacian picks up speckle at high frequencies, which is what noise looks like.
        try:
            import cv2
            import numpy as np

            # OpenCV wants a numpy array rather than a PIL image.
            img_array = np.array(img.convert("L"))
            # Low variance means noisy, high means already clean.
            laplacian = cv2.Laplacian(img_array, cv2.CV_64F)
            noise_metric = laplacian.var()

            if noise_metric < 100:
                steps.append("denoise")
                logger.debug(f"Noise detected (laplacian_var={noise_metric:.1f}), adding denoise")

                # Denoise alone leaves edges soft, so I follow it with sharpening.
                steps.append("sharpness")

        except ImportError:
            # Without OpenCV I skip the noise step rather than guess.
            pass

        # Scans are always a bit soft, so sharpness helps even when nothing else fires.
        if "sharpness" not in steps:
            steps.append("sharpness")

        return steps

    def _enhance_contrast(
        self,
        img: Image.Image,
        factor: float = 1.5,
    ) -> Image.Image:
        # I stretch the histogram to push values toward the full range.
        from PIL import ImageEnhance

        enhancer = ImageEnhance.Contrast(img)
        return enhancer.enhance(factor)

    def _enhance_sharpness(
        self,
        img: Image.Image,
        factor: float = 1.5,
    ) -> Image.Image:
        # An unsharp mask, which recovers edges better than plain blur.
        from PIL import ImageEnhance

        enhancer = ImageEnhance.Sharpness(img)
        return enhancer.enhance(factor)

    def _denoise(self, img: Image.Image) -> Image.Image:
        # A median filter removes speckle while keeping thin strokes intact.
        from PIL import ImageFilter

        return img.filter(ImageFilter.MedianFilter(size=3))

    def _binarize(self, img: Image.Image) -> Image.Image:
        # Otsu picks the threshold from the histogram instead of a fixed number.
        import numpy as np

        # Binarising a colour image makes no sense, so I convert first.
        if img.mode != "L":
            img = img.convert("L")

        # Same numpy hop as above.
        img_array = np.array(img)

        # A plain Otsu implementation on a histogram with 256 bins.
        threshold = self._otsu_threshold(img_array)

        # Apply threshold
        binary = ((img_array > threshold) * 255).astype(np.uint8)

        # OpenCV works in numpy, so I go back to PIL at the end.
        from PIL import Image as PILImage

        return PILImage.fromarray(binary)

    @staticmethod
    def _otsu_threshold(histogram: np.ndarray) -> int:
        # The value Otsu picks, exposed separately so tests can check it.
        import numpy as np

        # 256 bins covers the whole byte range.
        hist, _ = np.histogram(histogram, bins=256, range=(0, 256))
        total = histogram.size

        # The variance between the two classes is what Otsu maximises.
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
    # I use Laplacian variance as the sharpness number, because blur flattens it.
    import numpy as np

    arr = np.asarray(gray, dtype=np.float64)
    lap = -4.0 * arr[1:-1, 1:-1] + arr[:-2, 1:-1] + arr[2:, 1:-1] + arr[1:-1, :-2] + arr[1:-1, 2:]
    return float(lap.var())


def should_preprocess(image: Image.Image) -> bool:
    # I decide whether enhancing is worth the time, based on contrast and sharpness together.
    from PIL import ImageStat

    gray = image.convert("L") if image.mode != "L" else image

    stat = ImageStat.Stat(gray)
    stddev = stat.stddev[0]

    # A blank page has nothing to enhance and would only cost time.
    if stddev < 5:
        return False

    # Good contrast and sharp enough means the image is already fine.
    if stddev >= 40:
        if _laplacian_variance(gray) >= 150:
            return False

    # Anything else is worth another pass.
    return True


def preprocess_image(
    img: Image.Image,
    steps: list[str] | None = None,
) -> PreprocessedImage:
    # A shortcut for the common case of preprocessing then analysing.
    preprocessor = ImagePreprocessor()
    return preprocessor.preprocess(img, steps=steps)

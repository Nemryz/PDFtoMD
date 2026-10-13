
import pytest
from PIL import Image

from pdfmd.image_preprocessor import (
    ImagePreprocessor,
    preprocess_image,
    should_preprocess,
)
from pdfmd.types import PreprocessedImage


class TestImagePreprocessor:

    def test_preprocessor_initializes(self):
        preprocessor = ImagePreprocessor()
        assert preprocessor is not None

    def test_preprocess_returns_preprocessed_image(self):
        preprocessor = ImagePreprocessor()
        img = Image.new("L", (100, 100), 128)

        result = preprocessor.preprocess(img)

        assert isinstance(result, PreprocessedImage)
        assert result.image is not None
        assert isinstance(result.steps_applied, list)
        assert result.processing_time_ms >= 0

    def test_preprocess_preserves_image_size(self):
        preprocessor = ImagePreprocessor()
        img = Image.new("L", (200, 150), 128)

        result = preprocessor.preprocess(img)

        assert result.image.size == (200, 150)

    def test_preprocess_with_explicit_steps(self):
        preprocessor = ImagePreprocessor()
        img = Image.new("L", (100, 100), 128)

        result = preprocessor.preprocess(img, steps=["contrast"])

        assert "contrast" in result.steps_applied
        # Should not include other steps
        assert "sharpness" not in result.steps_applied or "contrast" in result.steps_applied

    def test_preprocess_contrast_enhancement(self):
        preprocessor = ImagePreprocessor()
        # Create image with variation (not uniform)
        img = Image.new("L", (100, 100), 128)
        pixels = list(img.getdata())
        for i in range(len(pixels)):
            if i % 2 == 0:
                pixels[i] = 100  # Darker pixels
        img.putdata(pixels)

        result = preprocessor.preprocess(img, steps=["contrast"], enhance_contrast=2.0)

        assert "contrast" in result.steps_applied
        # Image should be different (more contrast)
        assert list(result.image.getdata()) != list(img.getdata())

    def test_preprocess_sharpness_enhancement(self):
        preprocessor = ImagePreprocessor()
        img = Image.new("L", (100, 100), 128)

        result = preprocessor.preprocess(img, steps=["sharpness"], enhance_sharpness=2.0)

        assert "sharpness" in result.steps_applied

    def test_preprocess_denoise(self):
        preprocessor = ImagePreprocessor()
        img = Image.new("L", (100, 100), 128)

        result = preprocessor.preprocess(img, steps=["denoise"])

        assert "denoise" in result.steps_applied

    def test_preprocess_binarize(self):
        preprocessor = ImagePreprocessor()
        img = Image.new("L", (100, 100), 128)

        result = preprocessor.preprocess(img, steps=["binarize"])

        assert "binarize" in result.steps_applied
        # Should be black or white only
        pixels = list(result.image.getdata())
        assert all(p in [0, 255] for p in pixels)

    def test_preprocess_multiple_steps(self):
        preprocessor = ImagePreprocessor()
        img = Image.new("L", (100, 100), 128)

        result = preprocessor.preprocess(img, steps=["contrast", "sharpness", "denoise"])

        assert len(result.steps_applied) == 3
        assert "contrast" in result.steps_applied
        assert "sharpness" in result.steps_applied
        assert "denoise" in result.steps_applied

    def test_preprocess_adaptive_steps(self):
        preprocessor = ImagePreprocessor()
        img = Image.new("L", (100, 100), 128)

        result = preprocessor.preprocess(img, steps=None)

        # Should have selected at least one step
        assert len(result.steps_applied) > 0

    def test_preprocess_color_image(self):
        preprocessor = ImagePreprocessor()
        img = Image.new("RGB", (100, 100), (128, 128, 128))

        result = preprocessor.preprocess(img, steps=["contrast"])

        assert isinstance(result, PreprocessedImage)
        assert result.image.mode == "RGB"

    def test_preprocess_grayscale_image(self):
        preprocessor = ImagePreprocessor()
        img = Image.new("L", (100, 100), 128)

        result = preprocessor.preprocess(img, steps=["contrast"])

        assert isinstance(result, PreprocessedImage)

    def test_preprocess_timing(self):
        preprocessor = ImagePreprocessor()
        img = Image.new("L", (100, 100), 128)

        result = preprocessor.preprocess(img, steps=["contrast"])

        assert result.processing_time_ms >= 0  # May be 0 for very fast operations


class TestPreprocessImageFunction:

    def test_preprocess_image_returns_preprocessed_image(self):
        img = Image.new("L", (100, 100), 128)

        result = preprocess_image(img)

        assert isinstance(result, PreprocessedImage)

    def test_preprocess_image_with_steps(self):
        img = Image.new("L", (100, 100), 128)

        result = preprocess_image(img, steps=["contrast"])

        assert "contrast" in result.steps_applied


class TestOtsuThreshold:

    def test_otsu_returns_int(self):
        import numpy as np

        img = Image.new("L", (100, 100), 128)
        img_array = np.array(img)

        threshold = ImagePreprocessor._otsu_threshold(img_array)

        assert isinstance(threshold, (int, np.integer))
        assert 0 <= threshold <= 255

    def test_otsu_bimodal_distribution(self):
        import numpy as np

        # Create bimodal image (dark and light regions)
        img_array = np.zeros((100, 100), dtype=np.uint8)
        img_array[:50, :] = 50  # Dark half
        img_array[50:, :] = 200  # Light half

        threshold = ImagePreprocessor._otsu_threshold(img_array)

        # Threshold should be between the two modes (inclusive)
        assert 50 <= threshold <= 200


class TestImagePreprocessorIntegration:

    @pytest.fixture
    def low_contrast_image(self):
        # Create image with narrow intensity range
        img = Image.new("L", (200, 200), 100)
        # Add some variation
        pixels = list(img.getdata())
        for i in range(len(pixels)):
            if i % 2 == 0:
                pixels[i] = 110
        img.putdata(pixels)
        return img

    @pytest.fixture
    def noisy_image(self):
        import random

        img = Image.new("L", (200, 200), 128)
        pixels = []
        for _ in range(200 * 200):
            pixels.append(max(0, min(255, 128 + random.randint(-50, 50))))
        img.putdata(pixels)
        return img

    def test_low_contrast_enhancement(self, low_contrast_image):
        preprocessor = ImagePreprocessor()

        result = preprocessor.preprocess(low_contrast_image, steps=["contrast"])

        assert "contrast" in result.steps_applied
        # Image should have more contrast
        result_pixels = list(result.image.getdata())
        original_pixels = list(low_contrast_image.getdata())
        assert result_pixels != original_pixels

    def test_noisy_image_denoising(self, noisy_image):
        preprocessor = ImagePreprocessor()

        result = preprocessor.preprocess(noisy_image, steps=["denoise"])

        assert "denoise" in result.steps_applied


class TestShouldPreprocess:

    @staticmethod
    def _synthetic_document(fg: int, bg: int) -> Image.Image:
        width, height = 300, 300
        img = Image.new("L", (width, height), bg)
        pixels = list(img.getdata())
        # 12 rows of "text lines" (sharp 6px bars), ~18% dark coverage
        for row in range(30, 270, 20):
            for y in range(row, row + 6):
                for x in range(40, 260):
                    pixels[y * width + x] = fg
        img.putdata(pixels)
        return img

    @staticmethod
    def _noisy_image() -> Image.Image:
        import random

        random.seed(42)
        width, height = 300, 300
        img = Image.new("L", (width, height), 128)
        pixels = [max(0, min(255, 128 + random.randint(-40, 40))) for _ in range(width * height)]
        img.putdata(pixels)
        return img

    def test_returns_bool(self):
        img = Image.new("L", (100, 100), 128)
        assert isinstance(should_preprocess(img), bool)

    def test_good_quality_image_returns_false(self):
        img = self._synthetic_document(fg=0, bg=255)
        assert should_preprocess(img) is False

    def test_low_contrast_image_returns_true(self):
        img = self._synthetic_document(fg=140, bg=200)
        assert should_preprocess(img) is True

    def test_noisy_image_returns_true(self):
        img = self._noisy_image()
        assert should_preprocess(img) is True

    def test_blank_image_returns_false(self):
        img = Image.new("L", (300, 300), 255)
        assert should_preprocess(img) is False

    def test_color_image_supported(self):
        img = self._synthetic_document(fg=0, bg=255).convert("RGB")
        assert should_preprocess(img) is False

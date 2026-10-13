
from pathlib import Path

import pymupdf

from pdfmd.page_classifier import PageClassifier
from pdfmd.types import PageClassification


class TestBlankPageDetection:

    def test_blank_page_detected_heuristic(self):
        classifier = PageClassifier()
        # Force heuristic mode
        classifier._ocrsieve_available = False
        classifier._classifier = None

        doc = pymupdf.open()
        page = doc.new_page()  # Completely empty

        result = classifier.classify_page(doc, 0)

        assert result.classification == PageClassification.BLANK
        assert result.needs_ocr is False
        assert result.confidence >= 0.8

        doc.close()

    def test_text_page_not_blank_heuristic(self):
        classifier = PageClassifier()
        # Force heuristic mode
        classifier._ocrsieve_available = False
        classifier._classifier = None

        doc = pymupdf.open()
        page = doc.new_page()
        page.insert_text((72, 72), "This is not blank. " * 20)

        result = classifier.classify_page(doc, 0)

        assert result.classification != PageClassification.BLANK
        assert result.needs_ocr is True

        doc.close()

    def test_blank_page_in_multi_page_heuristic(self):
        classifier = PageClassifier()
        # Force heuristic mode
        classifier._ocrsieve_available = False
        classifier._classifier = None

        doc = pymupdf.open()

        # Page 1: Text
        page1 = doc.new_page()
        page1.insert_text((72, 72), "Page 1 content")

        # Page 2: Blank
        doc.new_page()

        # Page 3: Text
        page3 = doc.new_page()
        page3.insert_text((72, 72), "Page 3 content")

        temp_path = Path("test_blank_multi.pdf")
        doc.save(str(temp_path))
        doc.close()

        try:
            results = classifier.classify_document(temp_path)

            assert len(results) == 3
            assert results[0].classification != PageClassification.BLANK
            assert results[1].classification == PageClassification.BLANK
            assert results[2].classification != PageClassification.BLANK
        finally:
            temp_path.unlink(missing_ok=True)


class TestBlankPageHeuristic:

    def test_pixel_variance_blank(self):
        classifier = PageClassifier()

        # Create a truly blank image (all same pixels)
        import numpy as np
        from PIL import Image

        img = Image.new("L", (100, 100), 128)
        img_array = np.array(img)

        # Calculate variance manually
        mean = img_array.mean()
        variance = ((img_array - mean) ** 2).mean()

        # Very low variance = blank
        assert variance == 0.0  # Uniform image has 0 variance

    def test_pixel_variance_nonblank(self):
        import numpy as np
        from PIL import Image

        # Create image with variation
        img = Image.new("L", (100, 100), 128)
        pixels = list(img.getdata())
        for i in range(len(pixels)):
            if i % 2 == 0:
                pixels[i] = 200
        img.putdata(pixels)

        img_array = np.array(img)
        mean = img_array.mean()
        variance = ((img_array - mean) ** 2).mean()

        assert variance > 0  # Non-uniform has variance

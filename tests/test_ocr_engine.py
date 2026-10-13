"""Tests for ocr_engine module."""

from pathlib import Path

from pdfmd.ocr_engine import (
    get_confidence,
    initialize_tesseract,
    ocr_image,
    ocr_with_confidence,
)
from pdfmd.page_renderer import render_page
from pdfmd.pdf_reader import open_pdf

FIXTURE_DIR = Path(__file__).parent / "fixtures"
REAL_PDF = FIXTURE_DIR / "expediente Miranda ..pdf"


def _normalize_ws(text: str) -> str:
    """Collapse all whitespace for text comparison."""
    return " ".join(text.split())


class TestInitializeTesseract:
    """Tests for initialize_tesseract()."""

    def test_initializes_without_error(self):
        """Tesseract should initialize with default settings."""
        # Should not raise
        initialize_tesseract()


class TestOcrImage:
    """Tests for ocr_image()."""

    def test_returns_string(self):
        """ocr_image should return a string (may be empty for blank pages)."""
        doc = open_pdf(str(REAL_PDF))
        img = render_page(doc[0], dpi=300)
        result = ocr_image(img)
        assert isinstance(result, str)
        doc.close()

    def test_ocr_first_page_has_content(self):
        """First page of scanned PDF should produce some OCR text."""
        doc = open_pdf(str(REAL_PDF))
        img = render_page(doc[0], dpi=300)
        text = ocr_image(img)
        # Scanned legal doc should have at least some characters
        assert len(text.strip()) > 0
        doc.close()


class TestGetConfidence:
    """Tests for get_confidence()."""

    def test_returns_float_between_0_and_1(self):
        """Confidence should be a float between 0.0 and 1.0."""
        doc = open_pdf(str(REAL_PDF))
        img = render_page(doc[0], dpi=300)
        conf = get_confidence(img)
        assert isinstance(conf, float)
        assert 0.0 <= conf <= 1.0
        doc.close()


class TestOcrWithConfidence:
    """Tests for ocr_with_confidence() — single-pass OCR (US-1, Feature 003)."""

    def test_returns_text_and_confidence_tuple(self):
        """ocr_with_confidence should return a (str, float) tuple."""
        doc = open_pdf(str(REAL_PDF))
        img = render_page(doc[0], dpi=300)
        result = ocr_with_confidence(img)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], str)
        assert isinstance(result[1], float)
        doc.close()

    def test_text_matches_ocr_image(self):
        """Single-pass text should match ocr_image() output (whitespace-normalized)."""
        doc = open_pdf(str(REAL_PDF))
        img = render_page(doc[0], dpi=300)
        single_text, _ = ocr_with_confidence(img)
        dual_text = ocr_image(img)
        assert _normalize_ws(single_text) == _normalize_ws(dual_text)
        doc.close()

    def test_confidence_matches_get_confidence(self):
        """Single-pass confidence should match get_confidence() within 1%."""
        doc = open_pdf(str(REAL_PDF))
        img = render_page(doc[0], dpi=300)
        _, single_conf = ocr_with_confidence(img)
        dual_conf = get_confidence(img)
        assert abs(single_conf - dual_conf) <= 0.01
        doc.close()

    def test_single_tesseract_call(self, monkeypatch):
        """ocr_with_confidence must issue exactly ONE Tesseract call."""
        import pytesseract

        doc = open_pdf(str(REAL_PDF))
        img = render_page(doc[0], dpi=300)
        doc.close()

        calls = []
        original = pytesseract.image_to_data

        def counting_data(*args, **kwargs):
            calls.append(1)
            return original(*args, **kwargs)

        def fail_string(*args, **kwargs):
            raise AssertionError("image_to_string must not be called in single-pass OCR")

        monkeypatch.setattr(pytesseract, "image_to_data", counting_data)
        monkeypatch.setattr(pytesseract, "image_to_string", fail_string)

        ocr_with_confidence(img)

        assert len(calls) == 1

    def test_blank_image_returns_empty_and_zero(self):
        """Blank image yields empty text and 0.0 confidence."""
        from PIL import Image

        img = Image.new("RGB", (200, 200), (255, 255, 255))
        text, conf = ocr_with_confidence(img)
        assert text == ""
        assert conf == 0.0

    def test_first_page_has_content(self):
        """Single-pass OCR of the first scanned page should extract text."""
        doc = open_pdf(str(REAL_PDF))
        img = render_page(doc[0], dpi=300)
        text, conf = ocr_with_confidence(img)
        assert len(text.strip()) > 0
        assert conf > 0.0
        doc.close()

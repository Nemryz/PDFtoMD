
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
    return " ".join(text.split())


class TestInitializeTesseract:

    def test_initializes_without_error(self):
        # Should not raise
        initialize_tesseract()


class TestOcrImage:

    def test_returns_string(self):
        doc = open_pdf(str(REAL_PDF))
        img = render_page(doc[0], dpi=300)
        result = ocr_image(img)
        assert isinstance(result, str)
        doc.close()

    def test_ocr_first_page_has_content(self):
        doc = open_pdf(str(REAL_PDF))
        img = render_page(doc[0], dpi=300)
        text = ocr_image(img)
        # Scanned legal doc should have at least some characters
        assert len(text.strip()) > 0
        doc.close()


class TestGetConfidence:

    def test_returns_float_between_0_and_1(self):
        doc = open_pdf(str(REAL_PDF))
        img = render_page(doc[0], dpi=300)
        conf = get_confidence(img)
        assert isinstance(conf, float)
        assert 0.0 <= conf <= 1.0
        doc.close()


class TestOcrWithConfidence:

    def test_returns_text_and_confidence_tuple(self):
        doc = open_pdf(str(REAL_PDF))
        img = render_page(doc[0], dpi=300)
        result = ocr_with_confidence(img)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], str)
        assert isinstance(result[1], float)
        doc.close()

    def test_text_matches_ocr_image(self):
        doc = open_pdf(str(REAL_PDF))
        img = render_page(doc[0], dpi=300)
        single_text, _ = ocr_with_confidence(img)
        dual_text = ocr_image(img)
        assert _normalize_ws(single_text) == _normalize_ws(dual_text)
        doc.close()

    def test_confidence_matches_get_confidence(self):
        doc = open_pdf(str(REAL_PDF))
        img = render_page(doc[0], dpi=300)
        _, single_conf = ocr_with_confidence(img)
        dual_conf = get_confidence(img)
        assert abs(single_conf - dual_conf) <= 0.01
        doc.close()

    def test_single_tesseract_call(self, monkeypatch):
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
        from PIL import Image

        img = Image.new("RGB", (200, 200), (255, 255, 255))
        text, conf = ocr_with_confidence(img)
        assert text == ""
        assert conf == 0.0

    def test_first_page_has_content(self):
        doc = open_pdf(str(REAL_PDF))
        img = render_page(doc[0], dpi=300)
        text, conf = ocr_with_confidence(img)
        assert len(text.strip()) > 0
        assert conf > 0.0
        doc.close()

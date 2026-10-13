"""Tests for page_renderer module."""

from pathlib import Path

from pdfmd.page_renderer import render_page
from pdfmd.pdf_reader import open_pdf

FIXTURE_DIR = Path(__file__).parent / "fixtures"
REAL_PDF = FIXTURE_DIR / "expediente Miranda ..pdf"


class TestRenderPage:
    """Tests for render_page()."""

    def test_returns_pil_image(self):
        """render_page should return a PIL Image."""
        from PIL import Image

        doc = open_pdf(str(REAL_PDF))
        page = doc[0]
        img = render_page(page, dpi=300)
        assert isinstance(img, Image.Image)
        doc.close()

    def test_300_dpi_dimensions(self):
        """At 300 DPI, a letter-size page should be ~2481x3508 pixels."""
        doc = open_pdf(str(REAL_PDF))
        page = doc[0]
        img = render_page(page, dpi=300)
        # Real PDF may vary, but should be roughly 2400-2600 x 3400-3800
        assert 2400 <= img.width <= 2600
        assert 3400 <= img.height <= 3800
        doc.close()

    def test_different_dpi(self):
        """Different DPI values should produce different sized images."""
        doc = open_pdf(str(REAL_PDF))
        page = doc[0]
        img_150 = render_page(page, dpi=150)
        img_300 = render_page(page, dpi=300)
        # 300 DPI should be roughly 2x 150 DPI
        assert img_300.width > img_150.width
        assert img_300.height > img_150.height
        doc.close()

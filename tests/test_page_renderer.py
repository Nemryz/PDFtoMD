
from pathlib import Path

from pdfmd.page_renderer import render_page
from pdfmd.pdf_reader import open_pdf

FIXTURE_DIR = Path(__file__).parent / "fixtures"
REAL_PDF = FIXTURE_DIR / "expediente Miranda ..pdf"


class TestRenderPage:

    def test_returns_pil_image(self):
        from PIL import Image

        doc = open_pdf(str(REAL_PDF))
        page = doc[0]
        img = render_page(page, dpi=300)
        assert isinstance(img, Image.Image)
        doc.close()

    def test_300_dpi_dimensions(self):
        doc = open_pdf(str(REAL_PDF))
        page = doc[0]
        img = render_page(page, dpi=300)
        # A real PDF may vary, but should land near 2400 by 3400 pixels.
        assert 2400 <= img.width <= 2600
        assert 3400 <= img.height <= 3800
        doc.close()

    def test_different_dpi(self):
        doc = open_pdf(str(REAL_PDF))
        page = doc[0]
        img_150 = render_page(page, dpi=150)
        img_300 = render_page(page, dpi=300)
        # 300 DPI should be roughly 2x 150 DPI
        assert img_300.width > img_150.width
        assert img_300.height > img_150.height
        doc.close()

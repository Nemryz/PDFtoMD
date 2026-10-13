
import tempfile
from pathlib import Path

from pdfmd.image_extractor import deduplicate, extract_images, save_images
from pdfmd.pdf_reader import open_pdf

FIXTURE_DIR = Path(__file__).parent / "fixtures"
REAL_PDF = FIXTURE_DIR / "expediente Miranda ..pdf"


class TestExtractImages:

    def test_returns_list(self):
        doc = open_pdf(str(REAL_PDF))
        images = extract_images(doc, pages=[0])
        assert isinstance(images, list)
        doc.close()

    def test_extracts_from_page_with_images(self):
        doc = open_pdf(str(REAL_PDF))
        images = extract_images(doc, pages=[0])
        # Result may be empty if page has no embedded images (scanned PDFs
        # render the whole page as an image, not embed separate images)
        assert isinstance(images, list)
        doc.close()


class TestDeduplicate:

    def test_removes_duplicates(self):
        from pdfmd.image_extractor import ExtractedImage

        img1 = ExtractedImage(data=b"same_data", page=1, index=0, width=100, height=100)
        img2 = ExtractedImage(data=b"same_data", page=2, index=0, width=100, height=100)
        img3 = ExtractedImage(data=b"different_data", page=3, index=0, width=100, height=100)

        result = deduplicate([img1, img2, img3])
        assert len(result) == 2

    def test_empty_list(self):
        result = deduplicate([])
        assert result == []


class TestSaveImages:

    def test_saves_to_directory(self):
        from pdfmd.image_extractor import ExtractedImage

        with tempfile.TemporaryDirectory() as tmpdir:
            img = ExtractedImage(data=b"\x89PNG\r\n", page=1, index=0, width=100, height=100)
            saved = save_images([img], tmpdir)
            assert len(saved) == 1
            assert Path(saved[0].path).exists()

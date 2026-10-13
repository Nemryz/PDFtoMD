
from pathlib import Path

import pytest

from pdfmd.pdf_reader import extract_page_text, get_page_count, has_text_layer, open_pdf

FIXTURE_DIR = Path(__file__).parent / "fixtures"
REAL_PDF = FIXTURE_DIR / "expediente Miranda ..pdf"


class TestOpenPDF:

    def test_opens_real_pdf(self):
        doc = open_pdf(str(REAL_PDF))
        assert doc is not None
        doc.close()

    def test_raises_on_missing_file(self):
        with pytest.raises(FileNotFoundError):
            open_pdf("C:\\nonexistent\\file.pdf")


class TestGetPageCount:

    def test_real_pdf_page_count(self):
        doc = open_pdf(str(REAL_PDF))
        count = get_page_count(doc)
        assert count == 140
        doc.close()


class TestHasTextLayer:

    def test_scanned_pdf_has_no_text_layer(self):
        doc = open_pdf(str(REAL_PDF))
        page = doc[0]
        assert has_text_layer(page) is False
        doc.close()


class TestExtractPageText:

    def test_scanned_pdf_returns_empty_or_short(self):
        doc = open_pdf(str(REAL_PDF))
        page = doc[0]
        text = extract_page_text(page)
        # Scanned PDF has no embedded text
        assert len(text.strip()) < 10
        doc.close()

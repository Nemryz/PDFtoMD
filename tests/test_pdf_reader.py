"""Tests for pdf_reader module."""

from pathlib import Path

import pytest

from pdfmd.pdf_reader import extract_page_text, get_page_count, has_text_layer, open_pdf

FIXTURE_DIR = Path(__file__).parent / "fixtures"
REAL_PDF = FIXTURE_DIR / "expediente Miranda ..pdf"


class TestOpenPDF:
    """Tests for open_pdf()."""

    def test_opens_real_pdf(self):
        """Real scanned PDF should open without error."""
        doc = open_pdf(str(REAL_PDF))
        assert doc is not None
        doc.close()

    def test_raises_on_missing_file(self):
        """Non-existent file should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            open_pdf("C:\\nonexistent\\file.pdf")


class TestGetPageCount:
    """Tests for get_page_count()."""

    def test_real_pdf_page_count(self):
        """Real PDF should report correct page count."""
        doc = open_pdf(str(REAL_PDF))
        count = get_page_count(doc)
        assert count == 140
        doc.close()


class TestHasTextLayer:
    """Tests for has_text_layer()."""

    def test_scanned_pdf_has_no_text_layer(self):
        """Scanned PDF pages should have no text layer."""
        doc = open_pdf(str(REAL_PDF))
        page = doc[0]
        assert has_text_layer(page) is False
        doc.close()


class TestExtractPageText:
    """Tests for extract_page_text()."""

    def test_scanned_pdf_returns_empty_or_short(self):
        """Scanned PDF with no text layer should return empty or very short text."""
        doc = open_pdf(str(REAL_PDF))
        page = doc[0]
        text = extract_page_text(page)
        # Scanned PDF has no embedded text
        assert len(text.strip()) < 10
        doc.close()

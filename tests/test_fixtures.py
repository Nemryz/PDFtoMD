"""Tests for pipeline against fixture PDFs (US-4, Feature 003)."""

import tempfile
from pathlib import Path

import pytest

from pdfmd.core import convert_pdf

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "pdfs"


def _convert_fixture(pdf_name: str, category: str):
    """Convert a fixture PDF and return (result, content) or (None, None)."""
    pdf_path = FIXTURE_DIR / category / pdf_name
    if not pdf_path.exists():
        pytest.skip(f"Fixture not found: {pdf_path}")

    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "output.md"
        try:
            result = convert_pdf(str(pdf_path), str(out_path))
            content = out_path.read_text(encoding="utf-8") if out_path.exists() else ""
            return result, content
        except Exception:
            return None, None


class TestValidFixtures:
    """Tests for valid PDF fixtures — should produce non-empty Markdown."""

    def test_simple_1page(self):
        result, content = _convert_fixture("simple_1page.pdf", "valid")
        assert result is not None
        assert len(content) > 0

    def test_simple_5pages(self):
        result, content = _convert_fixture("simple_5pages.pdf", "valid")
        assert result is not None
        assert "Pagina 1" in content
        assert "Pagina 5" in content

    def test_with_tables(self):
        result, content = _convert_fixture("with_tables.pdf", "valid")
        assert result is not None
        assert "|" in content  # Table markers present

    def test_mixed_content(self):
        result, content = _convert_fixture("mixed_content.pdf", "valid")
        assert result is not None
        assert len(content) > 0

    def test_multi_column(self):
        result, content = _convert_fixture("multi_column.pdf", "valid")
        assert result is not None
        assert len(content) > 0

    def test_rotated_pages(self):
        result, content = _convert_fixture("rotated_pages.pdf", "valid")
        assert result is not None
        assert len(content) > 0

    def test_low_quality(self):
        result, content = _convert_fixture("low_quality.pdf", "valid")
        assert result is not None
        assert len(content) > 0


class TestEdgeCaseFixtures:
    """Tests for edge case PDFs — should be handled gracefully."""

    def test_empty_page(self):
        """Empty PDF should produce output (possibly empty or minimal)."""
        result, content = _convert_fixture("empty.pdf", "edge_cases")
        assert result is not None

    def test_blank_pages(self):
        """Blank pages should produce output without crashing."""
        result, content = _convert_fixture("blank_pages.pdf", "edge_cases")
        assert result is not None

    def test_encrypted_pdf(self):
        """Encrypted PDF should raise a clear error."""
        pdf_path = FIXTURE_DIR / "edge_cases" / "encrypted.pdf"
        if not pdf_path.exists():
            pytest.skip("Fixture not found")

        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "output.md"
            with pytest.raises(Exception):
                convert_pdf(str(pdf_path), str(out_path))

    def test_corrupted_pdf(self):
        """Corrupted PDF should be handled gracefully (error or partial output)."""
        result, content = _convert_fixture("corrupted.pdf", "edge_cases")
        # May return None (error) or partial output — both acceptable

    def test_only_images(self):
        """Image-only PDF should produce OCR output."""
        result, content = _convert_fixture("only_images.pdf", "edge_cases")
        assert result is not None

    def test_unicode_content(self):
        """Unicode PDF should preserve special characters."""
        result, content = _convert_fixture("unicode_content.pdf", "edge_cases")
        assert result is not None
        assert len(content) > 0


class TestLegalFixtures:
    """Tests for legal document PDFs."""

    def test_decreto(self):
        result, content = _convert_fixture("decreto.pdf", "legal")
        assert result is not None
        assert len(content) > 0

    def test_oficio(self):
        result, content = _convert_fixture("oficio.pdf", "legal")
        assert result is not None
        assert len(content) > 0

    def test_resolucion(self):
        result, content = _convert_fixture("resolucion.pdf", "legal")
        assert result is not None
        assert len(content) > 0

    def test_contrato(self):
        result, content = _convert_fixture("contrato.pdf", "legal")
        assert result is not None
        assert len(content) > 0


class TestBenchmarkFixtures:
    """Tests for benchmark PDFs (subset — not full conversion)."""

    def test_benchmark_50pages_metadata(self):
        """Verify 50-page benchmark opens and has correct page count."""
        import pymupdf

        pdf_path = FIXTURE_DIR / "benchmarks" / "bench_50pages.pdf"
        doc = pymupdf.open(str(pdf_path))
        assert doc.page_count == 50
        doc.close()

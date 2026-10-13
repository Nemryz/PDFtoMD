"""Tests for core pipeline module."""

import tempfile
from pathlib import Path

import pytest

from pdfmd.core import convert_pdf

FIXTURE_DIR = Path(__file__).parent / "fixtures"
REAL_PDF = FIXTURE_DIR / "expediente Miranda ..pdf"


class TestConvertPDF:
    """Tests for convert_pdf() — end-to-end pipeline."""

    @pytest.mark.slow
    def test_produces_markdown_file(self):
        """Full conversion should produce a .md file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "output.md"
            result = convert_pdf(str(REAL_PDF), str(output), pages=[0, 1])

            assert output.exists()
            assert output.stat().st_size > 0
            assert result.pages_processed == 2

    @pytest.mark.slow
    def test_markdown_has_content(self):
        """Generated Markdown should have non-empty content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "output.md"
            convert_pdf(str(REAL_PDF), str(output), pages=[0, 1])

            content = output.read_text(encoding="utf-8", errors="replace")
            assert len(content) > 50

    def test_raises_on_missing_file(self):
        """Should raise FileNotFoundError for non-existent input."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "output.md"
            with pytest.raises(FileNotFoundError):
                convert_pdf("C:\\nonexistent\\file.pdf", str(output))

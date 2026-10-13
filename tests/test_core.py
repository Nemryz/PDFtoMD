"""Integration tests for core pipeline — single-pass OCR (US-1, Feature 003)."""

import json
import tempfile
from pathlib import Path

import pytest

from pdfmd.core import convert_pdf

FIXTURE_DIR = Path(__file__).parent / "fixtures"
REAL_PDF = FIXTURE_DIR / "expediente Miranda ..pdf"


class TestSinglePassPipeline:
    """Pipeline must use single-pass OCR — one Tesseract call per page."""

    @pytest.mark.slow
    def test_convert_produces_output_and_metadata(self):
        """Conversion on real pages produces Markdown + metadata with confidence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "output.md"
            result = convert_pdf(str(REAL_PDF), str(output), pages=[0, 1, 2])

            assert output.exists()
            content = output.read_text(encoding="utf-8", errors="replace")
            assert len(content) > 50
            assert result.pages_processed == 3

            # Confidence values present in page results
            for pr in result.pages:
                assert 0.0 <= pr.confidence <= 1.0

            # metadata.json contains confidence information
            metadata_path = Path(result.metadata_path)
            assert metadata_path.exists()
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            assert "avg_confidence" in metadata
            assert metadata["ocr_pages"] >= 1

    @pytest.mark.slow
    def test_single_tesseract_call_per_page(self, monkeypatch):
        """Each OCR'd page triggers exactly one image_to_data call and
        image_to_string is never called (no double-OCR in the pipeline)."""
        import pytesseract

        calls = []
        original = pytesseract.image_to_data

        def counting_data(*args, **kwargs):
            calls.append(1)
            return original(*args, **kwargs)

        def fail_string(*args, **kwargs):
            raise AssertionError("image_to_string called — double-OCR still present in pipeline")

        monkeypatch.setattr(pytesseract, "image_to_data", counting_data)
        monkeypatch.setattr(pytesseract, "image_to_string", fail_string)

        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "output.md"
            result = convert_pdf(str(REAL_PDF), str(output), pages=[0, 1, 2])

        # No classify -> no retry -> exactly one call per OCR'd page
        assert result.pages_with_ocr >= 1
        assert len(calls) == result.pages_with_ocr

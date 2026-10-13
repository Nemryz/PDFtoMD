"""Tests for metadata_builder module."""

from pdfmd.metadata_builder import build_metadata
from pdfmd.quality_metrics import measure_text_quality


class TestBuildMetadata:
    """Tests for build_metadata()."""

    def test_returns_dict(self):
        result = build_metadata(
            source="test.pdf",
            pages_processed=10,
            total_pages=10,
            pages_with_ocr=8,
            avg_confidence=0.85,
            elapsed_seconds=5.0,
        )
        assert isinstance(result, dict)

    def test_has_required_fields(self):
        result = build_metadata(
            source="test.pdf",
            pages_processed=10,
            total_pages=10,
            pages_with_ocr=8,
            avg_confidence=0.85,
            elapsed_seconds=5.0,
        )
        assert "source" in result
        assert "total_pages" in result
        assert "pages_processed" in result
        assert "ocr_pages" in result
        assert "avg_confidence" in result
        assert "processing_time_seconds" in result
        assert "tool_version" in result

    def test_values_match_input(self):
        result = build_metadata(
            source="test.pdf",
            pages_processed=10,
            total_pages=50,
            pages_with_ocr=8,
            avg_confidence=0.85,
            elapsed_seconds=5.0,
        )
        assert result["source"] == "test.pdf"
        assert result["total_pages"] == 50
        assert result["pages_processed"] == 10
        assert result["ocr_pages"] == 8
        assert result["avg_confidence"] == 0.85

    def test_warnings_list(self):
        result = build_metadata(
            source="test.pdf",
            pages_processed=10,
            total_pages=10,
            pages_with_ocr=8,
            avg_confidence=0.85,
            elapsed_seconds=5.0,
            warnings=["Low confidence on page 3"],
        )
        assert "Low confidence on page 3" in result["warnings"]

    def test_quality_section_present(self):
        quality = measure_text_quality("# Title\n\nSome text.\n")
        result = build_metadata(
            source="test.pdf",
            pages_processed=1,
            total_pages=1,
            pages_with_ocr=1,
            avg_confidence=0.85,
            elapsed_seconds=1.0,
            quality=quality,
        )
        assert "quality" in result
        assert result["quality"]["words"] == 4
        assert result["quality"]["headers_detected"] == 1
        assert "score" in result["quality"]

    def test_quality_section_absent_when_none(self):
        result = build_metadata(
            source="test.pdf",
            pages_processed=1,
            total_pages=1,
            pages_with_ocr=1,
            avg_confidence=0.85,
            elapsed_seconds=1.0,
        )
        assert "quality" not in result

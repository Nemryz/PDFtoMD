"""Tests for enhanced metadata with classification support."""

from pdfmd.metadata_builder import build_metadata
from pdfmd.types import OCRParameters, PageClassification, PageClassificationResult


class TestBuildMetadata:
    """Test build_metadata function."""

    def test_basic_metadata(self):
        """Basic metadata without classification."""
        metadata = build_metadata(
            source="test.pdf",
            pages_processed=10,
            total_pages=10,
            pages_with_ocr=8,
            avg_confidence=0.75,
            elapsed_seconds=5.5,
        )

        assert metadata["source"] == "test.pdf"
        assert metadata["total_pages"] == 10
        assert metadata["ocr_pages"] == 8
        assert metadata["digital_pages"] == 2
        assert metadata["avg_confidence"] == 0.75
        assert metadata["processing_time_seconds"] == 5.5
        assert "classification_summary" not in metadata

    def test_metadata_with_warnings(self):
        """Metadata includes warnings."""
        warnings = ["Low confidence on page 5", "Page 10 blank"]
        metadata = build_metadata(
            source="test.pdf",
            pages_processed=10,
            total_pages=10,
            pages_with_ocr=8,
            avg_confidence=0.75,
            elapsed_seconds=5.5,
            warnings=warnings,
        )

        assert metadata["warnings"] == warnings

    def test_metadata_with_classifications(self):
        """Metadata includes classification data."""
        classifications = [
            PageClassificationResult(
                page_number=1,
                classification=PageClassification.TYPED_CLEAN,
                confidence=0.85,
                needs_ocr=True,
                needs_strong_ocr=False,
            ),
            PageClassificationResult(
                page_number=2,
                classification=PageClassification.BLANK,
                confidence=0.95,
                needs_ocr=False,
                needs_strong_ocr=False,
            ),
        ]

        metadata = build_metadata(
            source="test.pdf",
            pages_processed=2,
            total_pages=2,
            pages_with_ocr=1,
            avg_confidence=0.85,
            elapsed_seconds=1.0,
            classifications=classifications,
        )

        assert "classification_summary" in metadata
        assert "page_classifications" in metadata
        assert len(metadata["page_classifications"]) == 2

    def test_classification_summary_counts(self):
        """Classification summary has correct counts."""
        classifications = [
            PageClassificationResult(
                page_number=1,
                classification=PageClassification.TYPED_CLEAN,
                confidence=0.85,
                needs_ocr=True,
                needs_strong_ocr=False,
            ),
            PageClassificationResult(
                page_number=2,
                classification=PageClassification.TYPED_CLEAN,
                confidence=0.80,
                needs_ocr=True,
                needs_strong_ocr=False,
            ),
            PageClassificationResult(
                page_number=3,
                classification=PageClassification.BLANK,
                confidence=0.95,
                needs_ocr=False,
                needs_strong_ocr=False,
            ),
        ]

        metadata = build_metadata(
            source="test.pdf",
            pages_processed=3,
            total_pages=3,
            pages_with_ocr=2,
            avg_confidence=0.82,
            elapsed_seconds=1.0,
            classifications=classifications,
        )

        summary = metadata["classification_summary"]
        assert summary["total_pages"] == 3
        assert summary["counts"]["typed_clean"] == 2
        assert summary["counts"]["blank"] == 1
        assert summary["blank_pages"] == 1

    def test_page_classification_entry(self):
        """Page classification entry has correct fields."""
        classifications = [
            PageClassificationResult(
                page_number=1,
                classification=PageClassification.TYPED_ANNOTATED,
                confidence=0.70,
                needs_ocr=True,
                needs_strong_ocr=False,
                ocr_params=OCRParameters(
                    dpi=400,
                    psm=6,
                    lang="eng+spa",
                    preprocess=["contrast", "sharpness"],
                ),
            ),
        ]

        metadata = build_metadata(
            source="test.pdf",
            pages_processed=1,
            total_pages=1,
            pages_with_ocr=1,
            avg_confidence=0.70,
            elapsed_seconds=0.5,
            classifications=classifications,
        )

        page_entry = metadata["page_classifications"][0]
        assert page_entry["page"] == 1
        assert page_entry["classification"] == "typed_annotated"
        assert page_entry["confidence"] == 0.70
        assert page_entry["needs_ocr"] is True
        assert "ocr_params" in page_entry
        assert page_entry["ocr_params"]["dpi"] == 400

    def test_low_confidence_flagged_for_review(self):
        """Low confidence classifications are flagged for review."""
        classifications = [
            PageClassificationResult(
                page_number=1,
                classification=PageClassification.TYPED_CLEAN,
                confidence=0.3,  # Low confidence
                needs_ocr=True,
                needs_strong_ocr=False,
            ),
        ]

        metadata = build_metadata(
            source="test.pdf",
            pages_processed=1,
            total_pages=1,
            pages_with_ocr=1,
            avg_confidence=0.3,
            elapsed_seconds=0.5,
            classifications=classifications,
        )

        summary = metadata["classification_summary"]
        assert summary["needs_review"] == 1

    def test_metadata_json_serializable(self):
        """Metadata is JSON serializable."""
        import json

        classifications = [
            PageClassificationResult(
                page_number=1,
                classification=PageClassification.TYPED_CLEAN,
                confidence=0.85,
                needs_ocr=True,
                needs_strong_ocr=False,
            ),
        ]

        metadata = build_metadata(
            source="test.pdf",
            pages_processed=1,
            total_pages=1,
            pages_with_ocr=1,
            avg_confidence=0.85,
            elapsed_seconds=0.5,
            classifications=classifications,
        )

        # Should not raise
        json_str = json.dumps(metadata)
        assert len(json_str) > 0

"""Metadata builder — generate metadata.json for converted documents."""

from __future__ import annotations

from pdfmd import __version__
from pdfmd.quality_metrics import QualityReport, quality_score
from pdfmd.types import PageClassificationResult


def build_metadata(
    source: str,
    pages_processed: int,
    total_pages: int,
    pages_with_ocr: int,
    avg_confidence: float,
    elapsed_seconds: float,
    warnings: list[str] | None = None,
    classifications: list[PageClassificationResult] | None = None,
    quality: QualityReport | None = None,
) -> dict:
    """Build metadata dictionary for a converted document.

    Args:
        source: Original PDF filename.
        pages_processed: Number of pages processed.
        total_pages: Total pages in the PDF.
        pages_with_ocr: Pages that used OCR.
        avg_confidence: Average OCR confidence (0.0-1.0).
        elapsed_seconds: Processing time.
        warnings: Optional list of warning messages.
        classifications: Optional list of page classification results.
        quality: Optional quality report from text analysis.

    Returns:
        Dictionary suitable for JSON serialization.
    """
    metadata = {
        "source": source,
        "total_pages": total_pages,
        "pages_processed": pages_processed,
        "ocr_pages": pages_with_ocr,
        "digital_pages": pages_processed - pages_with_ocr,
        "avg_confidence": round(avg_confidence, 3),
        "processing_time_seconds": round(elapsed_seconds, 2),
        "tool_version": __version__,
        "warnings": warnings or [],
    }

    # Add classification data if provided
    if classifications:
        metadata["classification_summary"] = _build_classification_summary(classifications)
        metadata["page_classifications"] = [_build_page_classification(c) for c in classifications]

    # Add quality metrics if provided
    if quality is not None:
        metadata["quality"] = quality.to_dict()
        metadata["quality"]["score"] = quality_score(quality)

    return metadata


def _build_classification_summary(
    classifications: list[PageClassificationResult],
) -> dict:
    """Build summary of classification results.

    Args:
        classifications: List of page classification results.

    Returns:
        Summary dictionary with counts per type.
    """
    counts: dict[str, int] = {}
    blank_count = 0
    needs_review_count = 0

    for c in classifications:
        label = c.classification.value
        counts[label] = counts.get(label, 0) + 1

        if c.classification.value == "blank":
            blank_count += 1
        if c.needs_ocr and c.confidence < 0.5:
            needs_review_count += 1

    return {
        "total_pages": len(classifications),
        "counts": counts,
        "blank_pages": blank_count,
        "needs_review": needs_review_count,
    }


def _build_page_classification(
    result: PageClassificationResult,
) -> dict:
    """Build single page classification entry.

    Args:
        result: Page classification result.

    Returns:
        Dictionary with page classification data.
    """
    entry = {
        "page": result.page_number,
        "classification": result.classification.value,
        "confidence": round(result.confidence, 3),
        "needs_ocr": result.needs_ocr,
        "needs_review": result.needs_strong_ocr,
    }

    if result.ocr_params:
        entry["ocr_params"] = {
            "dpi": result.ocr_params.dpi,
            "psm": result.ocr_params.psm,
            "skip_ocr": result.ocr_params.skip_ocr,
            "preprocess": result.ocr_params.preprocess,
        }

    return entry

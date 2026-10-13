"""Adaptive OCR router that selects optimal parameters based on page classification.

This module maps page classifications to OCR parameters, enabling different
processing strategies for different page types.
"""

from __future__ import annotations

import logging

from pdfmd.types import (
    OCRParameters,
    PageClassification,
    PageClassificationResult,
)

logger = logging.getLogger(__name__)

# Routing table: classification -> OCR parameters
ROUTING_TABLE: dict[PageClassification, OCRParameters] = {
    PageClassification.BLANK: OCRParameters(
        dpi=300,
        psm=6,
        lang="eng+spa",
        preprocess=[],
        skip_ocr=True,
        needs_review=False,
    ),
    PageClassification.TYPED_CLEAN: OCRParameters(
        dpi=300,
        psm=6,
        lang="eng+spa",
        preprocess=[],
        skip_ocr=False,
        needs_review=False,
    ),
    PageClassification.TYPED_SIGNED: OCRParameters(
        dpi=300,
        psm=6,
        lang="eng+spa",
        preprocess=["sharpness"],
        skip_ocr=False,
        needs_review=False,
    ),
    PageClassification.TYPED_ANNOTATED: OCRParameters(
        dpi=400,
        psm=6,
        lang="eng+spa",
        preprocess=["contrast", "sharpness"],
        enhance_contrast=1.5,
        enhance_sharpness=1.5,
        skip_ocr=False,
        needs_review=False,
    ),
    PageClassification.HANDWRITTEN: OCRParameters(
        dpi=600,
        psm=11,
        lang="eng+spa",
        preprocess=["contrast", "sharpness", "denoise"],
        enhance_contrast=2.0,
        enhance_sharpness=2.0,
        skip_ocr=False,
        needs_review=True,  # Flag for manual review
    ),
    PageClassification.IMAGE_ONLY: OCRParameters(
        dpi=300,
        psm=6,
        lang="eng+spa",
        preprocess=[],
        skip_ocr=False,
        needs_review=True,  # Image may contain text we can't detect
    ),
    PageClassification.UNKNOWN: OCRParameters(
        dpi=300,
        psm=6,
        lang="eng+spa",
        preprocess=["sharpness"],
        skip_ocr=False,
        needs_review=True,  # Unknown type needs review
    ),
}


class AdaptiveOCRRouter:
    """Selects OCR parameters based on page classification."""

    def __init__(self, custom_routing: dict[PageClassification, OCRParameters] | None = None):
        """Initialize router with optional custom routing table.

        Args:
            custom_routing: Custom routing table to override defaults.
        """
        self._routing = ROUTING_TABLE.copy()
        if custom_routing:
            self._routing.update(custom_routing)

    def get_parameters(self, classification: PageClassification) -> OCRParameters:
        """Get OCR parameters for a given classification.

        Args:
            classification: Page classification.

        Returns:
            OCR parameters for this classification type.
        """
        params = self._routing.get(classification)
        if params is None:
            logger.warning(f"No routing for {classification}, using UNKNOWN defaults")
            params = self._routing[PageClassification.UNKNOWN]
        return params

    def get_parameters_for_result(self, result: PageClassificationResult) -> OCRParameters:
        """Get OCR parameters for a classification result.

        Args:
            result: Page classification result.

        Returns:
            OCR parameters with needs_review set based on confidence.
        """
        params = self.get_parameters(result.classification)

        # Create a copy to avoid modifying the routing table
        params = OCRParameters(
            dpi=params.dpi,
            psm=params.psm,
            lang=params.lang,
            preprocess=params.preprocess.copy(),
            enhance_contrast=params.enhance_contrast,
            enhance_sharpness=params.enhance_sharpness,
            skip_ocr=params.skip_ocr,
            needs_review=params.needs_review,
        )

        # Flag low-confidence classifications for review
        if result.confidence < 0.5:
            params.needs_review = True
            logger.debug(
                f"Page {result.page_number}: Low classification confidence "
                f"({result.confidence:.1%}), flagged for review"
            )

        return params

    def route_pages(
        self,
        classifications: list[PageClassificationResult],
    ) -> list[tuple[PageClassificationResult, OCRParameters]]:
        """Route multiple pages to their OCR parameters.

        Args:
            classifications: List of page classification results.

        Returns:
            List of (classification_result, ocr_params) tuples.
        """
        routed = []
        for result in classifications:
            params = self.get_parameters_for_result(result)
            routed.append((result, params))

        # Log summary
        skip_count = sum(1 for _, p in routed if p.skip_ocr)
        review_count = sum(1 for _, p in routed if p.needs_review)
        logger.info(f"Routed {len(routed)} pages: {skip_count} skipped, {review_count} need review")

        return routed

    def get_routing_summary(self) -> dict[str, dict]:
        """Get a summary of the routing table for display.

        Returns:
            Dictionary mapping classification names to their parameters.
        """
        summary = {}
        for classification, params in self._routing.items():
            summary[classification.value] = {
                "dpi": params.dpi,
                "psm": params.psm,
                "skip_ocr": params.skip_ocr,
                "needs_review": params.needs_review,
                "preprocess": params.preprocess,
            }
        return summary


def get_default_parameters() -> dict[PageClassification, OCRParameters]:
    """Get the default routing table.

    Returns:
        Default routing table.
    """
    return ROUTING_TABLE.copy()

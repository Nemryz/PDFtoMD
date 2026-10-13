# I pick the OCR settings per page type, so a blank page and a handwritten one differ.

from __future__ import annotations

import logging

from pdfmd.types import (
    OCRParameters,
    PageClassification,
    PageClassificationResult,
)

logger = logging.getLogger(__name__)

# This is how each page classification maps onto the parameters I hand to the OCR engine.
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
    # I turn a page classification into the parameters the engine will run with.

    def __init__(self, custom_routing: dict[PageClassification, OCRParameters] | None = None):
        # I take an optional override table, so callers can retune any page type they care about.
        self._routing = ROUTING_TABLE.copy()
        if custom_routing:
            self._routing.update(custom_routing)

    def get_parameters(self, classification: PageClassification) -> OCRParameters:
        # I look up whatever is registered for that classification, else fall back to UNKNOWN.
        params = self._routing.get(classification)
        if params is None:
            logger.warning(f"No routing for {classification}, using UNKNOWN defaults")
            params = self._routing[PageClassification.UNKNOWN]
        return params

    def get_parameters_for_result(self, result: PageClassificationResult) -> OCRParameters:
        # Same as above, except I also weigh how confident the classification came out.
        params = self.get_parameters(result.classification)

        # I copy before returning, otherwise I'd be editing the shared table in place.
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

        # Under half confidence I stop trusting the classification and flag the page for review.
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
        # I pair every page with its parameters, then summarise the batch.
        routed = []
        for result in classifications:
            params = self.get_parameters_for_result(result)
            routed.append((result, params))

        # One log line, cheaper than making the caller ask for the summary afterwards.
        skip_count = sum(1 for _, p in routed if p.skip_ocr)
        review_count = sum(1 for _, p in routed if p.needs_review)
        logger.info(f"Routed {len(routed)} pages: {skip_count} skipped, {review_count} need review")

        return routed

    def get_routing_summary(self) -> dict[str, dict]:
        # I reshape the table so a CLI can print it without knowing anything about the dataclass.
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
    # A copy, so the caller can poke at it without reaching my defaults.
    return ROUTING_TABLE.copy()

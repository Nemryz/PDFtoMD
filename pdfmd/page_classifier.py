"""Page classifier using ocrsieve for intelligent page type detection.

This module classifies PDF pages into categories (blank, typed, handwritten, etc.)
to enable adaptive OCR parameter selection.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING

from pdfmd.types import PageClassification, PageClassificationResult

if TYPE_CHECKING:
    import pymupdf

logger = logging.getLogger(__name__)


class PageClassifier:
    """Classifies PDF pages by content type using ocrsieve with heuristic fallback."""

    def __init__(self) -> None:
        self._ocrsieve_available = False
        self._classifier = None
        self._doc_cache_id: int | None = None
        self._doc_cache: dict[int, PageClassificationResult] = {}
        self._init_ocrsieve()

    def _init_ocrsieve(self) -> None:
        """Initialize ocrsieve classifier if available."""
        try:
            from ocrsieve import PageClassifier as OcrsieveClassifier

            self._classifier = OcrsieveClassifier(use_model=True)
            self._ocrsieve_available = True
            logger.info("ocrsieve classifier loaded successfully")
        except ImportError:
            logger.warning("ocrsieve not available, using heuristic fallback")
        except Exception as e:
            logger.warning(f"Failed to load ocrsieve: {e}, using heuristic fallback")

    def classify_page(
        self,
        doc: pymupdf.Document,
        page_index: int,
    ) -> PageClassificationResult:
        """Classify a single page by its content.

        Args:
            doc: PyMuPDF document.
            page_index: 0-indexed page number.

        Returns:
            Classification result with confidence and OCR needs.
        """
        page_number = page_index + 1
        start_time = time.time()

        if self._ocrsieve_available and self._classifier is not None:
            result = self._classify_with_ocrsieve(doc, page_index, page_number)
        else:
            result = self._classify_with_heuristic(doc, page_index, page_number)

        elapsed_ms = (time.time() - start_time) * 1000
        logger.debug(
            f"Page {page_number}: {result.classification.value} "
            f"({result.confidence:.1%}) in {elapsed_ms:.0f}ms"
        )

        return result

    def classify_document(self, pdf_path: str | Path) -> list[PageClassificationResult]:
        """Classify all pages in a document.

        Args:
            pdf_path: Path to the PDF file.

        Returns:
            List of classification results, one per page.
        """
        import pymupdf

        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        doc = pymupdf.open(str(pdf_path))
        results = []

        for i in range(len(doc)):
            result = self.classify_page(doc, i)
            results.append(result)

        doc.close()
        return results

    def _classify_with_ocrsieve(
        self,
        doc: pymupdf.Document,
        page_index: int,
        page_number: int,
    ) -> PageClassificationResult:
        """Classify using ocrsieve's ONNX model.

        Caches the full-document classification result to avoid O(n²)
        re-classification when called per page.
        """
        doc_id = id(doc)

        # Classify entire document ONCE, cache by document identity
        if doc_id != self._doc_cache_id:
            try:
                result = self._classifier.classify(doc)
                self._doc_cache = {}
                for idx, page_result in enumerate(result.pages):
                    classification = PageClassification.from_ocrsieve(page_result.label)
                    confidence = (
                        page_result.confidence if page_result.confidence is not None else 0.5
                    )
                    needs_ocr = page_result.needs_ocr
                    needs_strong = getattr(page_result, "needs_strong_ocr", False)
                    self._doc_cache[idx] = PageClassificationResult(
                        page_number=idx + 1,
                        classification=classification,
                        confidence=confidence,
                        needs_ocr=needs_ocr,
                        needs_strong_ocr=needs_strong,
                    )
                self._doc_cache_id = doc_id
                logger.info(f"ocrsieve classified {len(result.pages)} pages in one pass")
            except Exception as e:
                logger.warning(f"ocrsieve classification failed: {e}, using heuristic fallback")
                self._doc_cache_id = doc_id
                self._doc_cache = {}

        # Return cached result for this page
        if page_index in self._doc_cache:
            return self._doc_cache[page_index]

        # Fallback if page not in cached results
        return PageClassificationResult(
            page_number=page_number,
            classification=PageClassification.UNKNOWN,
            confidence=0.0,
            needs_ocr=True,
            needs_strong_ocr=False,
        )

    def _classify_with_heuristic(
        self,
        doc: pymupdf.Document,
        page_index: int,
        page_number: int,
    ) -> PageClassificationResult:
        """Classify using pixel variance and text extraction heuristics."""
        page = doc[page_index]

        # Check for blank page using pixel variance
        if self._is_blank_page(page):
            return PageClassificationResult(
                page_number=page_number,
                classification=PageClassification.BLANK,
                confidence=0.95,
                needs_ocr=False,
                needs_strong_ocr=False,
            )

        # Check for text content
        text = page.get_text()
        text_length = len(text.strip())

        # Check for images
        images = page.get_images()
        image_count = len(images)

        # Calculate image coverage
        page_rect = page.rect
        page_area = page_rect.width * page_rect.height
        image_area = 0
        for img in images:
            xref = img[0]
            try:
                img_rect = page.get_image_rects(xref)
                if img_rect:
                    image_area += img_rect[0].width * img_rect[0].height
            except Exception:
                pass

        image_coverage = image_area / page_area if page_area > 0 else 0

        # Decision logic
        if text_length == 0 and image_count > 0:
            # No text, has images -> image only
            return PageClassificationResult(
                page_number=page_number,
                classification=PageClassification.IMAGE_ONLY,
                confidence=0.85,
                needs_ocr=True,
                needs_strong_ocr=False,
            )
        elif text_length == 0 and image_count == 0:
            # No text, no images -> blank (shouldn't reach here if _is_blank_page works)
            return PageClassificationResult(
                page_number=page_number,
                classification=PageClassification.BLANK,
                confidence=0.90,
                needs_ocr=False,
                needs_strong_ocr=False,
            )
        elif text_length > 100 and image_coverage < 0.1:
            # Lots of text, few images -> typed clean
            return PageClassificationResult(
                page_number=page_number,
                classification=PageClassification.TYPED_CLEAN,
                confidence=0.80,
                needs_ocr=True,
                needs_strong_ocr=False,
            )
        elif text_length > 0 and image_coverage > 0.3:
            # Some text, lots of images -> could be annotated or mixed
            return PageClassificationResult(
                page_number=page_number,
                classification=PageClassification.TYPED_ANNOTATED,
                confidence=0.70,
                needs_ocr=True,
                needs_strong_ocr=False,
            )
        else:
            # Default: typed with possible signatures
            return PageClassificationResult(
                page_number=page_number,
                classification=PageClassification.TYPED_CLEAN,
                confidence=0.60,
                needs_ocr=True,
                needs_strong_ocr=False,
            )

    def _is_blank_page(self, page: pymupdf.Page, threshold: float = 0.001) -> bool:
        """Detect blank page using pixel variance analysis.

        Args:
            page: PyMuPDF page.
            threshold: Variance threshold below which page is blank.

        Returns:
            True if page appears blank.
        """
        try:
            # Render page to pixmap for analysis
            mat = pymupdf.Matrix(0.5, 0.5)  # Low res for speed
            pix = page.get_pixmap(matrix=mat)

            # Get pixel data
            samples = pix.samples
            if not samples:
                return False

            # Calculate pixel variance
            total = len(samples)
            if total == 0:
                return False

            mean = sum(samples) / total
            variance = sum((x - mean) ** 2 for x in samples) / total

            return variance < threshold

        except Exception:
            # If we can't analyze, assume not blank
            return False

"""Type definitions for Feature 002: Smart Page Classification & Adaptive OCR."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class PageClassification(Enum):
    """Classification of PDF page content type."""

    BLANK = "blank"
    """No content detected (pixel variance below threshold)."""

    TYPED_CLEAN = "typed_clean"
    """Printed/typewritten text, no pen strokes."""

    TYPED_SIGNED = "typed_signed"
    """Printed text with signatures, stamps, or initials."""

    TYPED_ANNOTATED = "typed_annotated"
    """Printed text with handwritten annotations that carry information."""

    HANDWRITTEN = "handwritten"
    """Body text is handwritten."""

    IMAGE_ONLY = "image_only"
    """Diagrams, charts, photos — no text to extract."""

    UNKNOWN = "unknown"
    """Could not classify — fallback."""

    @classmethod
    def from_ocrsieve(cls, label: str) -> PageClassification:
        """Convert ocrsieve label to our enum."""
        mapping = {
            "blank": cls.BLANK,
            "typed_clean": cls.TYPED_CLEAN,
            "typed_signed": cls.TYPED_SIGNED,
            "typed_annotated": cls.TYPED_ANNOTATED,
            "handwritten": cls.HANDWRITTEN,
            "digital_text": cls.TYPED_CLEAN,  # digital text = clean typed
        }
        return mapping.get(label, cls.UNKNOWN)


@dataclass
class OCRParameters:
    """OCR configuration parameters for a page."""

    dpi: int = 300
    """DPI for rendering the page."""

    psm: int = 6
    """Tesseract Page Segmentation Mode."""

    lang: str = "eng+spa"
    """Tesseract language(s)."""

    preprocess: list[str] = field(default_factory=list)
    """Preprocessing steps: 'contrast', 'sharpness', 'denoise', 'binarize'."""

    enhance_contrast: float = 1.0
    """Contrast enhancement factor (1.0 = no change)."""

    enhance_sharpness: float = 1.0
    """Sharpness enhancement factor (1.0 = no change)."""

    skip_ocr: bool = False
    """If True, skip OCR entirely (e.g., blank pages)."""

    needs_review: bool = False
    """If True, page needs manual review."""


@dataclass
class PageClassificationResult:
    """Result of classifying a single page."""

    page_number: int
    """1-indexed page number."""

    classification: PageClassification
    """The classification result."""

    confidence: float
    """Classification confidence (0.0 - 1.0)."""

    needs_ocr: bool
    """Whether this page needs OCR processing."""

    needs_strong_ocr: bool
    """Whether this page needs handwriting-optimized OCR."""

    ocr_params: OCRParameters | None = None
    """Selected OCR parameters (set by router)."""


@dataclass
class PreprocessedImage:
    """Result of image preprocessing."""

    image: object  # PIL.Image but avoid import at module level
    """The preprocessed PIL Image."""

    steps_applied: list[str]
    """List of preprocessing steps that were applied."""

    processing_time_ms: float
    """Time taken for preprocessing in milliseconds."""

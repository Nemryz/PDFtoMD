# Shared dataclasses and enums, so the modules don't import each other to talk about a page.

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class PageClassification(Enum):
    # The kinds of page I can tell apart.

    BLANK = "blank"
    # Nothing on it, by pixel variance.

    TYPED_CLEAN = "typed_clean"
    # Typed and nothing added by hand.

    TYPED_SIGNED = "typed_signed"
    # Typed, but with a signature or a stamp on it.

    TYPED_ANNOTATED = "typed_annotated"
    # Typed with handwriting in the margins that actually says something.

    HANDWRITTEN = "handwritten"
    # The body text itself is handwritten.

    IMAGE_ONLY = "image_only"
    # Pictures and diagrams, nothing to read.

    UNKNOWN = "unknown"
    # I couldn't place it, so I don't guess.

    @classmethod
    def from_ocrsieve(cls, label: str) -> PageClassification:
        # ocrsieve has its own labels, so I translate rather than duplicate.
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
    # Everything that varies per page when OCR is adaptive.

    dpi: int = 300
    # I render the page at this DPI.

    psm: int = 6
    # Passed straight to Tesseract as --psm.

    lang: str = "eng+spa"
    # Language packs, same syntax Tesseract uses.

    preprocess: list[str] = field(default_factory=list)
    # Which enhancers to run, in order.

    enhance_contrast: float = 1.0
    # A multiplier above 1 pushes contrast further apart.

    enhance_sharpness: float = 1.0
    # Same idea for sharpness.

    skip_ocr: bool = False
    # Blank pages skip OCR entirely.

    needs_review: bool = False
    # I flag the page so a human can check it later.


@dataclass
class PageClassificationResult:
    # One page's verdict.

    page_number: int
    # 1-indexed, to match what the reader sees.

    classification: PageClassification
    # The bucket itself.

    confidence: float
    # How sure the classifier was, 0 to 1.

    needs_ocr: bool
    # Whether this page needs OCR at all.

    needs_strong_ocr: bool
    # Whether it needs the handwriting-tuned parameters.

    ocr_params: OCRParameters | None = None
    # The router fills this in after classification.


@dataclass
class PreprocessedImage:
    # What came back from the preprocessor.

    image: object  # PIL.Image but avoid import at module level
    # The enhanced image, ready for OCR.

    steps_applied: list[str]
    # Which enhancers actually ran, which may differ from what was asked.

    processing_time_ms: float
    # Wall-clock cost, useful when tuning the gate.

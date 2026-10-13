"""Signature detector — detect signature regions in PDF pages."""

from __future__ import annotations

from dataclasses import dataclass, field

from PIL import Image


@dataclass
class SignatureRegion:
    """A detected signature region on a page."""

    x: int
    y: int
    width: int
    height: int
    confidence: float


@dataclass
class PageSignatures:
    """Signature information for a single page."""

    page_number: int
    signatures: list[SignatureRegion] = field(default_factory=list)
    expected_signers: list[str] = field(default_factory=list)
    matched_signers: list[str] = field(default_factory=list)


@dataclass
class SignatureReport:
    """Full signature report for the document."""

    total_pages: int
    pages_with_signatures: int
    pages_without_signatures: int
    expected_signers: list[str]
    unmatched_signers: list[str]
    pages: list[PageSignatures] = field(default_factory=list)


def detect_signatures(image: Image.Image) -> list[SignatureRegion]:
    """Detect potential signature regions in a page image.

    Uses heuristics to find dark ink regions that could be signatures:
    - Located in the bottom portion of the page
    - Has reasonable aspect ratio for a signature
    - Contains dark pixels (ink)

    Args:
        image: PIL Image of the page.

    Returns:
        List of SignatureRegion objects (may be empty).
    """
    regions: list[SignatureRegion] = []

    width, height = image.size

    # Focus on the bottom 30% of the page where signatures typically appear
    bottom_zone_top = int(height * 0.7)
    bottom_zone = image.crop((0, bottom_zone_top, width, height))

    # Convert to grayscale for analysis
    gray = bottom_zone.convert("L")

    # Simple heuristic: look for dark pixel clusters
    # This is a basic approach; a production system would use ML
    pixels = list(gray.get_flattened_data())
    total_pixels = len(pixels)

    if total_pixels == 0:
        return regions

    # Count dark pixels (potential ink)
    dark_threshold = 128
    dark_pixels = sum(1 for p in pixels if p < dark_threshold)
    dark_ratio = dark_pixels / total_pixels

    # If there's a reasonable amount of dark content, it could be a signature
    if 0.01 < dark_ratio < 0.15:
        # Find bounding box of dark pixels
        dark_coords = [
            (i % width, bottom_zone_top + i // width)
            for i, p in enumerate(pixels)
            if p < dark_threshold
        ]

        if dark_coords:
            xs = [c[0] for c in dark_coords]
            ys = [c[1] for c in dark_coords]
            x_min, x_max = min(xs), max(xs)
            y_min, y_max = min(ys), max(ys)

            sig_width = x_max - x_min
            sig_height = y_max - y_min

            # Reasonable signature dimensions
            if 50 < sig_width < width * 0.5 and 20 < sig_height < height * 0.15:
                regions.append(
                    SignatureRegion(
                        x=x_min,
                        y=y_min,
                        width=sig_width,
                        height=sig_height,
                        confidence=min(dark_ratio * 10, 1.0),
                    )
                )

    return regions


def match_signer(
    region: SignatureRegion,
    signers: list[str],
    page_text: str = "",
) -> str | None:
    """Try to match a signature region to a known signer.

    Uses text proximity — if a signer's name appears near the
    signature region in the OCR text, we assume it's their signature.

    Args:
        region: Detected signature region.
        signers: List of expected signer names.
        page_text: OCR text of the page for name matching.

    Returns:
        Matched signer name or None.
    """
    if not signers or not page_text:
        return None

    text_lower = page_text.lower()

    for signer in signers:
        if signer.lower() in text_lower:
            return signer

    return None


def generate_signature_report(pages: list[PageSignatures]) -> SignatureReport:
    """Generate a summary report of signature detection.

    Args:
        pages: List of PageSignatures for each page.

    Returns:
        SignatureReport with summary statistics.
    """
    all_expected: set[str] = set()
    all_matched: set[str] = set()

    for ps in pages:
        all_expected.update(ps.expected_signers)
        all_matched.update(ps.matched_signers)

    pages_with = sum(1 for ps in pages if ps.signatures)
    pages_without = len(pages) - pages_with
    unmatched = list(all_expected - all_matched)

    return SignatureReport(
        total_pages=len(pages),
        pages_with_signatures=pages_with,
        pages_without_signatures=pages_without,
        expected_signers=sorted(all_expected),
        unmatched_signers=sorted(unmatched),
        pages=pages,
    )

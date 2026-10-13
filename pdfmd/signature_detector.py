# I hunt for signature-shaped ink on a page.

from __future__ import annotations

from dataclasses import dataclass, field

from PIL import Image


@dataclass
class SignatureRegion:
    # A box I believe holds a signature, with a rough confidence.

    x: int
    y: int
    width: int
    height: int
    confidence: float


@dataclass
class PageSignatures:
    # What I found on one page, plus who the caller expected.

    page_number: int
    signatures: list[SignatureRegion] = field(default_factory=list)
    expected_signers: list[str] = field(default_factory=list)
    matched_signers: list[str] = field(default_factory=list)


@dataclass
class SignatureReport:
    # The rolled-up view across the document.

    total_pages: int
    pages_with_signatures: int
    pages_without_signatures: int
    expected_signers: list[str]
    unmatched_signers: list[str]
    pages: list[PageSignatures] = field(default_factory=list)


def detect_signatures(image: Image.Image) -> list[SignatureRegion]:
    # Signatures sit low on the page, so I only look at the bottom third.
    regions: list[SignatureRegion] = []

    width, height = image.size

    # The top of that zone, which is where I start cropping.
    bottom_zone_top = int(height * 0.7)
    bottom_zone = image.crop((0, bottom_zone_top, width, height))

    # I flatten to grey because I'm only counting dark pixels here.
    gray = bottom_zone.convert("L")

    # This is a crude heuristic, not a trained model, and it says so.
    # A real implementation would learn where signatures look like this.
    pixels = list(gray.get_flattened_data())
    total_pixels = len(pixels)

    if total_pixels == 0:
        return regions

    # Dark pixels are the candidate ink.
    dark_threshold = 128
    dark_pixels = sum(1 for p in pixels if p < dark_threshold)
    dark_ratio = dark_pixels / total_pixels

    # Too little ink means no signature, too much means it's body text.
    if 0.01 < dark_ratio < 0.15:
        # One bounding box over all the ink I found in the zone.
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

            # A signature is wide and short, so I check the proportions.
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
    # I match by name proximity in the page text, which is a guess, not a proof.
    if not signers or not page_text:
        return None

    text_lower = page_text.lower()

    for signer in signers:
        if signer.lower() in text_lower:
            return signer

    return None


def generate_signature_report(pages: list[PageSignatures]) -> SignatureReport:
    # I roll the per-page results into one report and list anyone who never matched.
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

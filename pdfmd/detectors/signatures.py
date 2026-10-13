# I wrap the existing signature detector so the pipeline can call it through
# the registry. The behaviour is unchanged, I only reshape the return value.

from __future__ import annotations

from pdfmd.detectors.base import DetectionContext, DetectionResult
from pdfmd.detectors.registry import register
from pdfmd.signature_detector import detect_signatures
from pdfmd.taxonomy import SIGNATURE


@register
class SignatureDetector:
    # I reuse the old heuristic verbatim and translate its regions into blocks.

    name = "signatures"
    block_types = frozenset({SIGNATURE})

    def detect(self, ctx: DetectionContext) -> DetectionResult:
        if not ctx.has_image:
            return DetectionResult(blocks=[], confidence=0.0, notes={"skipped": "no image"})

        regions = detect_signatures(ctx.image)
        blocks = []
        for region in regions:
            blocks.append(
                _signature_block(region, ctx.page_number)
            )

        confidence = max((r.confidence for r in regions), default=0.0)
        return DetectionResult(
            blocks=blocks,
            confidence=confidence,
            # I hand the raw regions back too, since signer matching still
            # works on regions rather than blocks.
            notes={"regions": len(regions), "signature_regions": regions},
        )


def _signature_block(region, page_number: int):
    # I import Block lazily to keep this module free of a circular import.
    from pdfmd.content_analyzer import Block

    text = f"[Firma detectada, confianza {region.confidence:.0%}]"
    return Block(
        type=SIGNATURE,
        text=text,
        confidence=region.confidence,
        bbox=(region.x, region.y, region.x + region.width, region.y + region.height),
        level=0,
        source="heuristic",
    )

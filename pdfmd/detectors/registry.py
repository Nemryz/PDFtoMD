# I keep a list of detectors so the pipeline never has to know which ones exist.
# Adding one means importing it here, nothing in core.py changes.

from __future__ import annotations

import logging

from pdfmd.detectors.base import DetectionContext, DetectionResult, Detector

logger = logging.getLogger(__name__)

_REGISTRY: dict[str, Detector] = {}


def register(detector: Detector) -> Detector:
    # I take the detector as it is and file it under its own name, so the same
    # function can be used as a decorator.
    if detector.name in _REGISTRY:
        raise ValueError(f"detector already registered: {detector.name}")
    _REGISTRY[detector.name] = detector
    logger.debug("registered detector %s", detector.name)
    return detector


def get(name: str) -> Detector | None:
    return _REGISTRY.get(name)


def registered() -> frozenset[str]:
    return frozenset(_REGISTRY)


def run_detectors(ctx: DetectionContext, names: list[str] | None = None) -> DetectionResult:
    # I walk the requested detectors in order, collect their blocks, and never
    # let one failure take the page down.
    targets = names if names is not None else list(_REGISTRY)
    blocks = []
    notes = {}
    confidence = 0.0

    for name in targets:
        detector = _REGISTRY.get(name)
        if detector is None:
            logger.warning("unknown detector requested: %s", name)
            continue
        try:
            result = detector.detect(ctx)
        except Exception:
            logger.exception("detector %s failed on page %s", name, ctx.page_number)
            continue
        if result is None:
            continue
        blocks.extend(result.blocks)
        notes[name] = result.notes
        confidence = max(confidence, result.confidence)

    return DetectionResult(blocks=blocks, confidence=confidence, notes=notes)


def clear() -> None:
    # Only used by tests, so they can start from an empty registry.
    _REGISTRY.clear()

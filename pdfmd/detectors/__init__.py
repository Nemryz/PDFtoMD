# I expose the registry and the shapes a detector works with.

from __future__ import annotations

from pdfmd.detectors.base import DetectionContext, DetectionResult, Detector
from pdfmd.detectors.registry import (
    clear,
    get,
    register,
    registered,
    run_detectors,
)

__all__ = [
    "DetectionContext",
    "DetectionResult",
    "Detector",
    "clear",
    "get",
    "register",
    "registered",
    "run_detectors",
]

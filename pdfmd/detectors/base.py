# What a detector is given, and what it is expected to hand back.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from PIL import Image

    from pdfmd.content_analyzer import Block


@dataclass
class DetectionContext:
    # I pass one of these to every detector, carrying whatever is known about
    # the page at the time it runs.

    page_number: int
    text: str = ""
    image: Image | None = None
    blocks: list[Block] = field(default_factory=list)
    layout: object | None = None
    extras: dict = field(default_factory=dict)

    @property
    def has_layout(self) -> bool:
        # Geometry is not available until Feature 005 lands, so detectors that
        # need it check this first instead of assuming.
        return self.layout is not None

    @property
    def has_image(self) -> bool:
        return self.image is not None


@dataclass
class DetectionResult:
    # A detector reports blocks and whatever else it wants to pass along.

    blocks: list[Block] = field(default_factory=list)
    confidence: float = 0.0
    notes: dict = field(default_factory=dict)


@runtime_checkable
class Detector(Protocol):
    # The three things I need from anything registered: a name for logging,
    # the types it may emit, and the call itself.

    name: str
    block_types: frozenset[str]

    def detect(self, ctx: DetectionContext) -> DetectionResult: ...

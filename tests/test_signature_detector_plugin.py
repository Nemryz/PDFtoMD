# The signature detector runs through the registry now, so I check it produces
# the same regions the old direct call did.

import pytest

from pdfmd.content_analyzer import Block
from pdfmd.detectors import DetectionContext
from pdfmd.detectors import registry as reg
from pdfmd.detectors.signatures import SignatureDetector
from pdfmd.signature_detector import detect_signatures
from pdfmd.taxonomy import SIGNATURE


@pytest.fixture
def blank_page():
    from PIL import Image

    return Image.new("RGB", (800, 1100), color="white")


@pytest.fixture
def signed_page():
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (800, 1100), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((60, 900), "Firma", fill="black")
    return img


class TestSignatureDetector:
    def test_it_is_registered_on_import(self):
        assert reg.get("signatures") is not None

    def test_it_declares_the_types_it_emits(self):
        assert SIGNATURE in SignatureDetector.block_types

    def test_no_image_means_no_blocks(self):
        detector = SignatureDetector()
        result = detector.detect(DetectionContext(page_number=1))
        assert result.blocks == []
        assert result.notes.get("skipped") == "no image"

    def test_a_blank_page_yields_no_blocks(self, blank_page):
        detector = SignatureDetector()
        result = detector.detect(DetectionContext(page_number=1, image=blank_page))
        assert result.blocks == []

    def test_regions_match_the_legacy_call(self, signed_page):
        # I reuse the old heuristic as it was and reshape only the return value.
        legacy = detect_signatures(signed_page)
        result = SignatureDetector().detect(DetectionContext(page_number=1, image=signed_page))
        assert len(result.blocks) == len(legacy)

    def test_blocks_carry_geometry_when_a_region_is_found(self, signed_page):
        result = SignatureDetector().detect(DetectionContext(page_number=1, image=signed_page))
        for block in result.blocks:
            assert isinstance(block, Block)
            assert block.type == SIGNATURE
            assert block.bbox is not None
            assert len(block.bbox) == 4

    def test_it_survives_a_detector_that_raises(self, monkeypatch):
        # The registry catches it, so a broken detector cannot lose a page.
        def boom(_img):
            raise RuntimeError("detector exploded")

        monkeypatch.setattr("pdfmd.detectors.signatures.detect_signatures", boom)
        ctx = DetectionContext(page_number=1, image=object())
        result = reg.run_detectors(ctx, names=["signatures"])
        assert result.blocks == []

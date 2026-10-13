# The registry has to stay reliable even when a detector misbehaves, since a
# page should never be lost just because one detector raised.

import pytest

from pdfmd import detectors
from pdfmd.content_analyzer import Block
from pdfmd.detectors import DetectionContext, DetectionResult, register
from pdfmd.detectors import registry as reg
from pdfmd.taxonomy import HEADING, SEAL


@pytest.fixture(autouse=True)
def _clean_registry():
    # I snapshot the registry rather than just emptying it, because clearing it
    # outright would unregister the signature detector for every later test.
    saved = dict(reg._REGISTRY)
    reg.clear()
    yield
    reg._REGISTRY.clear()
    reg._REGISTRY.update(saved)


def _block(text="x"):
    return Block(type=HEADING, text=text, confidence=0.9)


class TestRegistration:
    def test_register_adds_and_returns_the_detector(self):
        class Fake:
            name = "fake"
            block_types = frozenset({HEADING})

            def detect(self, ctx):
                return DetectionResult()

        detector = Fake()
        assert register(detector) is detector
        assert reg.get("fake") is detector
        assert "fake" in reg.registered()

    def test_duplicate_names_are_refused(self):
        class Fake:
            name = "dup"
            block_types = frozenset({HEADING})

            def detect(self, ctx):
                return DetectionResult()

        register(Fake())
        with pytest.raises(ValueError, match="already registered"):
            register(Fake())

    def test_get_returns_none_for_an_unknown_name(self):
        assert reg.get("never_registered") is None


class TestRunDetectors:
    def test_blocks_from_several_detectors_are_concatenated(self):
        class A:
            name = "a"
            block_types = frozenset({HEADING})

            def detect(self, ctx):
                return DetectionResult(blocks=[_block("from a")], confidence=0.5)

        class B:
            name = "b"
            block_types = frozenset({SEAL})

            def detect(self, ctx):
                return DetectionResult(blocks=[_block("from b")], confidence=0.9)

        register(A())
        register(B())
        result = reg.run_detectors(DetectionContext(page_number=1))
        assert [b.text for b in result.blocks] == ["from a", "from b"]

    def test_highest_confidence_wins(self):
        class A:
            name = "a"
            block_types = frozenset({HEADING})

            def detect(self, ctx):
                return DetectionResult(confidence=0.3)

        class B:
            name = "b"
            block_types = frozenset({HEADING})

            def detect(self, ctx):
                return DetectionResult(confidence=0.8)

        register(A())
        register(B())
        assert reg.run_detectors(DetectionContext(page_number=1)).confidence == pytest.approx(0.8)

    def test_a_raising_detector_does_not_stop_the_others(self):
        class Boom:
            name = "boom"
            block_types = frozenset({HEADING})

            def detect(self, ctx):
                raise RuntimeError("detector exploded")

        class Fine:
            name = "fine"
            block_types = frozenset({HEADING})

            def detect(self, ctx):
                return DetectionResult(blocks=[_block("survived")])

        register(Boom())
        register(Fine())
        result = reg.run_detectors(DetectionContext(page_number=1))
        assert [b.text for b in result.blocks] == ["survived"]

    def test_a_detector_returning_none_is_tolerated(self):
        class Nothing:
            name = "nothing"
            block_types = frozenset({HEADING})

            def detect(self, ctx):
                return None

        register(Nothing())
        result = reg.run_detectors(DetectionContext(page_number=1))
        assert result.blocks == []

    def test_unknown_names_are_skipped_not_fatal(self):
        result = reg.run_detectors(DetectionContext(page_number=1), names=["ghost"])
        assert result.blocks == []

    def test_an_explicit_list_selects_detectors(self):
        class A:
            name = "a"
            block_types = frozenset({HEADING})

            def detect(self, ctx):
                return DetectionResult(blocks=[_block("a")])

        class B:
            name = "b"
            block_types = frozenset({HEADING})

            def detect(self, ctx):
                return DetectionResult(blocks=[_block("b")])

        register(A())
        register(B())
        result = reg.run_detectors(DetectionContext(page_number=1), names=["b"])
        assert [b_.text for b_ in result.blocks] == ["b"]

    def test_notes_are_collected_per_detector(self):
        class A:
            name = "a"
            block_types = frozenset({HEADING})

            def detect(self, ctx):
                return DetectionResult(notes={"regions": 2})

        register(A())
        assert reg.run_detectors(DetectionContext(page_number=1)).notes == {"a": {"regions": 2}}


class TestContext:
    def test_has_image_reflects_the_image(self):
        assert DetectionContext(page_number=1).has_image is False
        assert DetectionContext(page_number=1, image=object()).has_image is True

    def test_has_layout_is_false_until_geometry_lands(self):
        assert DetectionContext(page_number=1).has_layout is False
        assert DetectionContext(page_number=1, layout=object()).has_layout is True

    def test_extras_default_to_an_empty_dict_per_context(self):
        a = DetectionContext(page_number=1)
        b = DetectionContext(page_number=2)
        a.extras["k"] = 1
        assert b.extras == {}

    def test_blocks_default_to_an_empty_list_per_context(self):
        a = DetectionContext(page_number=1)
        b = DetectionContext(page_number=2)
        a.blocks.append(_block())
        assert b.blocks == []


class TestPackageExports:
    def test_the_package_exports_what_detectors_need(self):
        for name in ("DetectionContext", "DetectionResult", "Detector",
                     "register", "run_detectors", "registered", "get"):
            assert hasattr(detectors, name), f"missing export: {name}"

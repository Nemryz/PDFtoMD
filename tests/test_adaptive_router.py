"""Tests for adaptive OCR router module."""

from pdfmd.adaptive_router import (
    ROUTING_TABLE,
    AdaptiveOCRRouter,
    get_default_parameters,
)
from pdfmd.types import (
    OCRParameters,
    PageClassification,
    PageClassificationResult,
)


class TestRoutingTable:
    """Test the routing table configuration."""

    def test_routing_table_has_all_classifications(self):
        """All classification types have routing entries."""
        for classification in PageClassification:
            assert classification in ROUTING_TABLE, f"Missing routing for {classification}"

    def test_routing_table_parameters_are_valid(self):
        """All routing parameters are valid."""
        for classification, params in ROUTING_TABLE.items():
            assert isinstance(params, OCRParameters), f"Invalid params for {classification}"
            assert params.dpi >= 72, f"DPI too low for {classification}"
            assert params.dpi <= 1200, f"DPI too high for {classification}"
            assert params.psm in [3, 4, 6, 7, 8, 11, 13], f"Invalid PSM for {classification}"

    def test_blank_page_skips_ocr(self):
        """Blank pages have skip_ocr=True."""
        assert ROUTING_TABLE[PageClassification.BLANK].skip_ocr is True

    def test_handwritten_needs_review(self):
        """Handwritten pages are flagged for review."""
        assert ROUTING_TABLE[PageClassification.HANDWRITTEN].needs_review is True

    def test_image_only_needs_review(self):
        """Image-only pages are flagged for review."""
        assert ROUTING_TABLE[PageClassification.IMAGE_ONLY].needs_review is True


class TestAdaptiveOCRRouter:
    """Test AdaptiveOCRRouter class."""

    def test_router_initializes(self):
        """Router can be created."""
        router = AdaptiveOCRRouter()
        assert router is not None

    def test_get_parameters_returns_ocr_parameters(self):
        """get_parameters returns OCRParameters."""
        router = AdaptiveOCRRouter()
        params = router.get_parameters(PageClassification.TYPED_CLEAN)
        assert isinstance(params, OCRParameters)

    def test_get_parameters_blank_skips_ocr(self):
        """Blank pages get skip_ocr=True."""
        router = AdaptiveOCRRouter()
        params = router.get_parameters(PageClassification.BLANK)
        assert params.skip_ocr is True

    def test_get_parameters_typed_clean(self):
        """Typed clean pages get standard parameters."""
        router = AdaptiveOCRRouter()
        params = router.get_parameters(PageClassification.TYPED_CLEAN)
        assert params.dpi == 300
        assert params.psm == 6
        assert params.skip_ocr is False

    def test_get_parameters_typed_annotated_higher_dpi(self):
        """Typed annotated pages get higher DPI."""
        router = AdaptiveOCRRouter()
        params = router.get_parameters(PageClassification.TYPED_ANNOTATED)
        assert params.dpi == 400
        assert "contrast" in params.preprocess

    def test_get_parameters_handwritten_highest_dpi(self):
        """Handwritten pages get highest DPI."""
        router = AdaptiveOCRRouter()
        params = router.get_parameters(PageClassification.HANDWRITTEN)
        assert params.dpi == 600
        assert params.psm == 11
        assert "denoise" in params.preprocess

    def test_get_parameters_unknown_fallback(self):
        """Unknown classification gets safe defaults."""
        router = AdaptiveOCRRouter()
        params = router.get_parameters(PageClassification.UNKNOWN)
        assert params.dpi == 300
        assert params.needs_review is True

    def test_get_parameters_custom_routing(self):
        """Custom routing table overrides defaults."""
        custom = {
            PageClassification.TYPED_CLEAN: OCRParameters(
                dpi=600,  # Override default 300
                psm=6,
                lang="eng+spa",
            )
        }
        router = AdaptiveOCRRouter(custom_routing=custom)
        params = router.get_parameters(PageClassification.TYPED_CLEAN)
        assert params.dpi == 600  # Custom value

    def test_get_parameters_for_result_low_confidence(self):
        """Low confidence results are flagged for review."""
        router = AdaptiveOCRRouter()
        result = PageClassificationResult(
            page_number=1,
            classification=PageClassification.TYPED_CLEAN,
            confidence=0.3,  # Low confidence
            needs_ocr=True,
            needs_strong_ocr=False,
        )
        params = router.get_parameters_for_result(result)
        assert params.needs_review is True  # Should be flagged

    def test_get_parameters_for_result_high_confidence(self):
        """High confidence results keep original review flag."""
        router = AdaptiveOCRRouter()
        result = PageClassificationResult(
            page_number=1,
            classification=PageClassification.TYPED_CLEAN,
            confidence=0.9,  # High confidence
            needs_ocr=True,
            needs_strong_ocr=False,
        )
        params = router.get_parameters_for_result(result)
        assert params.needs_review is False  # Original flag

    def test_route_pages_returns_list(self):
        """route_pages returns list of tuples."""
        router = AdaptiveOCRRouter()
        classifications = [
            PageClassificationResult(
                page_number=i,
                classification=PageClassification.TYPED_CLEAN,
                confidence=0.8,
                needs_ocr=True,
                needs_strong_ocr=False,
            )
            for i in range(3)
        ]

        routed = router.route_pages(classifications)
        assert len(routed) == 3
        assert all(isinstance(r, tuple) for r in routed)
        assert all(isinstance(r[1], OCRParameters) for r in routed)

    def test_route_pages_counts_skips(self):
        """route_pages counts skipped pages."""
        router = AdaptiveOCRRouter()
        classifications = [
            PageClassificationResult(
                page_number=1,
                classification=PageClassification.BLANK,
                confidence=0.9,
                needs_ocr=False,
                needs_strong_ocr=False,
            ),
            PageClassificationResult(
                page_number=2,
                classification=PageClassification.TYPED_CLEAN,
                confidence=0.8,
                needs_ocr=True,
                needs_strong_ocr=False,
            ),
        ]

        routed = router.route_pages(classifications)
        skip_count = sum(1 for _, p in routed if p.skip_ocr)
        assert skip_count == 1

    def test_get_routing_summary(self):
        """get_routing_summary returns valid summary."""
        router = AdaptiveOCRRouter()
        summary = router.get_routing_summary()

        assert isinstance(summary, dict)
        assert "blank" in summary
        assert "typed_clean" in summary
        assert "dpi" in summary["blank"]
        assert "skip_ocr" in summary["blank"]


class TestGetDefaultParameters:
    """Test get_default_parameters function."""

    def test_returns_copy(self):
        """Returns a copy, not the original."""
        params1 = get_default_parameters()
        params2 = get_default_parameters()
        assert params1 is not params2

    def test_contains_all_classifications(self):
        """Contains all classification types."""
        params = get_default_parameters()
        for classification in PageClassification:
            assert classification in params

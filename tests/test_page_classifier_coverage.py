"""Coverage tests for page_classifier module."""

import pymupdf
import pytest

from pdfmd.page_classifier import PageClassifier
from pdfmd.types import PageClassification

FIXTURE_DIR = __import__("pathlib").Path(__file__).parent / "fixtures"
REAL_PDF = FIXTURE_DIR / "expediente Miranda ..pdf"


class TestPageClassifierCoverage:
    """Tests to increase page_classifier.py coverage."""

    def test_classifier_init(self):
        clf = PageClassifier()
        assert clf is not None

    def test_classify_page_returns_result(self):
        if not REAL_PDF.exists():
            pytest.skip("Fixture PDF not found")
        doc = pymupdf.open(str(REAL_PDF))
        clf = PageClassifier()
        result = clf.classify_page(doc, 0)
        assert result is not None
        assert hasattr(result, "classification")
        assert hasattr(result, "confidence")
        assert hasattr(result, "needs_ocr")
        doc.close()

    def test_classify_page_returns_valid_classification(self):
        if not REAL_PDF.exists():
            pytest.skip("Fixture PDF not found")
        doc = pymupdf.open(str(REAL_PDF))
        clf = PageClassifier()
        result = clf.classify_page(doc, 0)
        assert isinstance(result.classification, PageClassification)
        doc.close()

    def test_classify_multiple_pages(self):
        if not REAL_PDF.exists():
            pytest.skip("Fixture PDF not found")
        doc = pymupdf.open(str(REAL_PDF))
        clf = PageClassifier()
        for i in range(min(5, doc.page_count)):
            result = clf.classify_page(doc, i)
            assert result is not None
        doc.close()

    def test_classify_empty_page(self):
        doc = pymupdf.open()
        doc.new_page()
        clf = PageClassifier()
        result = clf.classify_page(doc, 0)
        assert result is not None
        assert result.classification in list(PageClassification)
        doc.close()

    def test_classify_page_with_text(self):
        doc = pymupdf.open()
        page = doc.new_page()
        page.insert_text((72, 72), "This is a typed document with clear text content.")
        clf = PageClassifier()
        result = clf.classify_page(doc, 0)
        assert result is not None
        assert result.needs_ocr is False or result.confidence > 0
        doc.close()

    def test_classify_page_returns_page_number(self):
        if not REAL_PDF.exists():
            pytest.skip("Fixture PDF not found")
        doc = pymupdf.open(str(REAL_PDF))
        clf = PageClassifier()
        result = clf.classify_page(doc, 0)
        assert result.page_number == 1
        doc.close()

    def test_all_classification_types_exist(self):
        for cls in PageClassification:
            assert cls.value is not None


from pathlib import Path

import pymupdf
import pytest

from pdfmd.page_classifier import PageClassifier
from pdfmd.types import PageClassification, PageClassificationResult


class TestPageClassification:

    def test_classification_values(self):
        assert PageClassification.BLANK.value == "blank"
        assert PageClassification.TYPED_CLEAN.value == "typed_clean"
        assert PageClassification.TYPED_SIGNED.value == "typed_signed"
        assert PageClassification.TYPED_ANNOTATED.value == "typed_annotated"
        assert PageClassification.HANDWRITTEN.value == "handwritten"
        assert PageClassification.IMAGE_ONLY.value == "image_only"
        assert PageClassification.UNKNOWN.value == "unknown"

    def test_from_ocrsieve_mapping(self):
        assert PageClassification.from_ocrsieve("blank") == PageClassification.BLANK
        assert PageClassification.from_ocrsieve("typed_clean") == PageClassification.TYPED_CLEAN
        assert PageClassification.from_ocrsieve("typed_signed") == PageClassification.TYPED_SIGNED
        assert (
            PageClassification.from_ocrsieve("typed_annotated")
            == PageClassification.TYPED_ANNOTATED
        )
        assert PageClassification.from_ocrsieve("handwritten") == PageClassification.HANDWRITTEN
        assert PageClassification.from_ocrsieve("digital_text") == PageClassification.TYPED_CLEAN

    def test_from_ocrsieve_unknown(self):
        assert PageClassification.from_ocrsieve("unknown_label") == PageClassification.UNKNOWN
        assert PageClassification.from_ocrsieve("") == PageClassification.UNKNOWN


class TestPageClassifier:

    def test_classifier_initializes(self):
        classifier = PageClassifier()
        assert classifier is not None

    def test_classify_page_returns_result(self):
        classifier = PageClassifier()

        # Create a simple test PDF
        doc = pymupdf.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Test content")

        result = classifier.classify_page(doc, 0)

        assert isinstance(result, PageClassificationResult)
        assert result.page_number == 1
        assert isinstance(result.classification, PageClassification)
        assert 0.0 <= result.confidence <= 1.0
        assert isinstance(result.needs_ocr, bool)
        assert isinstance(result.needs_strong_ocr, bool)

        doc.close()

    def test_classify_page_number_is_1_indexed(self):
        classifier = PageClassifier()

        doc = pymupdf.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Test")

        result = classifier.classify_page(doc, 0)
        assert result.page_number == 1

        result2 = classifier.classify_page(doc, 0)
        assert result2.page_number == 1

        doc.close()

    def test_classify_document_returns_list(self):
        classifier = PageClassifier()

        # Create test PDF with 3 pages
        doc = pymupdf.open()
        for _ in range(3):
            page = doc.new_page()
            page.insert_text((72, 72), "Test content")

        # Save to temp file
        temp_path = Path("test_classifier_temp.pdf")
        doc.save(str(temp_path))
        doc.close()

        try:
            results = classifier.classify_document(temp_path)

            assert len(results) == 3
            assert all(isinstance(r, PageClassificationResult) for r in results)
            assert results[0].page_number == 1
            assert results[1].page_number == 2
            assert results[2].page_number == 3
        finally:
            temp_path.unlink(missing_ok=True)

    def test_classify_document_file_not_found(self):
        classifier = PageClassifier()

        with pytest.raises(FileNotFoundError):
            classifier.classify_document("nonexistent.pdf")

    def test_classify_text_page(self):
        classifier = PageClassifier()

        doc = pymupdf.open()
        page = doc.new_page()
        # Add substantial text
        text = "This is a test document with enough text to be detected. " * 10
        page.insert_text((72, 72), text)

        result = classifier.classify_page(doc, 0)

        # Should be classified as typed (clean or annotated)
        assert result.classification in [
            PageClassification.TYPED_CLEAN,
            PageClassification.TYPED_ANNOTATED,
        ]
        # needs_ocr depends on the ocrsieve model, so I just check it is a bool.
        assert isinstance(result.needs_ocr, bool)

        doc.close()

    def test_classify_blank_page(self):
        classifier = PageClassifier()

        doc = pymupdf.open()
        page = doc.new_page()  # Empty page

        result = classifier.classify_page(doc, 0)

        assert result.classification == PageClassification.BLANK
        assert result.needs_ocr is False

        doc.close()

    def test_heuristic_fallback_works(self):
        classifier = PageClassifier()

        # Force heuristic mode
        classifier._ocrsieve_available = False
        classifier._classifier = None

        doc = pymupdf.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Test content")

        result = classifier.classify_page(doc, 0)

        assert isinstance(result, PageClassificationResult)
        assert result.classification != PageClassification.UNKNOWN

        doc.close()


class TestPageClassifierWithRealPDF:

    @pytest.fixture
    def sample_pdf(self):
        doc = pymupdf.open()

        # Page 1: Text
        page1 = doc.new_page()
        page1.insert_text((72, 72), "Document title and content. " * 20)

        # Page 2: Blank
        doc.new_page()

        # Page 3: More text
        page3 = doc.new_page()
        page3.insert_text((72, 72), "Another page with text. " * 20)

        temp_path = Path("test_sample.pdf")
        doc.save(str(temp_path))
        doc.close()

        yield temp_path

        temp_path.unlink(missing_ok=True)

    def test_classifies_multiple_pages(self, sample_pdf):
        classifier = PageClassifier()
        results = classifier.classify_document(sample_pdf)

        assert len(results) == 3
        assert results[0].classification != PageClassification.BLANK
        assert results[1].classification == PageClassification.BLANK
        assert results[2].classification != PageClassification.BLANK

    def test_classification_confidence_range(self, sample_pdf):
        classifier = PageClassifier()
        results = classifier.classify_document(sample_pdf)

        for result in results:
            assert 0.0 <= result.confidence <= 1.0

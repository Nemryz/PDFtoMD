"""Coverage tests for exceptions module."""

from pdfmd.exceptions import (
    OCRError,
    OutputError,
    PDFCorruptedError,
    PdfmdError,
    PDFNotFoundError,
    PDFPasswordProtectedError,
    TesseractLanguageError,
    TesseractNotFoundError,
)


class TestPdfmdError:
    def test_base_exception(self):
        import pytest

        with pytest.raises(PdfmdError):
            raise PdfmdError("test error")


class TestPDFNotFoundError:
    def test_message(self):
        exc = PDFNotFoundError("/path/to/file.pdf")
        assert "/path/to/file.pdf" in str(exc)
        assert exc.path == "/path/to/file.pdf"

    def test_is_file_not_found_error(self):
        assert issubclass(PDFNotFoundError, FileNotFoundError)


class TestPDFCorruptedError:
    def test_message_with_reason(self):
        exc = PDFCorruptedError("/path/file.pdf", "truncated header")
        assert "truncated header" in str(exc)
        assert exc.reason == "truncated header"

    def test_message_without_reason(self):
        exc = PDFCorruptedError("/path/file.pdf")
        assert exc.reason == ""


class TestPDFPasswordProtectedError:
    def test_message(self):
        exc = PDFPasswordProtectedError("/path/secret.pdf")
        assert "password" in str(exc).lower()
        assert exc.path == "/path/secret.pdf"


class TestTesseractNotFoundError:
    def test_message_without_path(self):
        exc = TesseractNotFoundError()
        assert "tesseract" in str(exc).lower()

    def test_message_with_path(self):
        exc = TesseractNotFoundError("/usr/bin/tesseract")
        assert "/usr/bin/tesseract" in str(exc)
        assert exc.path == "/usr/bin/tesseract"


class TestTesseractLanguageError:
    def test_message(self):
        exc = TesseractLanguageError("deu")
        assert "deu" in str(exc)
        assert exc.lang == "deu"


class TestOCRError:
    def test_message_with_reason(self):
        exc = OCRError(5, "timeout")
        assert "page 5" in str(exc)
        assert "timeout" in str(exc)
        assert exc.page == 5
        assert exc.reason == "timeout"

    def test_message_without_reason(self):
        exc = OCRError(3)
        assert exc.reason == ""


class TestOutputError:
    def test_message_with_reason(self):
        exc = OutputError("/out/file.md", "permission denied")
        assert "permission denied" in str(exc)
        assert exc.path == "/out/file.md"
        assert exc.reason == "permission denied"

    def test_message_without_reason(self):
        exc = OutputError("/out/file.md")
        assert exc.reason == ""

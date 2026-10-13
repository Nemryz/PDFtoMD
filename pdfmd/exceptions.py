"""Custom exceptions for pdfmd."""


class PdfmdError(Exception):
    """Base exception for all pdfmd errors."""


class PDFNotFoundError(FileNotFoundError, PdfmdError):
    """Raised when the input PDF file does not exist."""

    def __init__(self, path: str) -> None:
        super().__init__(f"PDF file not found: {path}")
        self.path = path


class PDFCorruptedError(PdfmdError):
    """Raised when the PDF file is corrupted or unreadable."""

    def __init__(self, path: str, reason: str = "") -> None:
        msg = f"PDF file is corrupted: {path}"
        if reason:
            msg += f" ({reason})"
        super().__init__(msg)
        self.path = path
        self.reason = reason


class PDFPasswordProtectedError(PdfmdError):
    """Raised when the PDF requires a password to open."""

    def __init__(self, path: str) -> None:
        super().__init__(f"PDF is password-protected: {path}")
        self.path = path


class TesseractNotFoundError(PdfmdError):
    """Raised when Tesseract is not installed or not found."""

    def __init__(self, path: str | None = None) -> None:
        msg = "Tesseract is not installed or not found"
        if path:
            msg += f" at: {path}"
        msg += ". See INSTALL.md for installation instructions."
        super().__init__(msg)
        self.path = path


class TesseractLanguageError(PdfmdError):
    """Raised when a required Tesseract language pack is missing."""

    def __init__(self, lang: str) -> None:
        super().__init__(
            f"Tesseract language pack '{lang}' is not installed. "
            f"Install it with: tesseract-ocr-{lang}"
        )
        self.lang = lang


class OCRError(PdfmdError):
    """Raised when OCR processing fails on a page."""

    def __init__(self, page: int, reason: str = "") -> None:
        msg = f"OCR failed on page {page}"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)
        self.page = page
        self.reason = reason


class OutputError(PdfmdError):
    """Raised when writing output files fails."""

    def __init__(self, path: str, reason: str = "") -> None:
        msg = f"Failed to write output: {path}"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)
        self.path = path
        self.reason = reason

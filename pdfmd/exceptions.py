# Every exception pdfmd raises on purpose lives here.


class PdfmdError(Exception):
    # Base exception for all pdfmd errors, so callers can catch the family at once.
    pass


class PDFNotFoundError(FileNotFoundError, PdfmdError):
    # Raised when the input PDF file does not exist.
# I raise this when the input path doesn't exist.
    def __init__(self, path: str) -> None:
        super().__init__(f"PDF file not found: {path}")
        self.path = path


class PDFCorruptedError(PdfmdError):
    # Raised when the PDF file is corrupted or unreadable.
# PyMuPDF couldn't parse the file, so I pass along whatever reason it gave.
    def __init__(self, path: str, reason: str = "") -> None:
        msg = f"PDF file is corrupted: {path}"
        if reason:
            msg += f" ({reason})"
        super().__init__(msg)
        self.path = path
        self.reason = reason


class PDFPasswordProtectedError(PdfmdError):
    # Raised when the PDF requires a password to open.
# The PDF is encrypted and no password was supplied.
    def __init__(self, path: str) -> None:
        super().__init__(f"PDF is password-protected: {path}")
        self.path = path


class TesseractNotFoundError(PdfmdError):
    # Raised when Tesseract is not installed or not found.
# Tesseract is either not installed or not on PATH.
    def __init__(self, path: str | None = None) -> None:
        msg = "Tesseract is not installed or not found"
        if path:
            msg += f" at: {path}"
        msg += ". See INSTALL.md for installation instructions."
        super().__init__(msg)
        self.path = path


class TesseractLanguageError(PdfmdError):
    # Raised when a required Tesseract language pack is missing.
# Tesseract is installed but the requested language pack isn't.
    def __init__(self, lang: str) -> None:
        super().__init__(
            f"Tesseract language pack '{lang}' is not installed. "
            f"Install it with: tesseract-ocr-{lang}"
        )
        self.lang = lang


class OCRError(PdfmdError):
    # Raised when OCR processing fails on a page.
# Tesseract ran and failed on a specific page.
    def __init__(self, page: int, reason: str = "") -> None:
        msg = f"OCR failed on page {page}"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)
        self.page = page
        self.reason = reason


class OutputError(PdfmdError):
    # Raised when writing output files fails.
# Writing the output failed, usually permissions or a full disk.
    def __init__(self, path: str, reason: str = "") -> None:
        msg = f"Failed to write output: {path}"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)
        self.path = path
        self.reason = reason

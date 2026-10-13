"""PDF reader module — PyMuPDF wrapper for opening and reading PDFs."""

from __future__ import annotations

import pymupdf
from pymupdf import Document, Page

from pdfmd.exceptions import PDFCorruptedError, PDFNotFoundError, PDFPasswordProtectedError


def open_pdf(path: str) -> Document:
    """Open a PDF file and return a PyMuPDF Document.

    Raises:
        PDFNotFoundError: If the file does not exist.
        PDFPasswordProtectedError: If the PDF requires a password.
        PDFCorruptedError: If the PDF is corrupted or unreadable.
    """
    from pathlib import Path

    if not Path(path).exists():
        raise PDFNotFoundError(path)

    try:
        doc = pymupdf.open(path)
    except Exception as e:
        msg = str(e).lower()
        if "password" in msg or "encrypted" in msg:
            raise PDFPasswordProtectedError(path) from e
        raise PDFCorruptedError(path, str(e)) from e

    return doc


def get_page_count(doc: Document) -> int:
    """Return the number of pages in the document."""
    return doc.page_count


def has_text_layer(page: Page) -> bool:
    """Check if a page has a selectable text layer.

    Returns False for scanned/image-only pages.
    """
    text = page.get_text("text").strip()
    return len(text) > 50


def extract_page_text(page: Page) -> str:
    """Extract embedded text from a page (no OCR).

    Returns the raw text layer. For scanned PDFs this will be
    empty or near-empty — use OCR for those.
    """
    return page.get_text("text")

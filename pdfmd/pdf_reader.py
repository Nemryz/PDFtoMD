# Everything that touches PyMuPDF's document object, in one place.

from __future__ import annotations

import pymupdf
from pymupdf import Document, Page

from pdfmd.exceptions import PDFCorruptedError, PDFNotFoundError, PDFPasswordProtectedError


def open_pdf(path: str) -> Document:
    # I open the file and hand back the document.
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
    # Page count, which is also my blank-page check upstream.
    return doc.page_count


def has_text_layer(page: Page) -> bool:
    # A page with a text layer is far cheaper to read than to OCR.
    text = page.get_text("text").strip()
    return len(text) > 50


def extract_page_text(page: Page) -> str:
    # Native text extraction, no OCR involved.
    return page.get_text("text")

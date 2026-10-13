"""Page renderer — convert PDF pages to PIL images at specified DPI."""

from __future__ import annotations

import pymupdf
from PIL import Image
from pymupdf import Page


def render_page(page: Page, dpi: int = 300) -> Image.Image:
    """Render a PDF page to a PIL Image at the specified DPI.

    Args:
        page: PyMuPDF page object.
        dpi: Resolution in dots per inch (default 300).

    Returns:
        PIL Image of the rendered page.
    """
    # PyMuPDF renders at 72 DPI natively; scale factor = dpi / 72
    zoom = dpi / 72.0
    mat = pymupdf.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)

    # Convert from raw pixels to PIL Image
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    return img

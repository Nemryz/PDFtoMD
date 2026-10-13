# I turn PDF pages into PIL images at whatever DPI the caller asked for.

from __future__ import annotations

import pymupdf
from PIL import Image
from pymupdf import Page


def render_page(page: Page, dpi: int = 300) -> Image.Image:
    # PyMuPDF renders at 72 DPI, so the scale factor is just dpi over 72.
    # One matrix does the scaling for the whole page.
    zoom = dpi / 72.0
    mat = pymupdf.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)

    # The pixmap gives me raw samples, which I wrap back into a PIL image.
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    return img

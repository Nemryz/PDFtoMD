"""Content analyzer — detect document structure from OCR text."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Block:
    """A logical content block extracted from a page."""

    type: str  # heading, paragraph, list_item, page_number, header
    text: str
    confidence: float


def detect_heading(text: str) -> bool:
    """Detect if a line is a heading (all caps, short, or with colon)."""
    text = text.strip()
    if not text:
        return False
    if len(text) > 80:
        return False
    # All uppercase
    if text.isupper() and len(text) > 3:
        return True
    # Short with colon
    if len(text) < 40 and text.endswith(":"):
        return True
    return False


def detect_list_item(text: str) -> bool:
    """Detect if a line is a list item (bullet, number, dash)."""
    text = text.strip()
    if not text:
        return False
    patterns = [
        r"^[-•●]\s",  # bullet
        r"^\d+[\.\)]\s",  # numbered
        r"^[a-zA-Z][\.\)]\s",  # lettered
    ]
    return any(re.match(p, text) for p in patterns)


def detect_page_number(text: str) -> bool:
    """Detect if a line is just a page number."""
    text = text.strip()
    if not text:
        return False
    # Roman numerals
    if re.match(r"^[ivxlcdmIVXLCDM]+$", text):
        return True
    # Just a number
    if re.match(r"^\d{1,4}$", text):
        return True
    # "Página N" or "Page N"
    if re.match(r"^(?:Página|Page|Pág|Pg)\s*\d+$", text, re.IGNORECASE):
        return True
    return False


def detect_header(text: str, page_num: int) -> bool:
    """Detect if text is a repeated page header."""
    text = text.strip()
    if not text:
        return False
    if len(text) > 50:
        return False
    if page_num <= 1:
        return False
    # Short uppercase text on non-first pages
    if text.isupper() and len(text) > 3:
        return True
    return False


def analyze_page(text: str, confidence: float) -> list[Block]:
    """Analyze a page's OCR text and return structured blocks.

    Args:
        text: Raw OCR text from a single page.
        confidence: OCR confidence score (0.0-1.0).

    Returns:
        List of Block objects with type, text, and confidence.
    """
    blocks: list[Block] = []

    if not text or not text.strip():
        return blocks

    lines = text.split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if detect_page_number(line):
            blocks.append(Block(type="page_number", text=line, confidence=confidence))
        elif detect_heading(line):
            blocks.append(Block(type="heading", text=line, confidence=confidence))
        elif detect_list_item(line):
            blocks.append(Block(type="list_item", text=line, confidence=confidence))
        else:
            blocks.append(Block(type="paragraph", text=line, confidence=confidence))

    return blocks

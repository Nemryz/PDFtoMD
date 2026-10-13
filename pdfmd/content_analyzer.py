# I read the OCR text of one page and work out what kind of block each line is.

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Block:
    # One piece of a page: a heading, a paragraph, a list item, whatever it turned out to be.

    type: str  # heading, paragraph, list_item, page_number, header
    text: str
    confidence: float
    bbox: tuple[int, int, int, int] | None = None  # left, top, right, bottom in pixels
    level: int = 0  # nesting depth, so a heading knows whether it is an H1 or an H3
    source: str = "heuristic"  # heuristic, ocrsieve, or a model later on


def detect_heading(text: str) -> bool:
    # I call a line a heading when it's short, shouted, or ends in a colon.
    text = text.strip()
    if not text:
        return False
    if len(text) > 80:
        return False
    # All caps is the usual giveaway.
    if text.isupper() and len(text) > 3:
        return True
    # A colon at the end of a short line usually introduces a list.
    if len(text) < 40 and text.endswith(":"):
        return True
    return False


def detect_list_item(text: str) -> bool:
    # I match the usual bullet and numbering shapes.
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
    # Page numbers are the one thing I actively throw away later, so I flag them here.
    text = text.strip()
    if not text:
        return False
    # Roman numerals show up in front matter more than anywhere else.
    if re.match(r"^[ivxlcdmIVXLCDM]+$", text):
        return True
    # A bare number is almost always a page number.
    if re.match(r"^\d{1,4}$", text):
        return True
    # Some publishers spell it out, so I accept both languages.
    if re.match(r"^(?:Página|Page|Pág|Pg)\s*\d+$", text, re.IGNORECASE):
        return True
    return False


def detect_header(text: str, page_num: int) -> bool:
    # Repeated headers are short, uppercase, and never on page one.
    text = text.strip()
    if not text:
        return False
    if len(text) > 50:
        return False
    if page_num <= 1:
        return False
    # Short uppercase on a page past the first is my only signal here.
    if text.isupper() and len(text) > 3:
        return True
    return False


def analyze_page(text: str, confidence: float) -> list[Block]:
    # I walk each line, hand back blocks in order, each carrying the page confidence.
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

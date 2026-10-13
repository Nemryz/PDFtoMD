# I turn the blocks from one page into Markdown, with a page marker so I can find it later.

from __future__ import annotations

import re

from pdfmd.content_analyzer import Block


def _sanitize_list_item(text: str) -> str:
    # I strip the bullet or number the OCR left behind.
    # Covers 1. a) and the bullet characters.
    return re.sub(r"^[\d]+[\.\)]\s*|^[-•●]\s*", "", text).strip()


def build_markdown(blocks: list[Block], page_number: int) -> str:
    # I walk the blocks in order and emit one line each, skipping page numbers entirely.
    lines: list[str] = [f"<!-- Page {page_number} -->"]

    for block in blocks:
        if block.type == "page_number":
            continue  # Skip inferred page numbers
        elif block.type == "heading":
            lines.append(f"## {block.text}")
        elif block.type == "list_item":
            clean = _sanitize_list_item(block.text)
            lines.append(f"- {clean}")
        else:  # paragraph or anything else
            lines.append(block.text)

    return "\n".join(lines)

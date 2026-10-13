"""Markdown builder — convert content blocks to structured Markdown."""

from __future__ import annotations

import re

from pdfmd.content_analyzer import Block


def _sanitize_list_item(text: str) -> str:
    """Remove original list markers and return clean text."""
    # Remove leading markers like "1.", "•", "-", etc.
    return re.sub(r"^[\d]+[\.\)]\s*|^[-•●]\s*", "", text).strip()


def build_markdown(blocks: list[Block], page_number: int) -> str:
    """Convert a list of content blocks to Markdown for a single page.

    Args:
        blocks: List of Block objects from content_analyzer.
        page_number: 1-based page number for the comment marker.

    Returns:
        Markdown string for this page.
    """
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

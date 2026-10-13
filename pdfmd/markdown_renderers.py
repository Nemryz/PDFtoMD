# I keep one function per block type, so adding a type means adding a function
# rather than another branch in a chain of conditionals.

from __future__ import annotations

import re
from collections.abc import Callable

from pdfmd.content_analyzer import Block
from pdfmd.taxonomy import (
    CODE,
    FORMULA,
    HEADING,
    LIST_ITEM,
    SKIP,
)

Renderer = Callable[[Block], str | None]


def _render_heading(block: Block) -> str:
    # I prefix with hashes, using the block level when the analyser supplied one.
    depth = block.level if 1 <= block.level <= 6 else 2
    return f"{'#' * depth} {block.text}"


def _render_list_item(block: Block) -> str:
    # I drop the marker OCR left behind and put my own bullet in front.
    cleaned = re.sub(r"^[\d]+[\.\)]\s*|^[-•●]\s*", "", block.text).strip()
    return f"- {cleaned}"


def _render_formula(block: Block) -> str:
    # I wrap maths in dollars so Markdown renderers pick it up as LaTeX.
    return f"$${block.text}$$"


def _render_code(block: Block) -> str:
    # Fenced blocks keep their own line breaks, unlike paragraphs.
    return f"```\n{block.text}\n```"


def _render_verbatim(block: Block) -> str:
    # Anything with no renderer of its own is emitted as it arrived.
    return block.text


RENDERERS: dict[str, Renderer] = {
    HEADING: _render_heading,
    LIST_ITEM: _render_list_item,
    FORMULA: _render_formula,
    CODE: _render_code,
}

SKIPPED: frozenset[str] = SKIP


def render_block(block: Block) -> str | None:
    # I look up the renderer by type, and return None for the ones we drop.
    if block.type in SKIPPED:
        return None
    renderer = RENDERERS.get(block.type, _render_verbatim)
    return renderer(block)


def render_blocks(blocks: list[Block], page_number: int) -> str:
    # I open with the page marker, then one line per block that survives.
    lines = [f"<!-- Page {page_number} -->"]
    for block in blocks:
        rendered = render_block(block)
        if rendered is not None:
            lines.append(rendered)
    return "\n".join(lines)

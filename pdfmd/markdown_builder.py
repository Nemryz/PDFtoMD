# I turn the blocks from one page into Markdown, with a page marker so I can
# find it later. The per type logic now lives in markdown_renderers.

from __future__ import annotations

from pdfmd.content_analyzer import Block
from pdfmd.markdown_renderers import render_blocks


def build_markdown(blocks: list[Block], page_number: int) -> str:
    # I keep this name as the public entry point, and delegate the rest.
    return render_blocks(blocks, page_number)

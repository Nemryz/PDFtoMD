"""Tests for markdown_builder module."""

from pdfmd.content_analyzer import Block
from pdfmd.markdown_builder import build_markdown


class TestBuildMarkdown:
    """Tests for build_markdown()."""

    def test_heading_becomes_h2(self):
        blocks = [Block(type="heading", text="DEMANDA JUDICIAL", confidence=0.95)]
        result = build_markdown(blocks, page_number=1)
        assert "## DEMANDA JUDICIAL" in result

    def test_paragraph_stays_plain(self):
        blocks = [Block(type="paragraph", text="Some text here", confidence=0.95)]
        result = build_markdown(blocks, page_number=1)
        assert "Some text here" in result

    def test_list_item_gets_bullet(self):
        blocks = [Block(type="list_item", text="1. First item", confidence=0.95)]
        result = build_markdown(blocks, page_number=1)
        assert "- First item" in result

    def test_page_number_filtered(self):
        blocks = [
            Block(type="page_number", text="5", confidence=0.95),
            Block(type="paragraph", text="Content", confidence=0.95),
        ]
        result = build_markdown(blocks, page_number=5)
        # The page number "5" should not appear as content, only in the comment
        lines = result.split("\n")
        content_lines = [l for l in lines if not l.startswith("<!--")]
        assert "5" not in "\n".join(content_lines)

    def test_page_comment_inserted(self):
        blocks = [Block(type="paragraph", text="Hello", confidence=0.95)]
        result = build_markdown(blocks, page_number=3)
        assert "<!-- Page 3 -->" in result

    def test_multiple_blocks(self):
        blocks = [
            Block(type="heading", text="TITLE", confidence=0.95),
            Block(type="paragraph", text="Body text here", confidence=0.95),
            Block(type="list_item", text="- Item one", confidence=0.95),
        ]
        result = build_markdown(blocks, page_number=1)
        assert "## TITLE" in result
        assert "Body text here" in result
        assert "- Item one" in result

    def test_empty_blocks(self):
        result = build_markdown([], page_number=1)
        assert "<!-- Page 1 -->" in result

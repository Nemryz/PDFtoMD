# Snapshot of the Markdown we produce today, so the renderer refactor cannot
# quietly change the output. If build_markdown changes, this test tells us.
import pytest

from pdfmd.content_analyzer import Block
from pdfmd.markdown_builder import build_markdown

SAMPLE = [
    Block(type="heading", text="SECCION PRINCIPAL", confidence=0.95),
    Block(type="paragraph", text="Primer parrafo de cuerpo.", confidence=0.9),
    Block(type="list_item", text="1. Primer elemento", confidence=0.9),
    Block(type="list_item", text="- Segundo elemento", confidence=0.9),
    Block(type="page_number", text="12", confidence=0.99),
    Block(type="paragraph", text="Segundo parrafo.", confidence=0.88),
]


class TestMarkdownSnapshot:
    def test_full_document_output_is_byte_identical(self):
        expected = "\n".join(
            [
                "<!-- Page 3 -->",
                "## SECCION PRINCIPAL",
                "Primer parrafo de cuerpo.",
                "- Primer elemento",
                "- Segundo elemento",
                "Segundo parrafo.",
            ]
        )
        assert build_markdown(SAMPLE, page_number=3) == expected

    def test_page_marker_is_always_first(self):
        for page in (1, 7, 140):
            first = build_markdown(SAMPLE, page_number=page).split("\n")[0]
            assert first == f"<!-- Page {page} -->"

    def test_page_numbers_never_reach_the_output(self):
        output = build_markdown(SAMPLE, page_number=3)
        body = "\n".join(line for line in output.split("\n") if not line.startswith("<!--"))
        assert "12" not in body

    def test_numeric_list_markers_are_stripped_from_the_bullet(self):
        blocks = [Block(type="list_item", text="1. Tercero", confidence=0.9)]
        assert "- Tercero" in build_markdown(blocks, page_number=1)

    def test_bullet_markers_are_stripped_from_the_bullet(self):
        blocks = [Block(type="list_item", text="• Tercero", confidence=0.9)]
        assert "- Tercero" in build_markdown(blocks, page_number=1)

    def test_lettered_markers_survive_today(self):
        # Known gap, not introduced here: content_analyzer treats "a) x" as a
        # list item but the sanitiser only strips digits and bullets, so the
        # letter marker stays in the text. Tracked separately as a fix.
        for raw in ("a) Tercero", "a. Tercero"):
            blocks = [Block(type="list_item", text=raw, confidence=0.9)]
            assert f"- {raw}" in build_markdown(blocks, page_number=1)

    def test_empty_block_list_still_emits_the_marker(self):
        assert build_markdown([], page_number=5) == "<!-- Page 5 -->"

    def test_unknown_type_falls_through_as_paragraph(self):
        # Today anything not page_number, heading or list_item is emitted raw.
        blocks = [Block(type="something_new", text="texto suelto", confidence=0.5)]
        assert "texto suelto" in build_markdown(blocks, page_number=1)

    @pytest.mark.parametrize("page", [1, 2, 50])
    def test_output_is_stable_across_pages(self, page):
        output = build_markdown(SAMPLE, page_number=page)
        assert output.startswith("<!-- Page ")
        assert output.endswith("Segundo parrafo.")

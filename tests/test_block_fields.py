# The extra fields on Block exist so detectors can attach geometry later.

from pdfmd import taxonomy
from pdfmd.content_analyzer import Block, analyze_page


class TestBlockDefaults:
    def test_constructor_still_takes_three_arguments(self):
        # Every existing call site passes exactly three, and must keep working.
        block = Block(type="paragraph", text="hola", confidence=0.9)
        assert block.type == "paragraph"
        assert block.text == "hola"
        assert block.confidence == 0.9

    def test_new_fields_default_to_neutral_values(self):
        block = Block(type="paragraph", text="hola", confidence=0.9)
        assert block.bbox is None
        assert block.level == 0
        assert block.source == "heuristic"

    def test_keyword_construction_works(self):
        block = Block(type=taxonomy.HEADING, text="Titulo", confidence=1.0, level=2)
        assert block.level == 2
        assert block.type == taxonomy.HEADING

    def test_bbox_accepts_a_four_tuple(self):
        box = (10, 20, 30, 40)
        block = Block(type="paragraph", text="x", confidence=0.5, bbox=box)
        assert block.bbox == box

    def test_equality_still_works_on_the_old_fields(self):
        a = Block(type="paragraph", text="x", confidence=0.5)
        b = Block(type="paragraph", text="x", confidence=0.5)
        assert a == b

    def test_blocks_with_different_geometry_are_not_equal(self):
        # Otherwise the registry could not tell two layouts apart.
        a = Block(type="paragraph", text="x", confidence=0.5, bbox=(0, 0, 1, 1))
        b = Block(type="paragraph", text="x", confidence=0.5, bbox=(5, 5, 6, 6))
        assert a != b


class TestAnalyzerOutput:
    def test_blocks_come_back_with_the_new_defaults(self):
        blocks = analyze_page("Un parrafo normal de texto.\n\notro", confidence=0.8)
        assert blocks
        for block in blocks:
            assert block.bbox is None
            assert block.level == 0
            assert block.source == "heuristic"

    def test_types_are_known_to_the_taxonomy(self):
        blocks = analyze_page("TITULO\n\n1. Elemento de lista\n\nCuerpo", confidence=0.8)
        for block in blocks:
            assert taxonomy.is_known(block.type), f"unknown type: {block.type}"

    def test_empty_input_still_returns_nothing(self):
        assert analyze_page("", confidence=0.9) == []
        assert analyze_page("   \n  \n", confidence=0.9) == []

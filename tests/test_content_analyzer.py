
from pdfmd.content_analyzer import (
    analyze_page,
    detect_header,
    detect_heading,
    detect_list_item,
    detect_page_number,
)


class TestDetectHeading:

    def test_all_caps_line_is_heading(self):
        assert detect_heading("DEMANDA JUDICIAL") is True

    def test_short_uppercase_with_colon(self):
        assert detect_heading("EXPEDIENTE: 12345") is True

    def test_long_line_not_heading(self):
        assert (
            detect_heading(
                "This is a very long paragraph that should not be detected as a heading at all"
            )
            is False
        )

    def test_empty_string(self):
        assert detect_heading("") is False

    def test_mixed_case_short(self):
        assert detect_heading("Artículo 1") is False


class TestDetectListItem:

    def test_bullet_item(self):
        assert detect_list_item("- First item") is True

    def test_numbered_item(self):
        assert detect_list_item("1. First item") is True

    def test_dash_item(self):
        assert detect_list_item("• Something") is True

    def test_plain_paragraph(self):
        assert detect_list_item("This is just a regular paragraph of text") is False

    def test_empty_string(self):
        assert detect_list_item("") is False


class TestDetectPageNumber:

    def test_standalone_number(self):
        assert detect_page_number("5") is True

    def test_page_prefix(self):
        assert detect_page_number("Página 5") is True

    def test_number_in_context(self):
        assert detect_page_number("Article 5 of the contract") is False

    def test_roman_numeral(self):
        assert detect_page_number("IV") is True

    def test_empty_string(self):
        assert detect_page_number("") is False


class TestDetectHeader:

    def test_repeated_header(self):
        assert detect_header("EXPEDIENTE JUDICIAL", page_num=5) is True

    def test_short_first_page(self):
        # First page headers are less common
        assert detect_header("Title", page_num=1) is False

    def test_long_text_not_header(self):
        assert (
            detect_header("This is a very long text that is definitely not a header", page_num=3)
            is False
        )


class TestAnalyzePage:

    def test_returns_list_of_blocks(self):
        result = analyze_page("Hello world", 0.95)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_heading_detected(self):
        result = analyze_page("DEMANDA JUDICIAL", 0.95)
        types = [b.type for b in result]
        assert "heading" in types

    def test_paragraph_detected(self):
        result = analyze_page(
            "This is a regular paragraph of text that should be detected as such", 0.95
        )
        types = [b.type for b in result]
        assert "paragraph" in types

    def test_empty_page(self):
        result = analyze_page("", 0.0)
        assert result == []

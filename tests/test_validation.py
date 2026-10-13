
import tempfile
from pathlib import Path

from pdfmd.validation import (
    validate_duplicate_paragraphs,
    validate_encoding,
    validate_header_hierarchy,
    validate_image_refs,
    validate_line_length,
    validate_metadata_consistency,
    validate_output,
    validate_page_markers,
    validate_signature_placeholders,
    validate_table_format,
)


class TestValidateEncoding:
    def test_valid_utf8(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            md = Path(tmpdir) / "doc.md"
            md.write_text("Contenido válido con ñ y acentos.\n", encoding="utf-8")
            errors = validate_encoding(str(md))
            assert errors == []

    def test_invalid_encoding(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            md = Path(tmpdir) / "doc.md"
            md.write_bytes(b"Normal text\n")
            # Write a byte that's invalid UTF-8
            with open(md, "ab") as f:
                f.write(b"\xff\xfe")
            errors = validate_encoding(str(md))
            assert len(errors) > 0
            assert "encoding" in errors[0].lower()


class TestValidateImageRefs:
    def test_no_images(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            md = Path(tmpdir) / "doc.md"
            md.write_text("No images here.\n", encoding="utf-8")
            errors = validate_image_refs(str(md), tmpdir)
            assert errors == []

    def test_valid_image_ref(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            md = Path(tmpdir) / "doc.md"
            img_dir = Path(tmpdir) / "images"
            img_dir.mkdir()
            (img_dir / "img_001.png").write_bytes(b"\x89PNG")
            md.write_text("See image: ![fig](images/img_001.png)\n", encoding="utf-8")
            errors = validate_image_refs(str(md), tmpdir)
            assert errors == []

    def test_missing_image_ref(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            md = Path(tmpdir) / "doc.md"
            md.write_text("![missing](images/no_such.png)\n", encoding="utf-8")
            errors = validate_image_refs(str(md), tmpdir)
            assert len(errors) > 0
            assert "missing" in errors[0].lower() or "image" in errors[0].lower()


class TestValidateDuplicateParagraphs:
    def test_no_duplicates(self):
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph.\n"
        errors = validate_duplicate_paragraphs(text)
        assert errors == []

    def test_consecutive_duplicates(self):
        text = "Same paragraph.\n\nSame paragraph.\n\nDifferent.\n"
        errors = validate_duplicate_paragraphs(text)
        assert len(errors) > 0
        assert "duplicate" in errors[0].lower()


class TestValidateHeaderHierarchy:
    def test_valid_hierarchy(self):
        text = "# Title\n\n## Section\n\n### Subsection\n"
        errors = validate_header_hierarchy(text)
        assert errors == []

    def test_skipped_level(self):
        text = "# Title\n\n### Skipped H2\n"
        errors = validate_header_hierarchy(text)
        assert len(errors) > 0
        assert "header" in errors[0].lower() or "hierarchy" in errors[0].lower()


class TestValidateTableFormat:
    def test_valid_table(self):
        text = "| A | B |\n|---|---|\n| 1 | 2 |\n"
        errors = validate_table_format(text)
        assert errors == []

    def test_invalid_table(self):
        text = "| A | B\n|---\n| 1\n"
        errors = validate_table_format(text)
        assert len(errors) > 0


class TestValidatePageMarkers:
    def test_sequential_markers(self):
        text = "<!-- Page 1 -->\ntext\n<!-- Page 2 -->\ntext\n<!-- Page 3 -->\n"
        errors = validate_page_markers(text)
        assert errors == []

    def test_out_of_order_markers(self):
        text = "<!-- Page 1 -->\ntext\n<!-- Page 3 -->\ntext\n<!-- Page 2 -->\n"
        errors = validate_page_markers(text)
        assert len(errors) > 0
        assert "order" in errors[0].lower() or "sequence" in errors[0].lower()

    def test_no_markers(self):
        text = "Just text, no markers.\n"
        errors = validate_page_markers(text)
        assert errors == []  # No markers = no error (just absence)


class TestValidateLineLength:
    def test_short_lines(self):
        text = "Short line.\nAnother short line.\n"
        errors = validate_line_length(text, max_length=200)
        assert errors == []

    def test_long_line(self):
        text = "x" * 250 + "\n"
        errors = validate_line_length(text, max_length=200)
        assert len(errors) > 0
        assert "line" in errors[0].lower() or "length" in errors[0].lower()

    def test_long_line_in_table_ignored(self):
        text = "| " + "x" * 250 + " |\n"
        errors = validate_line_length(text, max_length=200)
        assert errors == []


class TestValidateMetadataConsistency:
    def test_consistent_metadata(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            md = Path(tmpdir) / "doc.md"
            md.write_text("text\n<!-- Page 1 -->\ntext\n<!-- Page 2 -->\n", encoding="utf-8")
            meta = {"total_pages": 2}
            errors = validate_metadata_consistency(str(md), meta)
            assert errors == []

    def test_page_count_mismatch(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            md = Path(tmpdir) / "doc.md"
            md.write_text("text\n<!-- Page 1 -->\ntext\n<!-- Page 2 -->\n", encoding="utf-8")
            meta = {"total_pages": 5}
            errors = validate_metadata_consistency(str(md), meta)
            assert len(errors) > 0
            assert "page" in errors[0].lower()


class TestValidateSignaturePlaceholders:
    def test_signatures_detected_with_markers(self):
        text = "text\n<!-- SIGNATURE: Juan Perez -->\nmore text\n"
        errors = validate_signature_placeholders(text, signatures_detected=True)
        assert errors == []

    def test_signatures_detected_without_markers(self):
        text = "text without signature markers\n"
        errors = validate_signature_placeholders(text, signatures_detected=True)
        assert len(errors) > 0
        assert "signature" in errors[0].lower()

    def test_no_signatures_no_markers(self):
        text = "text without signatures\n"
        errors = validate_signature_placeholders(text, signatures_detected=False)
        assert errors == []


class TestValidateOutput:

    def test_valid_output_passes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            md = Path(tmpdir) / "document.md"
            md.write_text("# Title\n\nSome content here.\n\n<!-- Page 1 -->\n", encoding="utf-8")
            result = validate_output(tmpdir)
            assert result["valid"] is True
            assert len(result["errors"]) == 0

    def test_missing_markdown_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = validate_output(tmpdir)
            assert result["valid"] is False
            assert any("markdown" in e.lower() for e in result["errors"])

    def test_empty_markdown_warns(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            md = Path(tmpdir) / "document.md"
            md.write_text("", encoding="utf-8")
            result = validate_output(tmpdir)
            assert any("empty" in w.lower() for w in result["warnings"])

    def test_page_comments_present(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            md = Path(tmpdir) / "document.md"
            md.write_text("<!-- Page 1 -->\nText\n<!-- Page 2 -->\nMore text\n", encoding="utf-8")
            result = validate_output(tmpdir)
            assert result.get("page_markers_found", 0) >= 2

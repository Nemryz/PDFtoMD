# I check the output after a conversion and report what's off.

from __future__ import annotations

import re
from pathlib import Path


def validate_output(output_dir: str) -> dict:
    # I look at a whole output directory and collect every problem I find.
    errors: list[str] = []
    warnings: list[str] = []
    page_markers = 0

    out = Path(output_dir)

    # The Markdown is the only file I really need.
    md_files = list(out.glob("*.md"))
    if not md_files:
        errors.append("No Markdown file found in output directory")
        return {"valid": False, "errors": errors, "warnings": warnings, "page_markers_found": 0}

    md_path = md_files[0]
    content = md_path.read_text(encoding="utf-8")

    # An empty file means the conversion produced nothing.
    if not content.strip():
        warnings.append(f"Markdown file is empty: {md_path.name}")

    # Page markers are how I count pages without re-reading the PDF.
    page_markers = len(re.findall(r"<!-- Page \d+ -->", content))
    if page_markers == 0:
        warnings.append("No page markers found in Markdown")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "page_markers_found": page_markers,
    }


def validate_encoding(file_path: str) -> list[str]:
    # Broken encodings show up as mojibake later, so I check here.
    errors: list[str] = []
    try:
        Path(file_path).read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        errors.append(f"Invalid UTF-8 encoding: {e}")
    return errors


def validate_image_refs(file_path: str, output_dir: str) -> list[str]:
    # A missing image is worse than a broken one, since the Markdown won't render.
    errors: list[str] = []
    content = Path(file_path).read_text(encoding="utf-8")
    out = Path(output_dir)

    # I match the inline image syntax to find the references.
    for match in re.finditer(r"!\[.*?\]\((.*?)\)", content):
        ref = match.group(1)
        # Paths are relative to the output directory, which is how Markdown resolves them.
        img_path = out / ref
        if not img_path.exists():
            errors.append(f"Missing image reference: {ref}")
    return errors


def validate_duplicate_paragraphs(text: str) -> list[str]:
    # The same paragraph twice running usually means a duplicated page.
    errors: list[str] = []
    paragraphs = re.split(r"\n\s*\n", text)

    for i in range(1, len(paragraphs)):
        prev = paragraphs[i - 1].strip()
        curr = paragraphs[i].strip()
        if prev and curr and prev == curr:
            preview = prev[:60] + ("..." if len(prev) > 60 else "")
            errors.append(f"Duplicate paragraph: '{preview}'")
    return errors


def validate_header_hierarchy(text: str) -> list[str]:
    # Skipping from H2 to H4 breaks most Markdown renderers, so I flag it.
    errors: list[str] = []
    last_level = 0

    for line in text.split("\n"):
        match = re.match(r"^(#{1,6})\s", line.strip())
        if match:
            level = len(match.group(1))
            if last_level > 0 and level > last_level + 1:
                errors.append(f"Header level skipped: H{last_level} followed by H{level}")
            last_level = level
    return errors


def validate_table_format(text: str) -> list[str]:
    # A table needs its pipes lined up, or it renders as plain text.
    errors: list[str] = []
    in_table = False
    expected_cols = 0

    for i, line in enumerate(text.split("\n"), 1):
        stripped = line.strip()
        if stripped.startswith("|"):
            cols = len([c for c in stripped.split("|") if c.strip()])
            if not in_table:
                in_table = True
                expected_cols = cols
            elif re.match(r"^\|[\s\-:|]+\|$", stripped):
                pass  # Separator row — skip
            else:
                if cols != expected_cols:
                    errors.append(f"Table row {i}: expected {expected_cols} columns, got {cols}")
        else:
            in_table = False
            expected_cols = 0
    return errors


def validate_page_markers(text: str) -> list[str]:
    # Markers should count up from one without gaps.
    errors: list[str] = []
    markers = re.findall(r"<!-- Page (\d+) -->", text)

    if len(markers) < 2:
        return errors

    prev_num = int(markers[0])
    for i in range(1, len(markers)):
        curr_num = int(markers[i])
        if curr_num != prev_num + 1:
            errors.append(f"Page markers out of order: Page {prev_num} followed by Page {curr_num}")
        prev_num = curr_num
    return errors


def validate_line_length(text: str, max_length: int = 200) -> list[str]:
    # Very long lines are hard to read, though tables are exempt.
    errors: list[str] = []
    for i, line in enumerate(text.split("\n"), 1):
        # Tables are allowed to run long, that's what they do.
        if line.strip().startswith("|"):
            continue
        if len(line) > max_length:
            errors.append(f"Line {i} exceeds {max_length} chars ({len(line)} chars)")
    return errors


def validate_metadata_consistency(file_path: str, metadata: dict) -> list[str]:
    # The metadata count and the markers should agree, otherwise I lost or duplicated a page.
    errors: list[str] = []
    content = Path(file_path).read_text(encoding="utf-8")
    marker_count = len(re.findall(r"<!-- Page \d+ -->", content))

    meta_pages = metadata.get("total_pages", 0)
    if meta_pages > 0 and marker_count > 0 and meta_pages != marker_count:
        errors.append(
            f"Page count mismatch: metadata says {meta_pages}, Markdown has {marker_count} markers"
        )
    return errors


def validate_signature_placeholders(text: str, signatures_detected: bool = False) -> list[str]:
    # A detected signature with no placeholder in the text means the writer dropped it.
    errors: list[str] = []
    if signatures_detected:
        has_markers = bool(re.search(r"<!-- SIGNATURE:.*?-->", text))
        if not has_markers:
            errors.append("Signatures detected but no signature placeholders found in Markdown")
    return errors

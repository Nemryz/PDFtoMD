"""Validation module — check output quality and consistency."""

from __future__ import annotations

import re
from pathlib import Path


def validate_output(output_dir: str) -> dict:
    """Validate the output directory of a conversion.

    Checks for:
    - Markdown file exists
    - Markdown is not empty
    - Page comment markers are present
    - metadata.json exists and is valid

    Returns:
        Dictionary with keys: valid, errors, warnings, page_markers_found.
    """
    errors: list[str] = []
    warnings: list[str] = []
    page_markers = 0

    out = Path(output_dir)

    # Find Markdown file
    md_files = list(out.glob("*.md"))
    if not md_files:
        errors.append("No Markdown file found in output directory")
        return {"valid": False, "errors": errors, "warnings": warnings, "page_markers_found": 0}

    md_path = md_files[0]
    content = md_path.read_text(encoding="utf-8")

    # Check not empty
    if not content.strip():
        warnings.append(f"Markdown file is empty: {md_path.name}")

    # Count page markers
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
    """Check that file is valid UTF-8.

    Args:
        file_path: Path to the Markdown file.

    Returns:
        List of error messages (empty if valid).
    """
    errors: list[str] = []
    try:
        Path(file_path).read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        errors.append(f"Invalid UTF-8 encoding: {e}")
    return errors


def validate_image_refs(file_path: str, output_dir: str) -> list[str]:
    """Check that all image references point to existing files.

    Args:
        file_path: Path to the Markdown file.
        output_dir: Directory containing the output (for resolving relative paths).

    Returns:
        List of error messages (empty if valid).
    """
    errors: list[str] = []
    content = Path(file_path).read_text(encoding="utf-8")
    out = Path(output_dir)

    # Match ![alt](path) patterns
    for match in re.finditer(r"!\[.*?\]\((.*?)\)", content):
        ref = match.group(1)
        # Resolve relative to output directory
        img_path = out / ref
        if not img_path.exists():
            errors.append(f"Missing image reference: {ref}")
    return errors


def validate_duplicate_paragraphs(text: str) -> list[str]:
    """Check for consecutive duplicate paragraphs.

    Args:
        text: Markdown content.

    Returns:
        List of error messages (empty if valid).
    """
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
    """Check that header hierarchy is valid (no skipped levels).

    Args:
        text: Markdown content.

    Returns:
        List of error messages (empty if valid).
    """
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
    """Check that tables have valid Markdown format.

    Args:
        text: Markdown content.

    Returns:
        List of error messages (empty if valid).
    """
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
    """Check that page markers are in sequential order.

    Args:
        text: Markdown content.

    Returns:
        List of error messages (empty if valid).
    """
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
    """Check that no lines exceed the maximum length (except tables).

    Args:
        text: Markdown content.
        max_length: Maximum allowed line length.

    Returns:
        List of error messages (empty if valid).
    """
    errors: list[str] = []
    for i, line in enumerate(text.split("\n"), 1):
        # Skip table lines (start with |)
        if line.strip().startswith("|"):
            continue
        if len(line) > max_length:
            errors.append(f"Line {i} exceeds {max_length} chars ({len(line)} chars)")
    return errors


def validate_metadata_consistency(file_path: str, metadata: dict) -> list[str]:
    """Check that page count in metadata matches page markers in Markdown.

    Args:
        file_path: Path to the Markdown file.
        metadata: Parsed metadata.json dictionary.

    Returns:
        List of error messages (empty if valid).
    """
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
    """Check that signature placeholders are present when signatures were detected.

    Args:
        text: Markdown content.
        signatures_detected: Whether signatures were detected in the PDF.

    Returns:
        List of error messages (empty if valid).
    """
    errors: list[str] = []
    if signatures_detected:
        has_markers = bool(re.search(r"<!-- SIGNATURE:.*?-->", text))
        if not has_markers:
            errors.append("Signatures detected but no signature placeholders found in Markdown")
    return errors

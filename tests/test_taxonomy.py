# Every block type the pipeline produces must exist in the taxonomy.

import re
from pathlib import Path

import pytest

from pdfmd import taxonomy

PDFMD = Path(__file__).parent.parent / "pdfmd"

# I pull the type strings straight out of the source so the test breaks the
# moment someone constructs a Block with a type the taxonomy never heard of.
PATTERNS = (
    re.compile(r"Block\(\s*type\s*=\s*\"([a-z_]+)\""),
    re.compile(r"\.type\s*==\s*\"([a-z_]+)\""),
    re.compile(r"\.type\s*!=\s*\"([a-z_]+)\""),
)


def _types_used_in_source() -> set[str]:
    found: set[str] = set()
    for path in PDFMD.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for pattern in PATTERNS:
            found.update(pattern.findall(text))
    return found


class TestTaxonomyCoversSource:
    def test_every_type_used_in_source_is_known(self):
        used = _types_used_in_source()
        unknown = {t for t in used if not taxonomy.is_known(t)}
        assert not unknown, f"types missing from taxonomy: {sorted(unknown)}"

    def test_source_really_uses_types(self):
        # Guards against the test passing because the patterns stopped matching.
        assert _types_used_in_source() >= {"heading", "paragraph", "list_item", "page_number"}

    @pytest.mark.parametrize("block_type", sorted(taxonomy.ALL))
    def test_all_entries_are_plain_strings(self, block_type):
        assert isinstance(block_type, str)
        assert block_type == block_type.strip().lower()


class TestAliases:
    @pytest.mark.parametrize(
        ("upstream", "expected"),
        [
            ("paragraph_title", taxonomy.HEADING),
            ("SectionHeader", taxonomy.HEADING),
            ("doc_title", taxonomy.TITLE),
            ("display_formula", taxonomy.FORMULA),
            ("Equation", taxonomy.FORMULA),
            ("reference_content", taxonomy.REFERENCE),
            ("Bibliography", taxonomy.REFERENCE),
            ("vertical_text", taxonomy.VERSE),
            ("TableOfContents", taxonomy.LIST_OF_CONTENTS),
            ("number", taxonomy.PAGE_NUMBER),
        ],
    )
    def test_upstream_labels_resolve(self, upstream, expected):
        assert taxonomy.resolve(upstream) == expected

    def test_unknown_label_falls_back_to_paragraph(self):
        assert taxonomy.resolve("something_we_never_defined") == taxonomy.PARAGRAPH

    def test_our_own_labels_pass_through(self):
        for block_type in taxonomy.ALL:
            assert taxonomy.resolve(block_type) == block_type

    def test_alias_targets_are_all_valid(self):
        # An alias pointing at a type we never defined would render nothing.
        for target in taxonomy.ALIASES.values():
            assert target in taxonomy.ALL, f"alias points at unknown type: {target}"


class TestSetIntegrity:
    def test_skip_types_exist_in_all(self):
        assert taxonomy.SKIP <= taxonomy.ALL

    def test_no_duplicate_alias_targets_are_unresolvable(self):
        assert all(taxonomy.is_known(v) for v in taxonomy.ALIASES.values())

    def test_all_is_a_frozenset(self):
        assert isinstance(taxonomy.ALL, frozenset)

    def test_resolve_is_total(self):
        # Whatever arrives, resolve returns something renderable.
        for candidate in list(taxonomy.ALL) + list(taxonomy.ALIASES) + ["", "  "]:
            assert taxonomy.resolve(candidate) in taxonomy.ALL

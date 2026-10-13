# One vocabulary for block types, so detectors and renderers stop disagreeing.

from __future__ import annotations

# The types the pipeline emits today.
PARAGRAPH = "paragraph"
HEADING = "heading"
LIST_ITEM = "list_item"
PAGE_NUMBER = "page_number"

# Page furniture.
TITLE = "title"
HEADER = "header"
FOOTER = "footer"

# Graphics.
FIGURE = "figure"
TABLE = "table"
IMAGE = "image"
CAPTION = "caption"

# Marks that matter for legal and scientific work.
SEAL = "seal"
SIGNATURE = "signature"
HIGHLIGHT = "highlight"

# Academic.
ABSTRACT = "abstract"
FORMULA = "formula"
REFERENCE = "reference"

# Long form reading.
VERSE = "verse"
BLOCKQUOTE = "blockquote"
CODE = "code"
LIST_OF_CONTENTS = "list_of_contents"

ALL: frozenset[str] = frozenset(
    {
        PARAGRAPH, HEADING, LIST_ITEM, PAGE_NUMBER,
        TITLE, HEADER, FOOTER,
        FIGURE, TABLE, IMAGE, CAPTION,
        SEAL, SIGNATURE, HIGHLIGHT,
        ABSTRACT, FORMULA, REFERENCE,
        VERSE, BLOCKQUOTE, CODE, LIST_OF_CONTENTS,
    }
)

# Types we never render, because they carry no text worth keeping.
SKIP: frozenset[str] = frozenset({PAGE_NUMBER})

# Paddle and Surya name things differently, so I map both vocabularies
# onto ours so a detector can report either and the renderer still understands.
ALIASES: dict[str, str] = {
    # From the Paddle layout classes.
    "doc_title": TITLE,
    "paragraph_title": HEADING,
    "figure_title": CAPTION,
    "vision_footnote": CAPTION,
    "inline_formula": FORMULA,
    "display_formula": FORMULA,
    "formula_number": FORMULA,
    "reference_content": REFERENCE,
    "number": PAGE_NUMBER,
    "content": LIST_OF_CONTENTS,
    "chart": FIGURE,
    "algorithm": CODE,
    "chemical_block": FORMULA,
    "aside_text": BLOCKQUOTE,
    "vertical_text": VERSE,
    # Surya
    "SectionHeader": HEADING,
    "PageHeader": HEADER,
    "PageFooter": FOOTER,
    "Caption": CAPTION,
    "Footnote": BLOCKQUOTE,
    "Equation": FORMULA,
    "Picture": IMAGE,
    "Diagram": FIGURE,
    "Bibliography": REFERENCE,
    "TableOfContents": LIST_OF_CONTENTS,
    "ListGroup": LIST_ITEM,
    "Form": TABLE,
    "BlankPage": PAGE_NUMBER,
}


def resolve(raw: str) -> str:
    """I map an upstream label onto ours, falling back to paragraph."""
    return ALIASES.get(raw, raw if raw in ALL else PARAGRAPH)


def is_known(raw: str) -> bool:
    """I report whether a label is ours or one of the aliases we accept."""
    return raw in ALL or raw in ALIASES

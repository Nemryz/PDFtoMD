# I pull embedded images out of the PDF and drop the duplicates.

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from pymupdf import Document


@dataclass
class ExtractedImage:
    # One image, still in memory, with the page it came from.

    data: bytes
    page: int  # 1-based page number
    index: int  # Image index on the page
    width: int
    height: int
    hash: str = ""

    def __post_init__(self) -> None:
        if not self.hash:
            self.hash = hashlib.sha256(self.data).hexdigest()[:16]


@dataclass
class SavedImage:
    # Same image, now on disk with a real path.

    path: str
    page: int
    index: int
    hash: str


def extract_images(doc: Document, pages: list[int] | None = None) -> list[ExtractedImage]:
    # I walk every page's image list and decode each one through PyMuPDF.
    images: list[ExtractedImage] = []

    if pages is None:
        pages = list(range(doc.page_count))

    for page_idx in pages:
        if page_idx >= doc.page_count:
            continue

        page = doc[page_idx]
        image_list = page.get_images(full=True)

        for img_idx, img_info in enumerate(image_list):
            xref = img_info[0]
            try:
                base_image = doc.extract_image(xref)
                if base_image:
                    images.append(
                        ExtractedImage(
                            data=base_image["image"],
                            page=page_idx + 1,
                            index=img_idx,
                            width=base_image.get("width", 0),
                            height=base_image.get("height", 0),
                        )
                    )
            except Exception:
                continue

    return images


def deduplicate(images: list[ExtractedImage]) -> list[ExtractedImage]:
    # The same logo on 200 pages is one file, so I compare content hashes.
    seen_hashes: set[str] = set()
    unique: list[ExtractedImage] = []

    for img in images:
        if img.hash not in seen_hashes:
            seen_hashes.add(img.hash)
            unique.append(img)

    return unique


def save_images(images: list[ExtractedImage], output_dir: str) -> list[SavedImage]:
    # I write the bytes and report what landed on disk.
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    saved: list[SavedImage] = []

    for img in images:
        # The extension comes from the bytes themselves, not the extension PDF claims.
        ext = "png"
        if img.data[:3] == b"\xff\xd8\xff":
            ext = "jpg"
        elif img.data[:4] == b"GIF8":
            ext = "gif"

        filename = f"page-{img.page:03d}-image-{img.index:03d}.{ext}"
        filepath = out / filename
        filepath.write_bytes(img.data)

        saved.append(
            SavedImage(
                path=str(filepath),
                page=img.page,
                index=img.index,
                hash=img.hash,
            )
        )

    return saved

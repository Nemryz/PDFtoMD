"""OCR engine — Tesseract wrapper for image-to-text conversion."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytesseract
from PIL import Image

from pdfmd.exceptions import TesseractLanguageError, TesseractNotFoundError

_TESSERACT_INITIALIZED = False


def initialize_tesseract(tesseract_path: str | None = None, lang: str = "spa") -> None:
    """Verify Tesseract is available and the requested language is installed.

    Raises:
        TesseractNotFoundError: If Tesseract binary is not found.
        TesseractLanguageError: If the requested language pack is missing.
    """
    global _TESSERACT_INITIALIZED

    if tesseract_path:
        pytesseract.pytesseract.tesseract_cmd = tesseract_path

    # Verify binary exists — check both PATH and common install locations
    cmd = pytesseract.pytesseract.tesseract_cmd
    if not shutil.which(cmd):
        # On Windows, check common install locations
        import platform

        if platform.system() == "Windows":
            common_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            ]
            for p in common_paths:
                if Path(p).exists():
                    pytesseract.pytesseract.tesseract_cmd = p
                    break
            else:
                raise TesseractNotFoundError(cmd)
        else:
            raise TesseractNotFoundError(cmd)

    # Verify language is available
    try:
        available_langs = pytesseract.get_languages()
    except Exception:
        available_langs = []

    if lang not in available_langs and lang != "eng":
        raise TesseractLanguageError(lang)

    _TESSERACT_INITIALIZED = True


def ocr_image(image: Image.Image, lang: str = "spa", config: str = "") -> str:
    """Run OCR on a PIL Image and return extracted text.

    Args:
        image: PIL Image to OCR.
        lang: Tesseract language code (default: spa for Spanish).
        config: Optional Tesseract config string (e.g. "--psm 6").

    Returns:
        Extracted text string (may be empty for blank images).
    """
    text = pytesseract.image_to_string(image, lang=lang, config=config)
    return text.strip()


def get_confidence(image: Image.Image, lang: str = "spa") -> float:
    """Get the average OCR confidence score for an image.

    Returns:
        Float between 0.0 (no confidence) and 1.0 (full confidence).
    """
    data = pytesseract.image_to_data(image, lang=lang, output_type=pytesseract.Output.DICT)

    confidences = [int(c) for c in data["conf"] if int(c) > 0]
    if not confidences:
        return 0.0

    avg = sum(confidences) / len(confidences)
    return avg / 100.0  # Normalize to 0.0–1.0


def ocr_with_confidence(
    image: Image.Image,
    lang: str = "spa",
    config: str = "",
) -> tuple[str, float]:
    """Run OCR once, returning both extracted text and average confidence.

    Single-pass alternative to calling ocr_image() + get_confidence()
    separately, which runs Tesseract twice per page. Uses one
    pytesseract.image_to_data() call and reconstructs the text from
    word tokens (US-1: eliminate double-OCR).

    Args:
        image: PIL Image to OCR.
        lang: Tesseract language code (default: spa for Spanish).
        config: Optional Tesseract config string (e.g. "--psm 6").

    Returns:
        Tuple of (extracted text, average confidence between 0.0 and 1.0).
    """
    data = pytesseract.image_to_data(
        image, lang=lang, config=config, output_type=pytesseract.Output.DICT
    )

    words_by_line: dict[tuple[int, ...], list[str]] = {}
    confidences: list[int] = []

    entries = len(data["text"])
    for idx in range(entries):
        conf = int(float(data["conf"][idx]))
        if conf > 0:
            confidences.append(conf)

        word = str(data["text"][idx]).strip()
        if word:
            key = (
                data["block_num"][idx],
                data["par_num"][idx],
                data["line_num"][idx],
            )
            words_by_line.setdefault(key, []).append(word)

    lines = [" ".join(words) for words in words_by_line.values()]
    text = "\n".join(lines).strip()

    avg_conf = sum(confidences) / len(confidences) / 100.0 if confidences else 0.0
    return text, avg_conf

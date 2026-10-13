# The Tesseract wrapper: everything that touches pytesseract lives in this one file.

from __future__ import annotations

import shutil
from pathlib import Path

import pytesseract
from PIL import Image

from pdfmd.exceptions import TesseractLanguageError, TesseractNotFoundError

_TESSERACT_INITIALIZED = False


def initialize_tesseract(tesseract_path: str | None = None, lang: str = "spa") -> None:
    # I check the binary and the language pack before anyone tries to use them.
    global _TESSERACT_INITIALIZED

    if tesseract_path:
        pytesseract.pytesseract.tesseract_cmd = tesseract_path

    # PATH first, because that's where a normal install lands.
    cmd = pytesseract.pytesseract.tesseract_cmd
    if not shutil.which(cmd):
        # On Windows the installer doesn't always add itself to PATH, so I look in the usual places.
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

    # An empty language list means get_languages failed, so I only check when I can.
    try:
        available_langs = pytesseract.get_languages()
    except Exception:
        available_langs = []

    if lang not in available_langs and lang != "eng":
        raise TesseractLanguageError(lang)

    _TESSERACT_INITIALIZED = True


def ocr_image(image: Image.Image, lang: str = "spa", config: str = "") -> str:
    # Straight image_to_string, used when I only need the text.
    text = pytesseract.image_to_string(image, lang=lang, config=config)
    return text.strip()


def get_confidence(image: Image.Image, lang: str = "spa") -> float:
    # Confidence on its own, which costs a second Tesseract run.
    data = pytesseract.image_to_data(image, lang=lang, output_type=pytesseract.Output.DICT)

    confidences = [int(c) for c in data["conf"] if int(c) > 0]
    if not confidences:
        return 0.0

    avg = sum(confidences) / len(confidences)
    return avg / 100.0  # Normalize to the range zero to one.


def ocr_with_confidence(
    image: Image.Image,
    lang: str = "spa",
    config: str = "",
) -> tuple[str, float]:
    # The one I use: text and confidence in a single pass, since two passes cost half the runtime.
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

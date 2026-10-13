"""Quality metrics — measure text quality of converted Markdown."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass


@dataclass
class QualityReport:
    """Report of text quality metrics."""

    words: int
    broken_sentences: int
    broken_connectors: int
    duplicate_lines: int
    noise_patterns: int
    headers_detected: int
    tables_detected: int
    lists_detected: int
    avg_line_length: float

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


_CONNECTORS = frozenset(
    {
        "de",
        "la",
        "el",
        "en",
        "que",
        "por",
        "con",
        "para",
        "los",
        "las",
        "del",
        "un",
        "una",
        "se",
        "al",
    }
)


def measure_text_quality(text: str) -> QualityReport:
    """Measure quality metrics for extracted text.

    Args:
        text: Extracted Markdown text.

    Returns:
        QualityReport with all metric values.
    """
    if not text:
        return QualityReport(
            words=0,
            broken_sentences=0,
            broken_connectors=0,
            duplicate_lines=0,
            noise_patterns=0,
            headers_detected=0,
            tables_detected=0,
            lists_detected=0,
            avg_line_length=0.0,
        )

    lines = text.split("\n")
    words = text.split()

    broken_sentences = _count_broken_sentences(lines)
    broken_connectors = _count_broken_connectors(lines)
    duplicate_lines = _count_duplicate_lines(lines)
    noise_patterns = _count_noise_patterns(lines)
    headers_detected = sum(1 for line in lines if re.match(r"^#{1,6}\s", line.strip()))
    tables_detected = sum(1 for line in lines if "|" in line and line.strip().startswith("|"))
    lists_detected = sum(
        1 for line in lines if re.match(r"^\s*[-*•]\s", line) or re.match(r"^\s*\d+\.\s", line)
    )

    non_empty = [line for line in lines if line.strip()]
    avg_line_length = sum(len(line) for line in non_empty) / len(non_empty) if non_empty else 0.0

    return QualityReport(
        words=len(words),
        broken_sentences=broken_sentences,
        broken_connectors=broken_connectors,
        duplicate_lines=duplicate_lines,
        noise_patterns=noise_patterns,
        headers_detected=headers_detected,
        tables_detected=tables_detected,
        lists_detected=lists_detected,
        avg_line_length=round(avg_line_length, 1),
    )


def quality_score(report: QualityReport) -> float:
    """Compute a weighted quality score (0-100).

    Args:
        report: QualityReport to score.

    Returns:
        Score from 0 (worst) to 100 (perfect).
    """
    if report.words == 0:
        return 100.0

    total_words = max(report.words, 1)

    # Penalty weights (per occurrence, normalized by word count)
    penalties = (
        report.broken_sentences * 2.0
        + report.broken_connectors * 3.0
        + report.duplicate_lines * 1.5
        + report.noise_patterns * 1.0
    )

    # Normalize penalties relative to text size
    normalized = (penalties / total_words) * 100

    # Clamp to 0-100
    score = max(0.0, min(100.0, 100.0 - normalized))
    return round(score, 1)


def _count_broken_sentences(lines: list[str]) -> int:
    """Count lines ending in lowercase vowel without punctuation, followed by content."""
    count = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if (
            stripped
            and stripped[-1] in "aeiouáéíóúñ"
            and (i + 1 < len(lines) and lines[i + 1].strip())
        ):
            count += 1
    return count


def _count_broken_connectors(lines: list[str]) -> int:
    """Count connector words split across lines."""
    count = 0
    for i, line in enumerate(lines):
        stripped = line.strip().lower()
        if stripped in _CONNECTORS and i + 1 < len(lines) and lines[i + 1].strip():
            count += 1
    return count


def _count_duplicate_lines(lines: list[str]) -> int:
    """Count consecutive identical non-empty lines."""
    count = 0
    for i in range(1, len(lines)):
        if lines[i].strip() and lines[i].strip() == lines[i - 1].strip():
            count += 1
    return count


def _count_noise_patterns(lines: list[str]) -> int:
    """Count OCR noise artifacts (single-char lines, garbage patterns)."""
    count = 0
    for line in lines:
        stripped = line.strip()
        # Single uppercase letter on its own line
        if re.match(r"^[A-Z]\s*$", stripped):
            count += 1
        # Lines with mostly non-word characters (garbage)
        elif stripped and re.search(r"[^\w\s.,;:!?¿¡\"'()\[\]{}\-–—/\\|@#$%&*+=<>]", stripped):
            count += 1
    return count

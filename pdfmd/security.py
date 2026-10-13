# Input checks and resource limits, so a bad file can't take the process down.

from __future__ import annotations

import os


def validate_path(path: str) -> bool:
    # I reject anything that tries to climb out of its directory or smuggle a null byte.
    if not path:
        return False

    # A null byte truncates the path in some C layers, so I never pass one through.
    if "\x00" in path:
        return False

    # Normalising first collapses ../ and makes the check meaningful.
    normalized = os.path.normpath(path)
    parts = normalized.split(os.sep)

    # Any '..' segment at all is refused.
    if ".." in parts:
        return False

    # Same idea, phrased for the user/../etc shape rather than a bare '..'.
    if ".." in path.replace("\\", "/").split("/"):
        return False

    return True


def check_page_limit(current: int, max_pages: int) -> bool:
    # I compare pages done against pages allowed, and zero means no limit.
    if max_pages <= 0:
        return True
    return current < max_pages


def check_memory_limit(peak_mb: float, max_mb: float) -> bool:
    # Same idea against a megabyte ceiling, zero meaning unlimited.
    if max_mb <= 0:
        return True
    return peak_mb < max_mb

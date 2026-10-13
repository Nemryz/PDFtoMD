"""Security module — input validation and resource limits."""

from __future__ import annotations

import os


def validate_path(path: str) -> bool:
    """Validate that a file path is safe (no traversal, no null bytes).

    Args:
        path: File path to validate.

    Returns:
        True if path is safe, False if it contains traversal or injection.
    """
    if not path:
        return False

    # Reject null bytes
    if "\x00" in path:
        return False

    # Normalize and check for traversal
    normalized = os.path.normpath(path)
    parts = normalized.split(os.sep)

    # Reject if any part is ".."
    if ".." in parts:
        return False

    # Reject if path contains ".." as a component (e.g. user/../etc)
    if ".." in path.replace("\\", "/").split("/"):
        return False

    return True


def check_page_limit(current: int, max_pages: int) -> bool:
    """Check if we're still within the page processing limit.

    Args:
        current: Current page number being processed.
        max_pages: Maximum pages allowed (0 = no limit).

    Returns:
        True if within limit, False if limit exceeded.
    """
    if max_pages <= 0:
        return True
    return current < max_pages


def check_memory_limit(peak_mb: float, max_mb: float) -> bool:
    """Check if memory usage is within the allowed limit.

    Args:
        peak_mb: Current peak memory usage in MB.
        max_mb: Maximum memory allowed in MB (0 = no limit).

    Returns:
        True if within limit, False if limit exceeded.
    """
    if max_mb <= 0:
        return True
    return peak_mb < max_mb

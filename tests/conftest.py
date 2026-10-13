"""Pytest configuration — skip tests that require the real legal PDF.

The real expediente is protected personal/legal data and is deliberately
excluded from version control (see .gitignore). Tests whose module defines
a module-level ``REAL_PDF`` constant pointing at it are skipped when the
file is absent, so a fresh clone still has a green suite.

Synthetic fixtures under ``tests/fixtures/pdfs/`` are committed and always run.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REAL_PDF = Path(__file__).parent / "fixtures" / "expediente Miranda ..pdf"


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip tests whose module needs the real PDF when it is absent."""
    if REAL_PDF.exists():
        return

    skip_real = pytest.mark.skip(reason="Real legal PDF excluded from VCS (data protection)")
    for item in items:
        real = getattr(item.module, "REAL_PDF", None)
        if real is not None and not Path(real).exists():
            item.add_marker(skip_real)
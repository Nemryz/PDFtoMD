
from __future__ import annotations

from pathlib import Path

import pytest

REAL_PDF = Path(__file__).parent / "fixtures" / "expediente Miranda ..pdf"


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if REAL_PDF.exists():
        return

    skip_real = pytest.mark.skip(reason="Real legal PDF excluded from VCS (data protection)")
    for item in items:
        real = getattr(item.module, "REAL_PDF", None)
        if real is not None and not Path(real).exists():
            item.add_marker(skip_real)
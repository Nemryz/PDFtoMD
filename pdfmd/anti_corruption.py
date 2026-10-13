# Safe file writes, borrowed from the SDD-Kit patterns: never leave a half-written file behind.

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any


def atomic_write(path: str | Path, content: str | bytes) -> None:
    # I write to a temp file then rename, since a rename is atomic on Windows and NTFS.
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(dir=target.parent, suffix=".tmp")
    try:
        mode = "w" if isinstance(content, str) else "wb"
        kwargs = {"encoding": "utf-8"} if isinstance(content, str) else {}
        with os.fdopen(fd, mode, **kwargs) as f:
            f.write(content)
        os.replace(tmp_path, target)
    except BaseException:
        os.unlink(tmp_path)
        raise


def write_with_backup(path: str | Path, content: str | bytes) -> None:
    # I keep the previous version around before overwriting, in case the caller wants it back.
    target = Path(path)
    if target.exists():
        backup_dir = target.parent.parent / ".opencode" / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        import time

        ts = int(time.time())
        backup_path = backup_dir / f"{target.name}.{ts}.bak"
        backup_path.write_bytes(target.read_bytes())

        # Ten is plenty; older backups are noise.
        backups = sorted(backup_dir.glob(f"{target.name}.*.bak"))
        for old in backups[:-10]:
            old.unlink()

    atomic_write(target, content)


def file_hash(path: str | Path) -> str:
    # I hash the bytes so callers can tell whether a file actually changed.
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_read_json(path: str | Path, default: Any = None) -> Any:
    # I never raise from here: a broken JSON file should degrade, not stop a conversion.
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def safe_write_json(path: str | Path, data: Any, indent: int = 2) -> None:
    # Same temp-then-rename dance as write_text_atomic, but for JSON.
    content = json.dumps(data, indent=indent, ensure_ascii=False)
    atomic_write(path, content + "\n")

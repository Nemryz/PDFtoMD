"""Anti-corruption layer — safe file I/O patterns from SDD-Kit."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any


def atomic_write(path: str | Path, content: str | bytes) -> None:
    """Write to a temp file then atomically rename to target.

    Prevents corruption if the process is interrupted mid-write.
    """
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
    """Write content with automatic backup of the previous version.

    If the target file exists, saves it as <file>.<timestamp>.bak
    in .opencode/backups/ before overwriting.
    """
    target = Path(path)
    if target.exists():
        backup_dir = target.parent.parent / ".opencode" / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        import time

        ts = int(time.time())
        backup_path = backup_dir / f"{target.name}.{ts}.bak"
        backup_path.write_bytes(target.read_bytes())

        # Keep max 10 backups
        backups = sorted(backup_dir.glob(f"{target.name}.*.bak"))
        for old in backups[:-10]:
            old.unlink()

    atomic_write(target, content)


def file_hash(path: str | Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_read_json(path: str | Path, default: Any = None) -> Any:
    """Read a JSON file safely, returning default on any error."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def safe_write_json(path: str | Path, data: Any, indent: int = 2) -> None:
    """Write data to a JSON file atomically."""
    content = json.dumps(data, indent=indent, ensure_ascii=False)
    atomic_write(path, content + "\n")

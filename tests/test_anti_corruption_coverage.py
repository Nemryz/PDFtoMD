"""Coverage tests for anti_corruption module."""

import json
import tempfile
from pathlib import Path

from pdfmd.anti_corruption import (
    atomic_write,
    file_hash,
    safe_read_json,
    safe_write_json,
    write_with_backup,
)


class TestAtomicWrite:
    def test_writes_string_content(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.txt"
            atomic_write(str(path), "hello world")
            assert path.read_text(encoding="utf-8") == "hello world"

    def test_writes_bytes_content(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.bin"
            atomic_write(str(path), b"\x00\x01\x02")
            assert path.read_bytes() == b"\x00\x01\x02"

    def test_creates_parent_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sub" / "dir" / "test.txt"
            atomic_write(str(path), "nested")
            assert path.read_text(encoding="utf-8") == "nested"

    def test_overwrites_existing_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.txt"
            atomic_write(str(path), "old")
            atomic_write(str(path), "new")
            assert path.read_text(encoding="utf-8") == "new"

    def test_cleans_up_tmp_on_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.txt"
            try:
                atomic_write(str(path), None)  # type: ignore
            except (TypeError, AttributeError):
                pass
            # .tmp file should not remain
            tmp_files = list(Path(tmpdir).glob("*.tmp"))
            assert len(tmp_files) == 0


class TestWriteWithBackup:
    def test_creates_backup(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sub" / "test.txt"
            path.parent.mkdir(parents=True)
            path.write_text("original", encoding="utf-8")

            write_with_backup(str(path), "updated")
            assert path.read_text(encoding="utf-8") == "updated"

            # Check backup exists in .opencode/backups/
            backup_dir = path.parent.parent / ".opencode" / "backups"
            backups = list(backup_dir.glob("test.txt.*.bak"))
            assert len(backups) == 1
            assert backups[0].read_text(encoding="utf-8") == "original"

    def test_no_backup_for_new_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sub" / "new.txt"
            path.parent.mkdir(parents=True)
            write_with_backup(str(path), "first")
            assert path.read_text(encoding="utf-8") == "first"

    def test_trims_old_backups(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sub" / "test.txt"
            path.parent.mkdir(parents=True)
            backup_dir = path.parent.parent / ".opencode" / "backups"
            backup_dir.mkdir(parents=True)

            # Create 12 fake backups
            for i in range(12):
                (backup_dir / f"test.txt.{1000 + i}.bak").write_text(f"old{i}")

            path.write_text("current", encoding="utf-8")
            write_with_backup(str(path), "new")

            # Should keep max 10
            backups = sorted(backup_dir.glob("test.txt.*.bak"))
            assert len(backups) <= 10


class TestFileHash:
    def test_hash_consistent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.txt"
            path.write_text("content", encoding="utf-8")
            h1 = file_hash(str(path))
            h2 = file_hash(str(path))
            assert h1 == h2

    def test_hash_different_for_different_content(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p1 = Path(tmpdir) / "a.txt"
            p2 = Path(tmpdir) / "b.txt"
            p1.write_text("aaa", encoding="utf-8")
            p2.write_text("bbb", encoding="utf-8")
            assert file_hash(str(p1)) != file_hash(str(p2))


class TestSafeReadJson:
    def test_reads_valid_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "data.json"
            path.write_text('{"key": "value"}', encoding="utf-8")
            result = safe_read_json(str(path))
            assert result == {"key": "value"}

    def test_returns_default_on_missing(self):
        result = safe_read_json("/nonexistent/file.json", default={"fallback": True})
        assert result == {"fallback": True}

    def test_returns_default_on_invalid_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "bad.json"
            path.write_text("not json {{{", encoding="utf-8")
            result = safe_read_json(str(path))
            assert result is None

    def test_returns_none_default(self):
        result = safe_read_json("/nonexistent.json")
        assert result is None


class TestSafeWriteJson:
    def test_writes_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "out.json"
            safe_write_json(str(path), {"a": 1, "b": [2, 3]})
            data = json.loads(path.read_text(encoding="utf-8"))
            assert data["a"] == 1
            assert data["b"] == [2, 3]

    def test_creates_parent_dirs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sub" / "dir" / "out.json"
            safe_write_json(str(path), {"nested": True})
            assert path.exists()

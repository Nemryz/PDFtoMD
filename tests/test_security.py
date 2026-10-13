
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from pdfmd.cli import app
from pdfmd.security import check_memory_limit, check_page_limit, validate_path

FIXTURE_DIR = Path(__file__).parent / "fixtures"
REAL_PDF = FIXTURE_DIR / "expediente Miranda ..pdf"

runner = CliRunner()


class TestValidatePath:
    def test_clean_path_accepted(self):
        assert validate_path("/home/user/documents/file.pdf") is True

    def test_relative_path_accepted(self):
        assert validate_path("documents/file.pdf") is True

    def test_path_with_dots_rejected(self):
        assert validate_path("/home/user/../etc/passwd") is False

    def test_path_traversal_dots_rejected(self):
        assert validate_path("../../../etc/passwd") is False

    def test_empty_path_rejected(self):
        assert validate_path("") is False

    def test_path_with_null_bytes_rejected(self):
        assert validate_path("/home/user/file\x00.pdf") is False

    def test_path_with_backslash_traversal_rejected(self):
        assert validate_path("C:\\Users\\..\\etc\\passwd") is False

    def test_windows_path_with_dots_rejected(self):
        assert validate_path("C:\\Users\\admin\\..\\secret.pdf") is False

    def test_normal_windows_path_accepted(self):
        assert validate_path("C:\\Users\\admin\\Documents\\file.pdf") is True


class TestCheckPageLimit:
    def test_under_limit(self):
        assert check_page_limit(current=5, max_pages=10) is True

    def test_at_limit(self):
        assert check_page_limit(current=10, max_pages=10) is False

    def test_over_limit(self):
        assert check_page_limit(current=15, max_pages=10) is False

    def test_zero_max_means_no_limit(self):
        assert check_page_limit(current=100, max_pages=0) is True

    def test_negative_current(self):
        assert check_page_limit(current=-1, max_pages=10) is True


class TestCheckMemoryLimit:
    def test_under_limit(self):
        assert check_memory_limit(peak_mb=500.0, max_mb=1024.0) is True

    def test_over_limit(self):
        assert check_memory_limit(peak_mb=1500.0, max_mb=1024.0) is False

    def test_exactly_at_limit(self):
        assert check_memory_limit(peak_mb=1024.0, max_mb=1024.0) is False

    def test_zero_max_means_no_limit(self):
        assert check_memory_limit(peak_mb=9999.0, max_mb=0.0) is True

    def test_negative_memory(self):
        assert check_memory_limit(peak_mb=-1.0, max_mb=1024.0) is True


class TestCLISecurity:

    def test_traversal_path_rejected(self):
        result = runner.invoke(app, ["convert", "../../../etc/passwd"])
        assert result.exit_code != 0

    @pytest.mark.slow
    def test_max_pages_flag(self):
        if not REAL_PDF.exists():
            pytest.skip("Fixture PDF not found")
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "result.md"
            result = runner.invoke(
                app,
                [
                    "convert",
                    str(REAL_PDF),
                    "-o",
                    str(output),
                    "--max-pages",
                    "1",
                ],
            )
            assert result.exit_code == 0

    @pytest.mark.slow
    def test_max_memory_flag(self):
        if not REAL_PDF.exists():
            pytest.skip("Fixture PDF not found")
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "result.md"
            result = runner.invoke(
                app,
                [
                    "convert",
                    str(REAL_PDF),
                    "-o",
                    str(output),
                    "--pages",
                    "0",
                    "--max-memory",
                    "9999",
                ],
            )
            assert result.exit_code == 0

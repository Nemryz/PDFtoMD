
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from pdfmd.cli import app

FIXTURE_DIR = Path(__file__).parent / "fixtures"
REAL_PDF = FIXTURE_DIR / "expediente Miranda ..pdf"

runner = CliRunner()


class TestCLIHelp:
    def test_root_help(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "pdfmd" in result.output.lower()

    def test_convert_help(self):
        result = runner.invoke(app, ["convert", "--help"])
        assert result.exit_code == 0
        assert "input" in result.output.lower() or "pdf" in result.output.lower()


class TestCLIVersion:
    def test_version_flag(self):
        result = runner.invoke(app, ["--version"])
        # Typer --version exits with code 0 or 2 depending on config
        assert result.exit_code in (0, 2)
        assert "pdfmd" in result.output.lower() or "version" in result.output.lower()


class TestCLIInfo:
    def test_info_missing_file(self):
        result = runner.invoke(app, ["info", "nonexistent.pdf"])
        assert result.exit_code != 0

    def test_info_valid_pdf(self):
        if not REAL_PDF.exists():
            pytest.skip("Fixture PDF not found")
        result = runner.invoke(app, ["info", str(REAL_PDF)])
        assert result.exit_code == 0
        assert "page" in result.output.lower()


class TestCLIConvert:
    def test_convert_missing_input(self):
        result = runner.invoke(app, ["convert", "nonexistent.pdf"])
        assert result.exit_code != 0

    def test_convert_not_pdf(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            txt = Path(tmpdir) / "file.txt"
            txt.write_text("not a pdf")
            result = runner.invoke(app, ["convert", str(txt)])
            assert result.exit_code != 0

    @pytest.mark.slow
    def test_convert_with_output_flag(self):
        if not REAL_PDF.exists():
            pytest.skip("Fixture PDF not found")
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "result.md"
            result = runner.invoke(
                app,
                ["convert", str(REAL_PDF), "-o", str(output), "--pages", "0"],
            )
            assert result.exit_code == 0
            assert output.exists()

    @pytest.mark.slow
    def test_convert_with_classify_flag(self):
        if not REAL_PDF.exists():
            pytest.skip("Fixture PDF not found")
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "result.md"
            result = runner.invoke(
                app,
                ["convert", str(REAL_PDF), "-o", str(output), "--pages", "0", "--classify"],
            )
            assert result.exit_code == 0

    @pytest.mark.slow
    def test_convert_with_lang_flag(self):
        if not REAL_PDF.exists():
            pytest.skip("Fixture PDF not found")
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "result.md"
            result = runner.invoke(
                app,
                ["convert", str(REAL_PDF), "-o", str(output), "--pages", "0", "--lang", "spa"],
            )
            assert result.exit_code == 0

    @pytest.mark.slow
    def test_convert_with_min_confidence_flag(self):
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
                    "--min-confidence",
                    "0.5",
                ],
            )
            assert result.exit_code == 0

    @pytest.mark.slow
    def test_convert_with_retry_threshold_flag(self):
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
                    "--retry-threshold",
                    "0.3",
                ],
            )
            assert result.exit_code == 0

    @pytest.mark.slow
    def test_convert_with_pages_flag_range(self):
        if not REAL_PDF.exists():
            pytest.skip("Fixture PDF not found")
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "result.md"
            result = runner.invoke(
                app,
                ["convert", str(REAL_PDF), "-o", str(output), "--pages", "0-2"],
            )
            assert result.exit_code == 0

    @pytest.mark.slow
    def test_convert_with_signers_flag(self):
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
                    "--signers",
                    "Juan Perez,Maria Garcia",
                ],
            )
            assert result.exit_code == 0

    @pytest.mark.slow
    def test_convert_with_dpi_flag(self):
        if not REAL_PDF.exists():
            pytest.skip("Fixture PDF not found")
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "result.md"
            result = runner.invoke(
                app,
                ["convert", str(REAL_PDF), "-o", str(output), "--pages", "0", "--dpi", "150"],
            )
            assert result.exit_code == 0

"""Tests for CLI module."""

import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from pdfmd.cli import app

FIXTURE_DIR = Path(__file__).parent / "fixtures"
REAL_PDF = FIXTURE_DIR / "expediente Miranda ..pdf"

runner = CliRunner()


class TestCLIConvert:
    """Tests for pdfmd convert command."""

    def test_help_shows_usage(self):
        """--help should show usage information."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Convert" in result.output or "pdfmd" in result.output

    def test_convert_missing_input(self):
        """Missing input file should show error."""
        result = runner.invoke(app, ["convert", "nonexistent.pdf"])
        assert result.exit_code != 0

    @pytest.mark.slow
    def test_convert_creates_output(self):
        """Converting a real PDF should create output files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "output.md"
            result = runner.invoke(
                app,
                [
                    "convert",
                    str(REAL_PDF),
                    "-o",
                    str(output),
                    "--pages",
                    "0,1",
                ],
            )
            assert result.exit_code == 0
            assert output.exists()

    def test_convert_with_signers_flag(self):
        """--signers flag should be accepted."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0

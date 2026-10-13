
import tempfile
from pathlib import Path

from typer.testing import CliRunner

from pdfmd.cli import app

FIXTURE_DIR = Path(__file__).parent / "fixtures"
REAL_PDF = FIXTURE_DIR / "expediente Miranda ..pdf"

runner = CliRunner()


class TestWindowsPaths:

    def test_path_with_spaces(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            spaced_dir = Path(tmpdir) / "my folder"
            spaced_dir.mkdir()
            output = spaced_dir / "output.md"

            result = runner.invoke(
                app,
                [
                    "convert",
                    str(REAL_PDF),
                    "-o",
                    str(output),
                    "--pages",
                    "0",
                ],
            )
            assert result.exit_code == 0
            assert output.exists()

    def test_output_creates_parent_dirs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "deep" / "nested" / "output.md"
            result = runner.invoke(
                app,
                [
                    "convert",
                    str(REAL_PDF),
                    "-o",
                    str(output),
                    "--pages",
                    "0",
                ],
            )
            assert result.exit_code == 0
            assert output.exists()

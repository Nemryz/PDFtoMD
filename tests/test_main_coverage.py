"""Coverage tests for __main__ module."""

import subprocess
import sys


class TestMain:
    def test_run_as_module(self):
        """python -m pdfmd should invoke the CLI."""
        result = subprocess.run(
            [sys.executable, "-m", "pdfmd", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "pdfmd" in result.stdout.lower() or "convert" in result.stdout.lower()

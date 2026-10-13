"""Tests for benchmark output format (US-8, Feature 003)."""

import json
import tempfile
from pathlib import Path

import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "pdfs"
SMALL_PDF = FIXTURE_DIR / "valid" / "simple_1page.pdf"


class TestBenchOutput:
    """Tests verifying bench.py JSON output structure."""

    def test_benchmark_runs(self):
        if not SMALL_PDF.exists():
            pytest.skip("Fixture PDF not found")
        from bench import benchmark_pdf

        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "report.json"
            results = benchmark_pdf(str(SMALL_PDF), classify=False, dpi=300, lang="spa")
            # Save and verify JSON serializable
            out.write_text(json.dumps(results, indent=2, ensure_ascii=False))
            loaded = json.loads(out.read_text(encoding="utf-8"))
            assert "timings" in loaded

    def test_has_timings_section(self):
        if not SMALL_PDF.exists():
            pytest.skip("Fixture PDF not found")
        from bench import benchmark_pdf

        results = benchmark_pdf(str(SMALL_PDF))
        assert "timings" in results
        assert "total_processing" in results["timings"]

    def test_has_quality_section(self):
        if not SMALL_PDF.exists():
            pytest.skip("Fixture PDF not found")
        from bench import benchmark_pdf

        results = benchmark_pdf(str(SMALL_PDF))
        assert "quality" in results
        q = results["quality"]
        assert "words" in q
        assert "broken_sentences" in q
        assert "broken_connectors" in q
        assert "noise_patterns" in q

    def test_has_stats_section(self):
        if not SMALL_PDF.exists():
            pytest.skip("Fixture PDF not found")
        from bench import benchmark_pdf

        results = benchmark_pdf(str(SMALL_PDF))
        assert "stats" in results
        s = results["stats"]
        assert "total_pages" in s
        assert "avg_confidence" in s

    def test_has_memory_section(self):
        if not SMALL_PDF.exists():
            pytest.skip("Fixture PDF not found")
        from bench import benchmark_pdf

        results = benchmark_pdf(str(SMALL_PDF))
        assert "memory" in results
        m = results["memory"]
        assert "peak_rss_mb" in m
        assert "end_rss_mb" in m
        assert "start_rss_mb" in m
        assert m["peak_rss_mb"] > 0

    def test_has_page_timings(self):
        if not SMALL_PDF.exists():
            pytest.skip("Fixture PDF not found")
        from bench import benchmark_pdf

        results = benchmark_pdf(str(SMALL_PDF))
        pages = results["timings"].get("pages", {})
        # PDF with text layer uses extract_text; scanned uses render+ocr
        assert len(pages) > 0

    def test_quality_values_are_ints(self):
        if not SMALL_PDF.exists():
            pytest.skip("Fixture PDF not found")
        from bench import benchmark_pdf

        results = benchmark_pdf(str(SMALL_PDF))
        q = results["quality"]
        assert isinstance(q["words"], int)
        assert isinstance(q["broken_sentences"], int)
        assert isinstance(q["noise_patterns"], int)

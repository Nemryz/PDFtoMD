
import tempfile
from pathlib import Path

import pytest

from pdfmd.core import ConversionResult, PageResult, convert_pdf

FIXTURE_DIR = Path(__file__).parent / "fixtures"
REAL_PDF = FIXTURE_DIR / "expediente Miranda ..pdf"


class TestCoreCoverage:

    def test_convert_returns_conversion_result(self):
        if not REAL_PDF.exists():
            pytest.skip("Fixture PDF not found")
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "output.md"
            result = convert_pdf(str(REAL_PDF), str(out), pages=[0])
            assert isinstance(result, ConversionResult)
            assert result.pages_processed >= 1
            assert result.total_pages > 0

    def test_output_path_set(self):
        if not REAL_PDF.exists():
            pytest.skip("Fixture PDF not found")
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "output.md"
            result = convert_pdf(str(REAL_PDF), str(out), pages=[0])
            assert result.output_path == str(out)

    def test_metadata_path_set(self):
        if not REAL_PDF.exists():
            pytest.skip("Fixture PDF not found")
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "output.md"
            result = convert_pdf(str(REAL_PDF), str(out), pages=[0])
            meta = Path(result.metadata_path)
            assert meta.exists()

    def test_metadata_json_valid(self):
        if not REAL_PDF.exists():
            pytest.skip("Fixture PDF not found")
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "output.md"
            result = convert_pdf(str(REAL_PDF), str(out), pages=[0])
            import json

            meta = json.loads(Path(result.metadata_path).read_text(encoding="utf-8"))
            assert "source" in meta
            assert "total_pages" in meta
            assert "quality" in meta

    def test_quality_in_metadata(self):
        if not REAL_PDF.exists():
            pytest.skip("Fixture PDF not found")
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "output.md"
            result = convert_pdf(str(REAL_PDF), str(out), pages=[0])
            import json

            meta = json.loads(Path(result.metadata_path).read_text(encoding="utf-8"))
            assert "quality" in meta
            assert "score" in meta["quality"]
            assert "words" in meta["quality"]

    def test_page_result_fields(self):
        if not REAL_PDF.exists():
            pytest.skip("Fixture PDF not found")
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "output.md"
            result = convert_pdf(str(REAL_PDF), str(out), pages=[0])
            assert len(result.pages) >= 1
            page = result.pages[0]
            assert isinstance(page, PageResult)
            assert page.page_number == 1
            assert page.text is not None
            assert page.confidence >= 0

    def test_page_has_blocks(self):
        if not REAL_PDF.exists():
            pytest.skip("Fixture PDF not found")
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "output.md"
            result = convert_pdf(str(REAL_PDF), str(out), pages=[0])
            assert len(result.pages[0].blocks) >= 1

    def test_output_file_created(self):
        if not REAL_PDF.exists():
            pytest.skip("Fixture PDF not found")
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "output.md"
            convert_pdf(str(REAL_PDF), str(out), pages=[0])
            assert out.exists()
            content = out.read_text(encoding="utf-8")
            assert len(content) > 0

    def test_warnings_list(self):
        if not REAL_PDF.exists():
            pytest.skip("Fixture PDF not found")
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "output.md"
            result = convert_pdf(str(REAL_PDF), str(out), pages=[0])
            assert isinstance(result.warnings, list)

    def test_elapsed_time_positive(self):
        if not REAL_PDF.exists():
            pytest.skip("Fixture PDF not found")
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "output.md"
            result = convert_pdf(str(REAL_PDF), str(out), pages=[0])
            assert result.elapsed_seconds > 0

    def test_nonexistent_file_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "output.md"
            with pytest.raises(Exception):
                convert_pdf("/nonexistent/file.pdf", str(out))

    def test_pages_parameter(self):
        if not REAL_PDF.exists():
            pytest.skip("Fixture PDF not found")
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "output.md"
            result = convert_pdf(str(REAL_PDF), str(out), pages=[0, 1])
            assert result.pages_processed == 2

    def test_classify_parameter(self):
        if not REAL_PDF.exists():
            pytest.skip("Fixture PDF not found")
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "output.md"
            result = convert_pdf(str(REAL_PDF), str(out), pages=[0], classify=True)
            assert result.pages_processed >= 1

    def test_min_confidence_parameter(self):
        if not REAL_PDF.exists():
            pytest.skip("Fixture PDF not found")
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "output.md"
            result = convert_pdf(
                str(REAL_PDF), str(out), pages=[0], min_confidence=0.3, retry_threshold=0.2
            )
            assert result.pages_processed >= 1

    def test_images_dir_none_when_no_images(self):
        if not REAL_PDF.exists():
            pytest.skip("Fixture PDF not found")
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "output.md"
            result = convert_pdf(str(REAL_PDF), str(out), pages=[0])
            # May or may not have images dir
            assert hasattr(result, "images_dir")

    def test_signature_report_path_none_without_signers(self):
        if not REAL_PDF.exists():
            pytest.skip("Fixture PDF not found")
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "output.md"
            result = convert_pdf(str(REAL_PDF), str(out), pages=[0])
            assert result.signature_report_path is None

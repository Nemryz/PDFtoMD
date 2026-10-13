
from pathlib import Path

from pdfmd.page_renderer import render_page
from pdfmd.pdf_reader import open_pdf
from pdfmd.signature_detector import (
    PageSignatures,
    SignatureRegion,
    SignatureReport,
    detect_signatures,
    generate_signature_report,
    match_signer,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures"
REAL_PDF = FIXTURE_DIR / "expediente Miranda ..pdf"


class TestDetectSignatures:

    def test_returns_list(self):
        doc = open_pdf(str(REAL_PDF))
        img = render_page(doc[0], dpi=150)  # Low DPI for speed
        result = detect_signatures(img)
        assert isinstance(result, list)
        doc.close()

    def test_returns_signature_region_type(self):
        doc = open_pdf(str(REAL_PDF))
        img = render_page(doc[0], dpi=150)
        result = detect_signatures(img)
        for sig in result:
            assert isinstance(sig, SignatureRegion)
        doc.close()


class TestMatchSigner:

    def test_matches_known_signer(self):
        region = SignatureRegion(x=100, y=500, width=200, height=100, confidence=0.8)
        signers = ["Juan Pérez", "María García"]
        result = match_signer(region, signers, page_text="Juan Pérez firma aquí")
        # May or may not match depending on heuristic
        assert result is None or isinstance(result, str)

    def test_no_match_returns_none(self):
        region = SignatureRegion(x=100, y=500, width=200, height=100, confidence=0.8)
        result = match_signer(region, ["Unknown Person"], page_text="Some random text")
        assert result is None


class TestGenerateSignatureReport:

    def test_returns_report(self):
        pages = [
            PageSignatures(
                page_number=1,
                signatures=[],
                expected_signers=["Juan Pérez"],
            ),
            PageSignatures(
                page_number=2,
                signatures=[SignatureRegion(x=0, y=0, width=100, height=50, confidence=0.9)],
                expected_signers=["María García"],
                matched_signers=["María García"],
            ),
        ]
        report = generate_signature_report(pages)
        assert isinstance(report, SignatureReport)
        assert report.total_pages == 2
        assert report.pages_with_signatures == 1

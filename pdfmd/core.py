# The pipeline itself: open, render, OCR, assemble, write.

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

from pdfmd.adaptive_router import AdaptiveOCRRouter
from pdfmd.anti_corruption import atomic_write, safe_write_json
from pdfmd.content_analyzer import Block, analyze_page
from pdfmd.image_extractor import deduplicate, extract_images, save_images
from pdfmd.image_preprocessor import ImagePreprocessor, should_preprocess
from pdfmd.markdown_builder import build_markdown
from pdfmd.metadata_builder import build_metadata
from pdfmd.ocr_engine import initialize_tesseract, ocr_with_confidence
from pdfmd.page_classifier import PageClassifier
from pdfmd.page_renderer import render_page
from pdfmd.pdf_reader import extract_page_text, get_page_count, has_text_layer, open_pdf
from pdfmd.quality_metrics import measure_text_quality
from pdfmd.signature_detector import (
    PageSignatures,
    detect_signatures,
    generate_signature_report,
    match_signer,
)
from pdfmd.types import OCRParameters, PageClassificationResult


@dataclass
class PageResult:
    # What came out of one page, whether it was OCR'd or read from a text layer.

    page_number: int
    text: str
    confidence: float
    used_ocr: bool
    blocks: list[Block] = field(default_factory=list)
    signatures_found: int = 0


@dataclass
class ConversionResult:
    # The whole run, from the first page to the files on disk.

    pages_processed: int
    total_pages: int
    pages_with_ocr: int
    avg_confidence: float
    elapsed_seconds: float
    output_path: str
    metadata_path: str
    signature_report_path: str | None = None
    images_dir: str | None = None
    warnings: list[str] = field(default_factory=list)
    pages: list[PageResult] = field(default_factory=list)


def convert_pdf(
    input_path: str,
    output_path: str,
    tesseract_path: str | None = None,
    lang: str = "spa",
    dpi: int = 300,
    pages: list[int] | None = None,
    signers: list[str] | None = None,
    classify: bool = False,
    min_confidence: float = 0.70,
    retry_threshold: float = 0.50,
) -> ConversionResult:
    # The public entry point. Everything else in here is a step inside it.
    start_time = time.time()
    warnings: list[str] = []

    # Tesseract first, because if it's missing nothing else matters.
    initialize_tesseract(tesseract_path=tesseract_path, lang=lang)

    # Classifier and router are optional, so I only build them when asked.
    page_classifier: PageClassifier | None = None
    adaptive_router: AdaptiveOCRRouter | None = None
    image_preprocessor: ImagePreprocessor | None = None
    classifications: list[PageClassificationResult] = []

    if classify:
        page_classifier = PageClassifier()
        adaptive_router = AdaptiveOCRRouter()
        image_preprocessor = ImagePreprocessor()
        warnings.append("Smart classification enabled — adaptive OCR active")

    # PyMuPDF hands back a document I can page through.
    doc = open_pdf(input_path)
    total_pages = get_page_count(doc)

    # An empty page spec means the entire document.
    if pages is not None:
        page_indices = [p for p in pages if p < total_pages]
    else:
        page_indices = list(range(total_pages))

    # Embedded images, when the caller wants them alongside the text.
    all_images = extract_images(doc, pages=page_indices)
    unique_images = deduplicate(all_images)

    # Nothing to save is a normal case, not an error.
    images_dir = None
    if unique_images:
        out_dir = Path(output_path).parent / "images"
        save_images(unique_images, str(out_dir))
        images_dir = str(out_dir)

    page_results: list[PageResult] = []
    page_signatures: list[PageSignatures] = []

    for i in page_indices:
        page = doc[i]
        page_num = i + 1

        # With classification on, each page picks its own DPI and PSM instead of one global setting.
        ocr_params = OCRParameters(dpi=dpi, psm=6, lang=lang)
        if page_classifier and adaptive_router:
            classification = page_classifier.classify_page(doc, i)
            ocr_params = adaptive_router.get_parameters_for_result(classification)
            classifications.append(classification)

            # Blank pages skip OCR entirely, which is where the big speedup comes from.
            if ocr_params.skip_ocr:
                result = PageResult(
                    page_number=page_num,
                    text="",
                    confidence=0.0,
                    used_ocr=False,
                    blocks=[],
                )
                page_results.append(result)
                continue

        # A real text layer is cheaper and more accurate than OCR, so I use it when present.
        if has_text_layer(page):
            text = extract_page_text(page)
            blocks = analyze_page(text, confidence=1.0)
            result = PageResult(
                page_number=page_num,
                text=text,
                confidence=1.0,
                used_ocr=False,
                blocks=blocks,
            )
        else:
            # Render at the DPI the classifier asked for, not the global default.
            render_dpi = ocr_params.dpi if classify else dpi
            img = render_page(page, dpi=render_dpi)

            # I gate preprocessing on image quality. Good scans skip it; retries always run it.
            # The gate skips preprocessing on good-quality images; the retry
            # path below always preprocesses (targeted corrective action).
            if classify and image_preprocessor and ocr_params.preprocess:
                if should_preprocess(img):
                    preprocessed = image_preprocessor.preprocess(
                        img,
                        steps=ocr_params.preprocess,
                        enhance_contrast=ocr_params.enhance_contrast,
                        enhance_sharpness=ocr_params.enhance_sharpness,
                    )
                    img = preprocessed.image

            # One Tesseract call per page, returning text and confidence together.
            psm = ocr_params.psm if classify else 6
            text, conf = ocr_with_confidence(img, lang=lang, config=f"--psm {psm}")

            # Low confidence gets one more attempt at a higher DPI before I give up on the page.
            if classify and conf < retry_threshold and image_preprocessor:
                retry_dpi = min(render_dpi + 100, 600)
                img_retry = render_page(page, dpi=retry_dpi)
                preprocessed = image_preprocessor.preprocess(
                    img_retry,
                    steps=["contrast", "sharpness", "denoise"],
                    enhance_contrast=2.0,
                    enhance_sharpness=1.8,
                )
                text_retry, conf_retry = ocr_with_confidence(
                    preprocessed.image, lang=lang, config="--psm 6"
                )
                if conf_retry > conf:
                    text, conf = text_retry, conf_retry
                    warnings.append(
                        f"Page {page_num}: retried with DPI {retry_dpi}, "
                        f"confidence improved {conf_retry:.2f}"
                    )

            # Below the caller's floor I mark the page for review rather than hiding the problem.
            if conf < min_confidence:
                warnings.append(
                    f"Page {page_num}: confidence {conf:.2f} below threshold "
                    f"{min_confidence:.2f} — flagged for review"
                )

            # Same signal, but only worth a warning when it's genuinely low.
            if conf < 0.5:
                warnings.append(f"Low OCR confidence on page {page_num}: {conf:.2f}")

            blocks = analyze_page(text, confidence=conf)
            result = PageResult(
                page_number=page_num,
                text=text,
                confidence=conf,
                used_ocr=True,
                blocks=blocks,
            )

            # Signer matching only costs anything if the caller said who to look for.
            if signers:
                sig_regions = detect_signatures(img)
                matched = []
                for sig in sig_regions:
                    signer = match_signer(sig, signers, page_text=text)
                    if signer:
                        matched.append(signer)

                result.signatures_found = len(sig_regions)

                page_sig = PageSignatures(
                    page_number=page_num,
                    signatures=sig_regions,
                    expected_signers=signers,
                    matched_signers=matched,
                )
                page_signatures.append(page_sig)

        page_results.append(result)

    doc.close()

    # Blocks in, Markdown out, one section per page.
    markdown_sections: list[str] = []
    for pr in page_results:
        section = build_markdown(pr.blocks, page_number=pr.page_number)
        if section.strip():
            markdown_sections.append(section)

    markdown_content = "\n\n".join(markdown_sections)

    # I score the finished text, not the OCR fragments, since that's what the reader gets.
    quality_report = measure_text_quality(markdown_content)

    # Write the Markdown first; it's the artefact people actually want.
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(out, markdown_content)

    # Metadata is a sidecar that describes the run.
    ocr_pages = [p for p in page_results if p.used_ocr]
    confidences = [p.confidence for p in ocr_pages]
    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
    elapsed = time.time() - start_time

    metadata = build_metadata(
        source=Path(input_path).name,
        pages_processed=len(page_results),
        total_pages=total_pages,
        pages_with_ocr=len(ocr_pages),
        avg_confidence=avg_conf,
        elapsed_seconds=elapsed,
        warnings=warnings,
        classifications=classifications if classify else None,
        quality=quality_report,
    )

    metadata_path = out.parent / "metadata.json"
    safe_write_json(metadata_path, metadata)

    # Only meaningful when the caller passed signers in.
    signature_report_path = None
    if signers and page_signatures:
        report = generate_signature_report(page_signatures)
        sig_report_md = _build_signature_report_md(report)
        sig_report_path = out.parent / "signature_report.md"
        atomic_write(sig_report_path, sig_report_md)

        sig_json_path = out.parent / "signature_report.json"
        safe_write_json(
            sig_json_path,
            {
                "total_pages": report.total_pages,
                "pages_with_signatures": report.pages_with_signatures,
                "expected_signers": report.expected_signers,
                "unmatched_signers": report.unmatched_signers,
            },
        )

        signature_report_path = str(sig_report_path)

        # A signer nobody matched is worth surfacing, not swallowing.
        for signer in report.unmatched_signers:
            warnings.append(f"Expected signer '{signer}' not found in any signature")

    return ConversionResult(
        pages_processed=len(page_results),
        total_pages=total_pages,
        pages_with_ocr=len(ocr_pages),
        avg_confidence=avg_conf,
        elapsed_seconds=elapsed,
        output_path=str(out),
        metadata_path=str(metadata_path),
        signature_report_path=signature_report_path,
        images_dir=images_dir,
        warnings=warnings,
        pages=page_results,
    )


def _build_signature_report_md(report) -> str:
    # I render the signature findings as a separate Markdown file.
    lines = [
        "# Signature Report",
        "",
        f"**Total pages:** {report.total_pages}",
        f"**Pages with signatures:** {report.pages_with_signatures}",
        f"**Expected signers:** {', '.join(report.expected_signers) or 'None'}",
        f"**Unmatched signers:** {', '.join(report.unmatched_signers) or 'None'}",
        "",
        "## Per-Page Details",
        "",
    ]

    for ps in report.pages:
        lines.append(f"### Page {ps.page_number}")
        if ps.signatures:
            lines.append(f"- **Signatures detected:** {len(ps.signatures)}")
        else:
            lines.append("- **No signatures detected**")

        if ps.expected_signers:
            for signer in ps.expected_signers:
                if signer in ps.matched_signers:
                    lines.append(f"- ✅ {signer} — signature found")
                else:
                    lines.append(f"- ❌ {signer} — signature NOT found")

        lines.append("")

    return "\n".join(lines)

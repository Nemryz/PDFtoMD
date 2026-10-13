"""Benchmark script — measures time per component and quality metrics."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

import psutil

from pdfmd.content_analyzer import analyze_page
from pdfmd.image_preprocessor import ImagePreprocessor, should_preprocess
from pdfmd.markdown_builder import build_markdown
from pdfmd.metadata_builder import build_metadata
from pdfmd.ocr_engine import initialize_tesseract, ocr_with_confidence
from pdfmd.page_classifier import PageClassifier
from pdfmd.page_renderer import render_page
from pdfmd.pdf_reader import get_page_count, has_text_layer, open_pdf


class Timer:
    """Context manager for timing code blocks."""

    def __init__(self, label: str) -> None:
        self.label = label
        self.elapsed: float = 0.0

    def __enter__(self) -> Timer:
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args: Any) -> None:
        self.elapsed = time.perf_counter() - self._start


def measure_text_quality(text: str) -> dict[str, Any]:
    """Measure quality metrics for extracted text."""
    if not text.strip():
        return {
            "words": 0,
            "broken_sentences": 0,
            "broken_connectors": 0,
            "duplicate_lines": 0,
            "noise_patterns": 0,
            "headers_detected": 0,
            "tables_detected": 0,
            "lists_detected": 0,
            "avg_line_length": 0.0,
        }

    lines = text.split("\n")
    words = text.split()

    # Broken sentences: line ends in lowercase without punctuation
    broken = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if (
            stripped
            and stripped[-1] in "aeiouáéíóúñ"
            and (i + 1 < len(lines) and lines[i + 1].strip())
        ):
            broken += 1

    # Broken connectors: connector split across lines
    connectors = {
        "de",
        "la",
        "el",
        "en",
        "que",
        "por",
        "con",
        "para",
        "los",
        "las",
        "del",
        "un",
        "una",
        "se",
        "al",
    }
    broken_conn = 0
    for i, line in enumerate(lines):
        stripped = line.strip().lower()
        if stripped in connectors and i + 1 < len(lines) and lines[i + 1].strip():
            broken_conn += 1

    # Duplicate lines
    duplicates = 0
    for i in range(1, len(lines)):
        if lines[i].strip() and lines[i].strip() == lines[i - 1].strip():
            duplicates += 1

    # Noise patterns
    noise = 0
    for line in lines:
        stripped = line.strip()
        if re.match(r"^[A-Z]\s*$", stripped):
            noise += 1
        if re.search(r"[^\w\s.,;:!?¿¡\"'()\[\]{}\-–—/\\|@#$%&*+=<>]", stripped):
            noise += 1

    # Headers
    headers = sum(1 for line in lines if re.match(r"^#{1,6}\s", line.strip()))

    # Tables
    tables = sum(1 for line in lines if "|" in line and line.strip().startswith("|"))

    # Lists
    lists = sum(
        1 for line in lines if re.match(r"^\s*[-*•]\s", line) or re.match(r"^\s*\d+\.\s", line)
    )

    # Avg line length
    non_empty = [line for line in lines if line.strip()]
    avg_len = sum(len(l) for l in non_empty) / len(non_empty) if non_empty else 0.0

    return {
        "words": len(words),
        "broken_sentences": broken,
        "broken_connectors": broken_conn,
        "duplicate_lines": duplicates,
        "noise_patterns": noise,
        "headers_detected": headers,
        "tables_detected": tables,
        "lists_detected": lists,
        "avg_line_length": round(avg_len, 1),
    }


def benchmark_pdf(
    pdf_path: str,
    classify: bool = False,
    dpi: int = 300,
    lang: str = "spa",
) -> dict[str, Any]:
    """Run full benchmark on a PDF file."""
    pdf_path_obj = Path(pdf_path)
    if not pdf_path_obj.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    # Initialize Tesseract
    t = Timer("tesseract_init")
    with t:
        initialize_tesseract(lang=lang)

    # Open PDF
    t2 = Timer("pdf_open")
    with t2:
        doc = open_pdf(pdf_path)

    total_pages = get_page_count(doc)

    results: dict[str, Any] = {
        "pdf": pdf_path_obj.name,
        "classify": classify,
        "dpi": dpi,
        "lang": lang,
        "timings": {
            "tesseract_init": round(t.elapsed, 3),
            "pdf_open": round(t2.elapsed, 3),
        },
        "quality": {},
        "stats": {"total_pages": total_pages},
        "memory": {},
    }

    # Memory tracking
    process = psutil.Process()
    mem_start = process.memory_info().rss / (1024 * 1024)  # MB
    peak_mem = mem_start

    # Classify all pages (if enabled)
    classifier = None
    if classify:
        t = Timer("classify_all")
        with t:
            classifier = PageClassifier()
        results["timings"]["classify_init"] = round(t.elapsed, 3)

    # Process each page
    page_timings: list[dict[str, float]] = []
    all_text: list[str] = []
    confidences: list[float] = []
    preprocessor = ImagePreprocessor() if classify else None

    for i in range(total_pages):
        page = doc[i]
        page_num = i + 1
        pt: dict[str, float] = {}

        if has_text_layer(page):
            from pdfmd.pdf_reader import extract_page_text

            t = Timer("extract_text")
            with t:
                text = extract_page_text(page)
            pt["extract_text"] = round(t.elapsed, 4)
            conf = 1.0
        else:
            # Render
            t = Timer("render")
            with t:
                img = render_page(page, dpi=dpi)
            pt["render"] = round(t.elapsed, 4)

            # Preprocess (if classify)
            if classify and preprocessor:
                t = Timer("preprocess")
                with t:
                    from pdfmd.types import OCRParameters

                    params = OCRParameters(dpi=dpi, psm=6, lang=lang)
                    if classifier:
                        cls_result = classifier.classify_page(doc, i)
                        from pdfmd.adaptive_router import AdaptiveOCRRouter

                        router = AdaptiveOCRRouter()
                        params = router.get_parameters_for_result(cls_result)
                    if params.preprocess and should_preprocess(img):
                        preprocessed = preprocessor.preprocess(
                            img,
                            steps=params.preprocess,
                            enhance_contrast=params.enhance_contrast,
                            enhance_sharpness=params.enhance_sharpness,
                        )
                        img = preprocessed.image
                pt["preprocess"] = round(t.elapsed, 4)

            # OCR — single pass (text + confidence in one Tesseract call, US-1)
            t = Timer("ocr")
            with t:
                psm = params.psm if classify else 6
                text, conf = ocr_with_confidence(img, lang=lang, config=f"--psm {psm}")
            pt["ocr"] = round(t.elapsed, 4)

        confidences.append(conf)
        all_text.append(text)
        page_timings.append(pt)

        # Track memory
        current_mem = process.memory_info().rss / (1024 * 1024)
        if current_mem > peak_mem:
            peak_mem = current_mem

        # Progress
        if page_num % 10 == 0 or page_num == total_pages:
            print(f"  Page {page_num}/{total_pages}...", flush=True)

    doc.close()

    # Final memory stats
    mem_end = process.memory_info().rss / (1024 * 1024)
    results["memory"] = {
        "peak_rss_mb": round(peak_mem, 1),
        "end_rss_mb": round(mem_end, 1),
        "start_rss_mb": round(mem_start, 1),
    }

    # Aggregate timings
    agg: dict[str, float] = {}
    for key in ["render", "preprocess", "ocr", "confidence", "extract_text"]:
        vals = [pt[key] for pt in page_timings if key in pt]
        if vals:
            agg[f"{key}_total"] = round(sum(vals), 3)
            agg[f"{key}_avg"] = round(sum(vals) / len(vals), 4)
            agg[f"{key}_min"] = round(min(vals), 4)
            agg[f"{key}_max"] = round(max(vals), 4)
    results["timings"]["pages"] = agg

    # Total processing time
    total_processing = sum(sum(pt.values()) for pt in page_timings)
    results["timings"]["total_processing"] = round(total_processing, 3)

    # Content analysis + markdown build (on all pages combined)
    t = Timer("content_analysis")
    with t:
        all_blocks = []
        for text in all_text:
            blocks = analyze_page(text, confidence=1.0)
            all_blocks.extend(blocks)
    results["timings"]["content_analysis"] = round(t.elapsed, 3)

    t = Timer("markdown_build")
    with t:
        sections = []
        for i, blocks in enumerate([all_blocks]):  # simplified
            section = build_markdown(blocks, page_number=i + 1)
            if section.strip():
                sections.append(section)
    results["timings"]["markdown_build"] = round(t.elapsed, 3)

    # Quality metrics (on combined text)
    full_text = "\n\n".join(all_text)
    t = Timer("quality_check")
    with t:
        quality = measure_text_quality(full_text)
    results["timings"]["quality_check"] = round(t.elapsed, 3)
    results["quality"] = quality

    # Confidence stats
    ocr_confs = [c for c in confidences if c < 1.0]
    results["stats"]["avg_confidence"] = round(
        sum(ocr_confs) / len(ocr_confs) if ocr_confs else 1.0, 4
    )
    results["stats"]["min_confidence"] = round(min(ocr_confs) if ocr_confs else 1.0, 4)
    results["stats"]["max_confidence"] = round(max(ocr_confs) if ocr_confs else 1.0, 4)
    results["stats"]["pages_below_50"] = sum(1 for c in ocr_confs if c < 0.5)
    results["stats"]["pages_below_70"] = sum(1 for c in ocr_confs if c < 0.7)
    results["stats"]["pages_with_text_layer"] = total_pages - len(ocr_confs)
    results["stats"]["total_words"] = quality["words"]

    # Metadata
    t = Timer("metadata_build")
    with t:
        metadata = build_metadata(
            source=pdf_path_obj.name,
            pages_processed=total_pages,
            total_pages=total_pages,
            pages_with_ocr=len(ocr_confs),
            avg_confidence=results["stats"]["avg_confidence"],
            elapsed_seconds=total_processing,
            warnings=[],
        )
    results["timings"]["metadata_build"] = round(t.elapsed, 3)

    return results


def print_report(results: dict[str, Any]) -> None:
    """Print formatted benchmark report."""
    print("\n" + "=" * 70)
    print("BENCHMARK REPORT — PDFtoMD Pipeline")
    print("=" * 70)
    print(f"PDF: {results['pdf']}")
    print(f"Classify: {results['classify']}")
    print(f"DPI: {results['dpi']}")
    print(f"Language: {results['lang']}")
    print()

    # Component breakdown
    t = results["timings"]
    pages = t.get("pages", {})
    total = t.get("total_processing", 0)

    print("COMPONENT BREAKDOWN:")
    print("-" * 70)
    print(f"{'Component':<25} {'Total (s)':>10} {'% Total':>8} {'Avg/Page':>10}")
    print("-" * 70)

    components = [
        ("PDF Open", t.get("pdf_open", 0)),
        ("Tesseract Init", t.get("tesseract_init", 0)),
        ("Render", pages.get("render_total", 0)),
        ("Preprocess", pages.get("preprocess_total", 0)),
        ("OCR", pages.get("ocr_total", 0)),
        ("Confidence", pages.get("confidence_total", 0)),
        ("Extract Text", pages.get("extract_text_total", 0)),
        ("Content Analysis", t.get("content_analysis", 0)),
        ("Markdown Build", t.get("markdown_build", 0)),
        ("Metadata Build", t.get("metadata_build", 0)),
        ("Quality Check", t.get("quality_check", 0)),
    ]

    grand_total = sum(v for _, v in components)
    for name, val in components:
        pct = (val / grand_total * 100) if grand_total > 0 else 0
        avg = val / results["stats"]["total_pages"] if results["stats"]["total_pages"] > 0 else 0
        print(f"  {name:<23} {val:>10.3f} {pct:>7.1f}% {avg * 1000:>9.1f}ms")

    print("-" * 70)
    print(f"  {'TOTAL':<23} {grand_total:>10.3f} {'100.0%':>8}")
    print()

    # Quality metrics
    q = results["quality"]
    s = results["stats"]

    print("QUALITY METRICS:")
    print("-" * 70)
    print(f"  Words extracted:        {q['words']:>8}")
    print(
        f"  Broken sentences:       {q['broken_sentences']:>8} ({q['broken_sentences'] / max(q['words'], 1) * 100:.1f}%)"
    )
    print(f"  Broken connectors:      {q['broken_connectors']:>8}")
    print(f"  Duplicate lines:        {q['duplicate_lines']:>8}")
    print(f"  Noise patterns:         {q['noise_patterns']:>8}")
    print(f"  Headers detected:       {q['headers_detected']:>8}")
    print(f"  Tables detected:        {q['tables_detected']:>8}")
    print(f"  Lists detected:         {q['lists_detected']:>8}")
    print(f"  Avg line length:        {q['avg_line_length']:>8.1f} chars")
    print()

    print("CONFIDENCE STATS:")
    print("-" * 70)
    print(f"  Avg confidence:         {s['avg_confidence']:>8.1%}")
    print(f"  Min confidence:         {s['min_confidence']:>8.1%}")
    print(f"  Max confidence:         {s['max_confidence']:>8.1%}")
    print(f"  Pages with text layer:  {s['pages_with_text_layer']:>8}")
    print(f"  Pages below 50%:        {s['pages_below_50']:>8}")
    print(f"  Pages below 70%:        {s['pages_below_70']:>8}")
    print(f"  Total pages:            {s['total_pages']:>8}")
    print()

    # Memory stats
    mem = results.get("memory", {})
    if mem:
        print("MEMORY USAGE:")
        print("-" * 70)
        print(f"  Peak RSS:               {mem.get('peak_rss_mb', 0):>8.1f} MB")
        print(f"  End RSS:                {mem.get('end_rss_mb', 0):>8.1f} MB")
        print(f"  Start RSS:              {mem.get('start_rss_mb', 0):>8.1f} MB")
        print()

    print("=" * 70)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="PDFtoMD Benchmark")
    parser.add_argument("pdf", help="Path to PDF file")
    parser.add_argument("--classify", action="store_true", help="Enable classification")
    parser.add_argument("--dpi", type=int, default=300, help="Render DPI (default: 300)")
    parser.add_argument("--lang", default="spa", help="OCR language (default: spa)")
    parser.add_argument("--output", "-o", help="Save JSON report to file")
    args = parser.parse_args()

    print(f"Starting benchmark: {args.pdf}")
    print(f"  classify={args.classify}, dpi={args.dpi}, lang={args.lang}")
    print()

    start = time.perf_counter()
    results = benchmark_pdf(
        pdf_path=args.pdf,
        classify=args.classify,
        dpi=args.dpi,
        lang=args.lang,
    )
    elapsed = time.perf_counter() - start
    results["wall_time"] = round(elapsed, 3)

    print_report(results)

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"Report saved to: {out}")


if __name__ == "__main__":
    main()

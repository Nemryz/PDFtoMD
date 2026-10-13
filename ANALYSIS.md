# PDF to Markdown - Complete Analysis

## 1. Context Summary

**Goal**: Build a CLI tool that converts PDF files (1-300 pages) to structured Markdown, prioritizing text extraction with optional image extraction.

**Workspace**: local clone of this repository

**Test file**: a real legal/official document used locally for benchmarking.
It is protected personal data and is therefore excluded from version control
(see `.gitignore`); synthetic fixtures stand in for it in the test suite.

**User profile**: Developer building a personal tool, not a commercial product yet.

---

## 2. Architecture Analysis

### 2.1 Core Architecture (from SRS)

```
PDF → PDFReader → ContentDetector → TextExtractor/LayoutAnalyzer → DocumentModel → MarkdownRenderer → output
```

### 2.2 Key Design Decision: Intermediate Document Model

The SRS proposes a `ParsedDocument` with typed `DocumentBlock` objects. This is the **correct** architecture because:

- **Decouples extraction from rendering** — changing PyMuPDF for Marker doesn't touch the renderer
- **Enables validation** — can inspect the intermediate model before rendering
- **Supports multiple outputs** — same model can render to Markdown, HTML, or JSON
- **Testable** — each stage can be tested independently

### 2.3 Component Map

| Component | Responsibility | Risk Level |
|-----------|---------------|------------|
| `PdfReader` | Open PDF, enumerate pages | LOW |
| `ContentDetector` | Detect text layer vs scanned | MEDIUM |
| `TextExtractor` | Extract text blocks with positions | HIGH |
| `LayoutAnalyzer` | Detect headings, lists, tables, columns | HIGH |
| `ImageExtractor` | Extract embedded images, deduplicate | MEDIUM |
| `OcrEngine` | OCR for scanned pages | HIGH |
| `MarkdownRenderer` | Convert blocks to Markdown | MEDIUM |
| `MetadataGenerator` | Create metadata.json | LOW |
| `QualityValidator` | Validate output | MEDIUM |

---

## 3. Failure Modes and Edge Cases

### 3.1 PDF-Level Failures

| # | Failure Mode | Impact | Mitigation |
|---|-------------|--------|------------|
| F-1 | **Password-protected PDF** | Cannot open | Detect encryption, report error, skip file |
| F-2 | **Corrupted PDF header** | Parser crash | Validate PDF magic bytes before processing |
| F-3 | **PDF with no text layer AND no images** | Empty output | Detect, warn, skip gracefully |
| F-4 | **Extremely large PDF (>300 pages)** | Memory issues | Process page-by-page, stream output |
| F-5 | **PDF with embedded fonts (non-Unicode)** | Garbled text | Font mapping, fallback to image extraction |
| F-6 | **PDF with JavaScript** | Security risk | Disable JS execution, extract content only |
| F-7 | **PDF with DRM/permissions** | Extraction blocked | Detect, warn user about restrictions |
| F-8 | **Empty PDF (0 pages)** | Division by zero | Check page count before processing |

### 3.2 Text Extraction Failures

| # | Failure Mode | Impact | Mitigation |
|---|-------------|--------|------------|
| F-9 | **Text split across pages** | Broken paragraphs | Detect page-break artifacts, merge when logical |
| F-10 | **Multi-column layout** | Reading order wrong | Layout analysis, column detection |
| F-11 | **Footnotes/endnotes** | Separated from body | Detect footnote patterns, link references |
| F-12 | **Headers/footers mixed with body** | Duplicate text | Detect repeating patterns across pages |
| F-13 | **Tables with merged cells** | Broken table structure | Table-specific extraction, HTML table fallback |
| F-14 | **Mathematical formulas** | LaTeX or plain text | Detect formula blocks, preserve notation |
| F-15 | **Code blocks** | Indentation lost | Detect monospace fonts, preserve formatting |
| F-16 | **RTL text (Arabic, Hebrew)** | Reversed text | Detect direction, handle bidirectional text |
| F-17 | **Unicode characters outside BMP** | Replacement chars | Verify encoding handling end-to-end |
| F-18 | **Text with ligatures (fi, fl)** | Missing characters | Expand ligatures during extraction |
| F-19 | **Overlapping text blocks** | Duplicated text | Deduplicate by position + content hash |

### 3.3 Image Extraction Failures

| # | Failure Mode | Impact | Mitigation |
|---|-------------|--------|------------|
| F-20 | **Image embedded as vector** | Cannot extract as raster | Detect vector, render page region instead |
| F-21 | **Same image repeated multiple times** | Wasted space | SHA-256 deduplication |
| F-22 | **Image with transparency (PNG)** | Display issues | Preserve alpha channel, test rendering |
| F-23 | **Image referenced but missing in PDF** | Broken link in MD | Validate references, mark missing images |
| F-24 | **Very large images (>10MB)** | Slow processing, huge output | Optional resize, size warning |
| F-25 | **Image is actually a page background** | Noise extraction | Detect full-page images, skip decorative ones |

### 3.4 Markdown Generation Failures

| # | Failure Mode | Impact | Mitigation |
|---|-------------|--------|------------|
| F-26 | **Heading hierarchy broken** | Invalid structure | Validate heading levels are sequential |
| F-27 | **Unclosed code blocks** | Rendering broken | Validate backtick pairs |
| F-28 | **Special characters in filenames** | Broken image links | Sanitize filenames, use relative paths |
| F-29 | **Empty Markdown file** | No useful output | Reject empty output, report warning |
| F-30 | **Markdown with only images, no text** | Unusable without context | Warn about text-less conversion |
| F-31 | **Broken table formatting** | Readable but ugly | Validate pipe alignment, offer HTML fallback |

### 3.5 Operational Failures (PC-Specific)

| # | Failure Mode | Impact | Mitigation |
|---|-------------|--------|------------|
| F-32 | **Path with spaces (`expediente Miranda ..pdf`)** | Path parsing error | Quote all paths, test with spaces |
| F-33 | **Path with special chars (`..` in filename)** | Traversal issues | Sanitize, don't resolve relative to parent |
| F-34 | **Output directory doesn't exist** | Write failure | Create output dir automatically |
| F-35 | **Output directory is read-only** | Permission denied | Check writable before processing |
| F-36 | **Concurrent conversions** | File conflicts | Use temp files, atomic writes |
| F-37 | **Windows path length limit (260 chars)** | Truncation | Use extended-length paths or shorten names |
| F-38 | **Antivirus locks PDF file** | EACCES error | Retry with backoff, detect lock |
| F-39 | **OneDrive sync conflicts** | File locked | Detect cloud storage, warn user |
| F-40 | **Disk full during extraction** | Partial output | Check free space before writing |

### 3.6 Performance Failures

| # | Failure Mode | Impact | Mitigation |
|---|-------------|--------|------------|
| F-41 | **300-page PDF takes >10 minutes** | Poor UX | Progress indicator, page-by-page processing |
| F-42 | **OCR on every page (when not needed)** | Slow | Auto-detect pages needing OCR |
| F-43 | **Loading entire PDF into memory** | OOM crash | Stream pages, release after processing |
| F-44 | **Duplicate processing of same file** | Wasted time | Cache by SHA-256 of source file |
| F-45 | **Batch processing hangs on one file** | Stuck | Per-file timeout, continue on failure |

---

## 4. Testing Strategy

### 4.1 Test Categories

#### Category A: Unit Tests (Pure Functions)
- `slugify()` — filename generation
- `parseNNN()` — feature number parsing
- Heading level detection logic
- Filename sanitization
- Hash computation for deduplication
- Markdown special character escaping

#### Category B: Integration Tests (Real PDF → Real Output)

**B-1: Digital PDF tests (text layer present)**
| Test | PDF Type | Validates |
|------|----------|-----------|
| B-1a | Simple 1-page text PDF | Basic extraction, clean Markdown |
| B-1b | Multi-page document (10+ pages) | Page ordering, paragraph merging |
| B-1c | Multi-column layout | Reading order detection |
| B-1d | PDF with headings (H1-H6) | Heading hierarchy preservation |
| B-1e | PDF with bullet lists | List structure preservation |
| B-1f | PDF with numbered lists | Ordered list numbering |
| B-1g | PDF with tables | Table extraction (Markdown or HTML) |
| B-1h | PDF with images | Image extraction + MD references |
| B-1i | PDF with hyperlinks | Link preservation |
| B-1j | PDF with footnotes | Footnote handling |
| B-1k | PDF with code blocks | Monospace detection |
| B-1l | PDF with math formulas | Formula preservation |
| B-1m | PDF with headers/footers | Header/footer exclusion |
| B-1n | PDF with page numbers | Page number exclusion |
| B-1o | PDF with TOC | Table of contents handling |

**B-2: Scanned PDF tests (image-based)**
| Test | PDF Type | Validates |
|------|----------|-----------|
| B-2a | Clean scanned text | OCR extraction accuracy |
| B-2b | Low-resolution scan | OCR fallback handling |
| B-2c | Skewed scan | Deskew before OCR |
| B-2d | Mixed text + scan pages | Hybrid extraction |

**B-3: Edge case PDF tests**
| Test | PDF Type | Validates |
|------|----------|-----------|
| B-3a | PDF with password | Error handling, graceful skip |
| B-3b | Corrupted PDF | Error handling, partial recovery |
| B-3c | Empty PDF (0 pages) | Edge case handling |
| B-3d | PDF with only images | Image extraction, no text warning |
| B-3e | PDF with embedded fonts | Font handling |
| B-3f | PDF with Unicode (CJK, Arabic) | Encoding handling |
| B-3g | PDF with special filename (`..`, spaces) | Path handling |
| B-3h | Very large PDF (300 pages) | Performance, memory |
| B-3i | PDF with DRM | Detection, warning |
| B-3j | PDF with JavaScript | Security, content extraction |

**B-4: Output validation tests**
| Test | Validates |
|------|-----------|
| B-4a | Markdown is valid UTF-8 |
| B-4b | Markdown is not empty if PDF has content |
| B-4c | Image references point to existing files |
| B-4d | No duplicate paragraphs (unless intentional) |
| B-4e | Heading levels are sequential (no jumps) |
| B-4f | metadata.json is valid JSON |
| B-4g | metadata.json page count matches PDF |
| B-4h | All extracted images have valid SHA-256 |

**B-5: CLI tests**
| Test | Validates |
|------|-----------|
| B-5a | `pdfmd convert file.pdf -o ./out` works |
| B-5b | `--extract-images` flag works |
| B-5c | `--ocr auto` flag works |
| B-5d | `--overwrite` flag works |
| B-5e | `--log-level debug` shows verbose output |
| B-5f | Error messages are clear and actionable |
| B-5g | Exit code 0 on success, 1 on error |
| B-5h | Batch mode processes multiple files |

**B-6: Windows-specific tests**
| Test | Validates |
|------|-----------|
| B-6a | Paths with spaces work correctly |
| B-6b | Paths with special characters work |
| B-6c | Long paths (>260 chars) are handled |
| B-6d | OneDrive/synced folders work |
| B-6e | File permissions are checked |
| B-6f | Output dir creation works |

### 4.2 Test Data Requirements

Since we can't include copyrighted PDFs, create test fixtures:

```
tests/fixtures/
├── simple-text.pdf          # 1-page, plain text
├── multi-page.pdf           # 5+ pages, structured
├── multi-column.pdf         # 2-column layout
├── with-images.pdf          # PDF with embedded images
├── with-tables.pdf          # PDF with tables
├── scanned.pdf              # Image-based text
├── password-protected.pdf   # Encrypted PDF
├── corrupted.pdf            # Invalid PDF structure
├── empty.pdf                # 0 pages
├── unicode.pdf              # CJK/Arabic text
├── special-filename.pdf     # Test path handling
└── expediente Miranda ..pdf # Real-world test file
```

### 4.3 Performance Benchmarks

| Metric | Target | How to Measure |
|--------|--------|----------------|
| 1-page digital PDF | < 2 seconds | Time CLI invocation |
| 10-page digital PDF | < 10 seconds | Time CLI invocation |
| 100-page digital PDF | < 60 seconds | Time CLI invocation |
| 300-page digital PDF | < 3 minutes | Time CLI invocation |
| Memory usage (300 pages) | < 500MB | Process monitor |
| Image extraction (10 images) | < 5 seconds | Time extraction |

### 4.4 Test Execution Commands

```bash
# Unit tests only
python -m pytest tests/unit/ -v

# Integration tests
python -m pytest tests/integration/ -v

# All tests with coverage
python -m pytest --cov=pdfmd --cov-report=html

# Performance tests
python -m pytest tests/performance/ -v --benchmark-only

# Windows-specific
python -m pytest tests/integration/test_windows_paths.py -v
```

---

## 5. Risk Analysis

### 5.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **R-1: PyMuPDF AGPL license** | CERTAIN | MEDIUM | Use PyMuPDF4LLM (MIT) or check Marker's license |
| **R-2: Layout detection is unreliable** | HIGH | HIGH | Start with simple heuristics, improve iteratively |
| **R-3: OCR quality varies by language** | MEDIUM | MEDIUM | Test with Spanish + English, make language configurable |
| **R-4: Memory usage on large PDFs** | MEDIUM | HIGH | Page-by-page processing, explicit memory release |
| **R-5: Windows path issues** | HIGH | MEDIUM | Test on Windows from day 1, use pathlib |
| **R-6: Font encoding issues** | MEDIUM | HIGH | Test with real-world PDFs early |
| **R-7: Table detection fails on complex tables** | HIGH | LOW | Accept imperfection, offer HTML fallback |
| **R-8: Image extraction misses images** | MEDIUM | MEDIUM | Validate against page renders |

### 5.2 Project Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **R-9: Scope creep (adding features too early)** | HIGH | HIGH | Strict MVP: text + images + Markdown only |
| **R-10: Over-engineering architecture** | MEDIUM | HIGH | Start with 3 files, not 15 modules |
| **R-11: No real PDFs for testing** | LOW | HIGH | Use `expediente Miranda ..pdf` + generated fixtures |
| **R-12: Choosing wrong backend** | MEDIUM | MEDIUM | Try PyMuPDF first, switch if needed |
| **R-13: Abandoning project due to complexity** | MEDIUM | HIGH | Ship MVP in 1 week, iterate after |

### 5.3 Dependency Risks

| Dependency | License | Risk | Alternative |
|------------|---------|------|-------------|
| PyMuPDF | AGPL-3.0 | Commercial use restricted | PyMuPDF4LLM (MIT) |
| marker-pdf | GPL-3.0 | Must open-source modifications | Custom wrapper |
| Tesseract | Apache-2.0 | Safe | PaddleOCR, Surya |
| Pillow | HPND | Safe | None needed |
| Typer | BSD | Safe | Click, argparse |
| Pydantic | MIT | Safe | dataclasses |

---

## 6. Recommended MVP Scope

### Week 1: Core Pipeline
1. PDF reader (PyMuPDF4LLM)
2. Text extraction (basic, no layout)
3. Image extraction (embedded only)
4. Markdown renderer (headings + paragraphs + images)
5. metadata.json generation
6. CLI with `convert` command

### Week 2: Polish
7. Layout detection (headings, lists)
8. Quality validation
9. Error handling
10. Test suite
11. README

### Week 3+: Iteration
12. OCR support
13. Table extraction
14. Batch mode
15. Advanced features

---

## 7. Key Decisions to Make Before Implementation

1. **Primary backend**: PyMuPDF4LLM vs Marker vs custom?
2. **License**: MIT for the tool itself?
3. **Python version**: 3.11+ or 3.10+?
4. **Package manager**: pip, poetry, or uv?
5. **Test framework**: pytest or unittest?
6. **CLI framework**: Typer or argparse?

---

## 8. Success Criteria

The MVP is successful when:

- [ ] Can convert `expediente Miranda ..pdf` to readable Markdown
- [ ] Text is complete and in correct reading order
- [ ] Images are extracted and linked in Markdown
- [ ] metadata.json is generated with correct page count
- [ ] CLI runs on Windows without errors
- [ ] All tests pass
- [ ] Processing time < 30 seconds for the test PDF

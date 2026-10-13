# pdfmd

Convert scanned PDF documents to structured Markdown with OCR and signature detection.

## Features

- **OCR Text Extraction**: Converts scanned PDFs to text using Tesseract
- **Structured Markdown**: Detects headings, paragraphs, and lists
- **Image Extraction**: Extracts and deduplicates embedded images
- **Signature Detection**: Identifies signature regions and matches against expected signers
- **Metadata Generation**: Creates `metadata.json` with conversion stats
- **Windows Support**: Handles paths with spaces and special characters

## Installation

### Prerequisites

- Python 3.11+
- Tesseract OCR (see [INSTALL.md](INSTALL.md) for installation guide)

### Install pdfmd

```bash
cd PDFtoMD
pip install -e .
```

## Usage

### Basic conversion

```bash
pdfmd convert document.pdf
```

### Custom output path

```bash
pdfmd convert document.pdf -o ./output/document.md
```

### With signature detection

```bash
pdfmd convert document.pdf --signers "Juan Pérez,María García"
```

### Convert specific pages

```bash
pdfmd convert document.pdf --pages "0,1,2,3,4"
```

### Show PDF info

```bash
pdfmd info document.pdf
```

### Show version

```bash
pdfmd --version
```

## Output Files

| File | Description |
|------|-------------|
| `document.md` | Structured Markdown with OCR text |
| `metadata.json` | Conversion stats (pages, confidence, time) |
| `signature_report.md` | Signature detection report |
| `signature_report.json` | Signature data in JSON format |
| `images/` | Extracted images (if any) |

## CLI Options

```
Usage: pdfmd [OPTIONS] INPUT_PATH

Options:
  -o, --output PATH     Output Markdown file path
  -l, --lang TEXT        OCR language (default: spa)
  -d, --dpi INTEGER      Render DPI (default: 300)
  -s, --signers TEXT     Comma-separated list of expected signers
  -p, --pages TEXT       Pages to process (e.g., '0,1,2' or '0-5')
  -v, --version          Show version
  --help                 Show this message and exit
```

## Development

### Run tests

```bash
pytest tests/ -v
```

### Run lint

```bash
ruff check pdfmd/
```

## License

MIT

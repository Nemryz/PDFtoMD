# Installing Tesseract OCR for pdfmd

pdfmd requires Tesseract OCR to extract text from scanned PDFs.

## Windows

### Option 1: Direct download (recommended)

1. Download the installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer (default path: `C:\Program Files\Tesseract-OCR\`)
3. During installation, select the **Spanish** language pack

### Option 2: With Chocolatey

```bash
choco install tesseract
```

### Verify installation

```bash
tesseract --version
```

### Install Spanish language pack

If you didn't select Spanish during installation:

```bash
# Download spa.traineddata from:
# https://github.com/tesseract-ocr/tessdata/raw/main/spa.traineddata
# Place it in: C:\Program Files\Tesseract-OCR\tessdata\
```

## Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-spa
```

## macOS

```bash
brew install tesseract tesseract-lang
```

## Verify pdfmd can find Tesseract

```bash
python -m pdfmd --version
```

If Tesseract is not found, you can specify the path:

```bash
python -m pdfmd convert document.pdf --tesseract-path "C:\Program Files\Tesseract-OCR\tesseract.exe"
```

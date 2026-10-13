"""
analyze_low_confidence.py — Analyzes why certain pages have low OCR confidence.

Tests different OCR parameters on problematic pages to find optimal configuration.
"""

import json
import time
from pathlib import Path

import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import pymupdf


def get_tesseract_path():
    """Auto-detect Tesseract path on Windows."""
    import shutil
    tesseract_cmd = shutil.which("tesseract")
    if tesseract_cmd:
        return tesseract_cmd
    
    # Try common Windows paths
    possible_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    for path in possible_paths:
        if Path(path).exists():
            return path
    
    return "tesseract"


def preprocess_image(img, method="enhance"):
    """Apply different preprocessing methods to improve OCR."""
    
    if method == "original":
        return img
    
    elif method == "enhance":
        # Enhance contrast and sharpness
        img = ImageEnhance.Contrast(img).enhance(1.5)
        img = ImageEnhance.Sharpness(img).enhance(2.0)
        return img
    
    elif method == "grayscale":
        # Convert to grayscale and enhance
        img = img.convert("L")
        img = ImageEnhance.Contrast(img).enhance(2.0)
        img = img.point(lambda x: 0 if x < 128 else 255)
        return img
    
    elif method == "denoise":
        # Denoise and enhance
        img = img.filter(ImageFilter.MedianFilter(size=3))
        img = ImageEnhance.Contrast(img).enhance(1.8)
        img = ImageEnhance.Sharpness(img).enhance(1.5)
        return img
    
    elif method == "aggressive":
        # Aggressive preprocessing for very noisy images
        img = img.convert("L")
        img = img.filter(ImageFilter.MedianFilter(size=3))
        img = ImageEnhance.Contrast(img).enhance(2.5)
        img = img.point(lambda x: 0 if x < 140 else 255)
        return img
    
    return img


def test_ocr_params(image_path, tesseract_path, page_num):
    """Test different OCR parameters on a single image."""
    
    results = []
    img = Image.open(image_path)
    
    # Test different preprocessing methods
    methods = ["original", "enhance", "grayscale", "denoise", "aggressive"]
    
    # Test different PSM modes
    psm_modes = [3, 4, 6, 11]  # 3=auto, 4=single column, 6=block, 11=sparse
    
    print(f"\nPage {page_num}: Testing {len(methods)} methods x {len(psm_modes)} PSM modes")
    
    for method in methods:
        processed_img = preprocess_image(img, method)
        
        for psm in psm_modes:
            config = f"--psm {psm}"
            
            try:
                # Get OCR result with confidence
                data = pytesseract.image_to_data(
                    processed_img,
                    lang="eng+spa",
                    config=config,
                    output_type=pytesseract.Output.DICT
                )
                
                # Calculate average confidence
                confidences = [int(c) for c in data["conf"] if int(c) > 0]
                avg_conf = sum(confidences) / len(confidences) if confidences else 0
                text = pytesseract.image_to_string(processed_img, lang="eng+spa", config=config)
                text_len = len(text.strip())
                
                results.append({
                    "method": method,
                    "psm": psm,
                    "confidence": avg_conf,
                    "text_length": text_len,
                    "text_preview": text[:100] if text else ""
                })
                
            except Exception as e:
                results.append({
                    "method": method,
                    "psm": psm,
                    "confidence": 0,
                    "text_length": 0,
                    "error": str(e)
                })
    
    # Sort by confidence
    results.sort(key=lambda x: x["confidence"], reverse=True)
    
    # Show top 3 results
    print(f"  Top 3 configurations:")
    for i, r in enumerate(results[:3]):
        print(f"    {i+1}. {r['method']}/psm{r['psm']}: {r['confidence']:.1f}% confidence, {r['text_length']} chars")
    
    return results


def main():
    """Analyze low confidence pages and test optimizations."""
    
    tesseract_path = get_tesseract_path()
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
    
    print("=" * 70)
    print("LOW CONFIDENCE PAGE ANALYSIS")
    print("=" * 70)
    
    # Load metadata to find low confidence pages
    metadata_path = Path("output/metadata.json")
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        warnings = metadata.get("warnings", [])
        
        # Extract low confidence pages
        low_conf_pages = []
        for w in warnings:
            if "Low OCR confidence" in w:
                import re
                match = re.search(r'page (\d+): ([\d.]+)', w)
                if match:
                    page_num = int(match.group(1))
                    confidence = float(match.group(2))
                    if confidence < 0.4:
                        low_conf_pages.append((page_num, confidence))
        
        print(f"\nFound {len(low_conf_pages)} pages with confidence < 40%")
    else:
        # Test a few sample pages
        low_conf_pages = [(18, 0.0), (40, 0.0), (64, 0.32)]
    
    # Test on first 5 problematic pages
    test_pages = low_conf_pages[:5]
    
    pdf_path = "expediente Miranda ..pdf"
    doc = pymupdf.open(pdf_path)
    
    all_results = {}
    
    for page_num, orig_conf in test_pages:
        print(f"\n{'='*70}")
        print(f"Testing page {page_num} (original confidence: {orig_conf:.1%})")
        print(f"{'='*70}")
        
        # Render page at different DPIs
        page = doc[page_num - 1]
        
        for dpi in [300, 400, 600]:
            zoom = dpi / 72
            mat = pymupdf.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            
            img_path = f"output/test_page_{page_num}_dpi{dpi}.png"
            pix.save(img_path)
            
            print(f"\n  DPI {dpi}:")
            results = test_ocr_params(img_path, tesseract_path, page_num)
            
            all_results[f"page_{page_num}_dpi{dpi}"] = {
                "original_confidence": orig_conf,
                "dpi": dpi,
                "results": results[:5]  # Keep top 5
            }
    
    doc.close()
    
    # Save analysis results
    output_path = Path("output/ocr_analysis.json")
    output_path.write_text(json.dumps(all_results, indent=2, ensure_ascii=False), encoding="utf-8")
    
    print(f"\n{'='*70}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*70}")
    print(f"Results saved to: {output_path}")
    
    # Find best configuration across all pages
    best_configs = {}
    for key, data in all_results.items():
        for r in data["results"]:
            config_key = f"{r['method']}/psm{r['psm']}"
            if config_key not in best_configs:
                best_configs[config_key] = []
            best_configs[config_key].append(r["confidence"])
    
    print(f"\nBest configurations (average confidence across all test pages):")
    config_avg = [(k, sum(v)/len(v)) for k, v in best_configs.items()]
    config_avg.sort(key=lambda x: x[1], reverse=True)
    
    for config, avg in config_avg[:5]:
        print(f"  {config}: {avg:.1f}%")


if __name__ == "__main__":
    main()

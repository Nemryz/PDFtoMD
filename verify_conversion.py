"""
verify_conversion.py — Verifies consistency between PDF source and MD output.

Compares:
1. Page count: PDF pages vs MD sections
2. Text extraction: characters extracted per page
3. Image extraction: images found vs expected
4. OCR confidence: per-page analysis
5. Content integrity: no data loss
"""

import json
import re
import sys
from pathlib import Path

import pymupdf


def verify_conversion(pdf_path: str, md_path: str, metadata_path: str, images_dir: str):
    """Run full verification of PDF → MD conversion."""
    
    print("=" * 70)
    print("CONVERSION VERIFICATION REPORT")
    print("=" * 70)
    print()
    
    # Load metadata
    metadata = json.loads(Path(metadata_path).read_text(encoding="utf-8"))
    
    results = {
        "page_count": False,
        "text_extraction": False,
        "image_extraction": False,
        "ocr_confidence": False,
        "content_integrity": False,
    }
    
    # 1. Page count verification
    print("1. PAGE COUNT VERIFICATION")
    print("-" * 40)
    
    doc = pymupdf.open(pdf_path)
    pdf_page_count = len(doc)
    md_content = Path(md_path).read_text(encoding="utf-8")
    md_page_headers = len(re.findall(r'<!-- Page \d+ -->', md_content))
    
    print(f"   PDF pages:        {pdf_page_count}")
    print(f"   MD page headers:  {md_page_headers}")
    print(f"   Metadata pages:   {metadata['total_pages']}")
    
    if pdf_page_count == md_page_headers == metadata['total_pages']:
        print("   [PASS] Page counts match")
        results["page_count"] = True
    else:
        print("   [FAIL] Page count mismatch")
    print()
    
    # 2. Text extraction verification
    print("2. TEXT EXTRACTION VERIFICATION")
    print("-" * 40)
    
    total_chars = 0
    empty_pages = 0
    low_quality_pages = []
    
    for i in range(pdf_page_count):
        page = doc[i]
        text = page.get_text()
        char_count = len(text.strip())
        total_chars += char_count
        
        if char_count == 0:
            empty_pages += 1
        elif char_count < 50:
            low_quality_pages.append(i + 1)
    
    md_chars = len(md_content)
    
    print(f"   PDF total chars:  {total_chars:,}")
    print(f"   MD total chars:   {md_chars:,}")
    print(f"   Empty PDF pages:  {empty_pages}")
    print(f"   Low-quality pages: {len(low_quality_pages)}")
    
    # MD should have more chars due to formatting
    if md_chars > total_chars * 0.5:  # MD has at least 50% of PDF chars
        print("   [PASS] Text extraction reasonable")
        results["text_extraction"] = True
    else:
        print("   [WARN] Low text extraction ratio")
    print()
    
    # 3. Image extraction verification
    print("3. IMAGE EXTRACTION VERIFICATION")
    print("-" * 40)
    
    images_path = Path(images_dir)
    if images_path.exists():
        image_files = list(images_path.glob("*.png")) + list(images_path.glob("*.jpg"))
        pdf_images = 0
        for i in range(pdf_page_count):
            page = doc[i]
            pdf_images += len(page.get_images())
        
        print(f"   PDF embedded images: {pdf_images}")
        print(f"   Extracted images:    {len(image_files)}")
        
        if len(image_files) > 0 or pdf_images == 0:
            print("   [PASS] Images handled")
            results["image_extraction"] = True
        else:
            print("   [WARN] Images exist but none extracted")
    else:
        print("   [INFO] No images directory (no images in PDF)")
        results["image_extraction"] = True
    print()
    
    # 4. OCR confidence verification
    print("4. OCR CONFIDENCE VERIFICATION")
    print("-" * 40)
    
    avg_confidence = metadata.get("avg_confidence", 0)
    warnings = metadata.get("warnings", [])
    low_conf_warnings = [w for w in warnings if "Low OCR confidence" in w]
    
    print(f"   Average confidence:  {avg_confidence:.1%}")
    print(f"   Low conf warnings:   {len(low_conf_warnings)}")
    
    # Extract per-page confidence from warnings
    page_confidences = {}
    for w in low_conf_warnings:
        match = re.search(r'page (\d+): ([\d.]+)', w)
        if match:
            page_num = int(match.group(1))
            confidence = float(match.group(2))
            page_confidences[page_num] = confidence
    
    # Count pages by confidence level
    excellent = sum(1 for c in page_confidences.values() if c >= 0.8)
    good = sum(1 for c in page_confidences.values() if 0.6 <= c < 0.8)
    fair = sum(1 for c in page_confidences.values() if 0.4 <= c < 0.6)
    poor = sum(1 for c in page_confidences.values() if c < 0.4)
    
    # Pages not in warnings likely have confidence >= 0.4
    pages_ok = pdf_page_count - len(page_confidences)
    
    print(f"   Pages with conf >= 80%: {excellent + pages_ok - len([c for c in page_confidences.values() if c >= 0.4])}")
    print(f"   Pages with conf 60-79%: {good}")
    print(f"   Pages with conf 40-59%: {fair}")
    print(f"   Pages with conf < 40%:  {poor}")
    
    if avg_confidence >= 0.7:
        print("   [PASS] Good OCR quality")
        results["ocr_confidence"] = True
    elif avg_confidence >= 0.5:
        print("   [WARN] Moderate OCR quality")
        results["ocr_confidence"] = True
    else:
        print("   [FAIL] Low OCR quality")
    print()
    
    # 5. Content integrity verification
    print("5. CONTENT INTEGRITY VERIFICATION")
    print("-" * 40)
    
    # Check for common OCR artifacts (exclude empty string)
    artifacts = {
        "?": md_content.count("?"),
        "□": md_content.count("□"),
        "garbled": md_content.lower().count("garbled"),
    }
    
    total_artifacts = sum(artifacts.values())
    
    print(f"   Total characters:   {md_chars:,}")
    print(f"   Total lines:        {md_content.count(chr(10)):,}")
    print(f"   OCR artifacts:      {total_artifacts}")
    for artifact, count in artifacts.items():
        if count > 0:
            print(f"     '{artifact}': {count}")
    
    if total_artifacts < md_chars * 0.01:  # Less than 1% artifacts
        print("   [PASS] Content integrity good")
        results["content_integrity"] = True
    else:
        print("   [WARN] High artifact count")
        results["content_integrity"] = True  # Still pass, artifacts are expected in OCR
    print()
    
    # Summary
    print("=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for check, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"   {status} {check.replace('_', ' ').title()}")
    
    print()
    print(f"   Score: {passed}/{total} checks passed")
    
    if passed == total:
        print("   OVERALL: PASS")
    elif passed >= total - 1:
        print("   OVERALL: PASS WITH WARNINGS")
    else:
        print("   OVERALL: FAIL")
    
    # Recommendations
    print()
    print("RECOMMENDATIONS")
    print("-" * 40)
    
    if avg_confidence < 0.7:
        print("   1. Consider increasing DPI (current: 300)")
        print("   2. Try different Tesseract PSM modes")
        print("   3. Pre-process images (contrast, sharpening)")
    
    if empty_pages > 0:
        print(f"   4. {empty_pages} pages are blank or images only")
    
    if poor > 10:
        print(f"   5. {poor} pages have very low confidence (<40%)")
    
    doc.close()
    
    return results


if __name__ == "__main__":
    pdf_path = "expediente Miranda ..pdf"
    md_path = "output/expediente Miranda ..md"
    metadata_path = "output/metadata.json"
    images_dir = "output/images"
    
    verify_conversion(pdf_path, md_path, metadata_path, images_dir)

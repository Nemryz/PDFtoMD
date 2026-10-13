"""
PDFtoMD - Clarify Phase Validator
Ejecuta este script para verificar que las dependencias críticas funcionan.

Uso:
    python validate_environment.py

Requisitos:
    pip install pymupdf pytesseract pillow

Salida esperada:
    ✅ Todo listo para continuar con el SDD
    o
    ❌ Problemas detectados que resolver antes de continuar
"""

import sys
import os
import subprocess
from pathlib import Path

# Colores para terminal
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def check(name: str, passed: bool, detail: str = ""):
    """Imprime resultado de una verificación."""
    icon = f"{GREEN}✅{RESET}" if passed else f"{RED}❌{RESET}"
    print(f"  {icon} {name}")
    if detail:
        print(f"     {YELLOW}→ {detail}{RESET}")
    return passed

def separator():
    print()

# ============================================================
# VERIFICACIÓN 1: Python version
# ============================================================
print(f"\n{'='*60}")
print("VERIFICACIÓN 1: Python version")
print(f"{'='*60}")

py_version = sys.version_info
check(
    "Python 3.11+ instalado",
    py_version >= (3, 11),
    f"Versión actual: {py_version.major}.{py_version.minor}.{py_version.micro}"
)

# ============================================================
# VERIFICACIÓN 2: PyMuPDF (fitz)
# ============================================================
print(f"\n{'='*60}")
print("VERIFICACIÓN 2: PyMuPDF (librería de PDF)")
print(f"{'='*60}")

try:
    import fitz
    check("PyMuPDF importado correctamente", True, f"Versión: {fitz.__version__}")
    
    # Probar abrir un PDF de ejemplo
    test_pdf = Path(__file__).parent / "expediente Miranda ..pdf"
    if test_pdf.exists():
        doc = fitz.open(str(test_pdf))
        check(
            "PDF de prueba se puede abrir",
            True,
            f"Páginas: {len(doc)}, Título: {doc.metadata.get('title', 'N/A')}"
        )
        
        # Verificar si tiene text layer
        page = doc[0]
        text = page.get_text()
        has_text = len(text.strip()) > 10
        check(
            "PDF tiene text layer (texto seleccionable)",
            has_text,
            f"Texto extraído de página 1: {len(text)} caracteres" + 
            (" ← OCR será necesario" if not has_text else " ← Texto directo disponible")
        )
        
        # Probar renderizado a imagen
        try:
            pix = page.get_pixmap(dpi=300)
            check(
                "Renderizado a 300 DPI funciona",
                True,
                f"Imagen: {pix.width}x{pix.height} píxeles"
            )
        except Exception as e:
            check("Renderizado a 300 DPI", False, str(e))
        
        doc.close()
    else:
        check("PDF de prueba encontrado", False, f"No se encontró: {test_pdf}")
        
except ImportError:
    check("PyMuPDF importado", False, "Ejecuta: pip install pymupdf")
except Exception as e:
    check("PyMuPDF funciona", False, str(e))

# ============================================================
# VERIFICACIÓN 3: Tesseract OCR
# ============================================================
print(f"\n{'='*60}")
print("VERIFICACIÓN 3: Tesseract OCR")
print(f"{'='*60}")

try:
    import pytesseract
    check("pytesseract importado", True)
    
    # Buscar ejecutable de Tesseract
    tesseract_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expanduser(r"~\AppData\Local\Tesseract-OCR\tesseract.exe"),
    ]
    
    tesseract_found = False
    tesseract_path = None
    
    for path in tesseract_paths:
        if os.path.exists(path):
            tesseract_found = True
            tesseract_path = path
            pytesseract.pytesseract.tesseract_cmd = path
            break
    
    if not tesseract_found:
        # Intentar encontrar en PATH
        try:
            result = subprocess.run(
                ["tesseract", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                tesseract_found = True
                check("Tesseract encontrado en PATH", True, result.stdout.strip().split('\n')[0])
        except:
            pass
    
    if tesseract_found and tesseract_path:
        check("Tesseract ejecutable encontrado", True, tesseract_path)
        
        # Verificar idiomas disponibles
        try:
            result = subprocess.run(
                [tesseract_path, "--list-langs"],
                capture_output=True,
                text=True,
                timeout=5
            )
            langs = result.stdout.strip().split('\n')[1:]  # Skip header
            has_spa = any('spa' in lang for lang in langs)
            check(
                "Idioma español (spa) disponible",
                has_spa,
                f"Idiomas instalados: {', '.join(langs[:5])}..."
            )
        except Exception as e:
            check("Verificar idiomas", False, str(e))
            
    elif not tesseract_found:
        check("Tesseract ejecutable encontrado", False, 
              "Instalar desde: https://github.com/UB-Mannheim/tesseract/wiki")
        
except ImportError:
    check("pytesseract importado", False, "Ejecuta: pip install pytesseract")
except Exception as e:
    check("Tesseract funciona", False, str(e))

# ============================================================
# VERIFICACIÓN 4: Pillow (para imágenes)
# ============================================================
print(f"\n{'='*60}")
print("VERIFICACIÓN 4: Pillow (procesamiento de imágenes)")
print(f"{'='*60}")

try:
    from PIL import Image
    check("Pillow importado correctamente", True)
    
    # Crear imagen de prueba
    try:
        img = Image.new('RGB', (100, 100), color='red')
        check("Puede crear imágenes", True)
    except Exception as e:
        check("Crear imágenes", False, str(e))
        
except ImportError:
    check("Pillow importado", False, "Ejecuta: pip install Pillow")

# ============================================================
# VERIFICACIÓN 5: Pydantic + Typer + Rich
# ============================================================
print(f"\n{'='*60}")
print("VERIFICACIÓN 5: Dependencias del CLI")
print(f"{'='*60}")

try:
    import pydantic
    check("Pydantic importado", True, f"Versión: {pydantic.__version__}")
except ImportError:
    check("Pydantic importado", False, "Ejecuta: pip install pydantic")

try:
    import typer
    check("Typer importado", True, f"Versión: {typer.__version__}")
except ImportError:
    check("Typer importado", False, "Ejecuta: pip install typer")

try:
    import rich
    check("Rich importado", True, f"Versión: {rich.__version__}")
except ImportError:
    check("Rich importado", False, "Ejecuta: pip install rich")

# ============================================================
# VERIFICACIÓN 6: Prueba de OCR real
# ============================================================
print(f"\n{'='*60}")
print("VERIFICACIÓN 6: Prueba de OCR real")
print(f"{'='*60}")

if tesseract_found:
    try:
        import pytesseract
        from PIL import Image
        
        # Crear imagen con texto de prueba
        img = Image.new('RGB', (400, 100), color='white')
        # No podemos escribir texto sin fuente, pero podemos probar que OCR funciona
        # con una imagen vacía (debería devolver texto vacío, no error)
        
        text = pytesseract.image_to_string(img, lang='spa')
        check(
            "OCR funciona con pytesseract",
            True,
            f"Texto extraído de imagen vacía: '{text.strip()}' (esperado: vacío)"
        )
        
        # Probar con el PDF real si existe
        test_pdf = Path(__file__).parent / "expediente Miranda ..pdf"
        if test_pdf.exists():
            import fitz
            doc = fitz.open(str(test_pdf))
            page = doc[0]
            pix = page.get_pixmap(dpi=200)
            
            # Convertir pixmap a PIL Image
            img_data = pix.tobytes("png")
            from io import BytesIO
            pil_img = Image.open(BytesIO(img_data))
            
            text = pytesseract.image_to_string(pil_img, lang='spa')
            check(
                "OCR funciona con PDF real (página 1)",
                len(text.strip()) > 0,
                f"Texto extraído: {len(text.strip())} caracteres" +
                (f"\n     Primera línea: '{text.strip()[:80]}...'" if text.strip() else "")
            )
            doc.close()
        
    except Exception as e:
        check("OCR real funciona", False, str(e))
else:
    check("OCR real", False, "Tesseract no encontrado, saltando prueba")

# ============================================================
# RESUMEN
# ============================================================
print(f"\n{'='*60}")
print("RESUMEN")
print(f"{'='*60}")

print(f"""
{YELLOW}Si todas las verificaciones muestran ✅, estamos listos para continuar.

Si hay ❌, necesitas instalar las dependencias faltantes:

  pip install pymupdf pytesseract pillow pydantic typer rich

Y para Tesseract OCR, descargar el installer desde:
  https://github.com/UB-Mannheim/tesseract/wiki

Después de instalar, ejecuta este script de nuevo.
{RESET}""")

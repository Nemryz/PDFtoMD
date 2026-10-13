
from __future__ import annotations

from pathlib import Path

import pymupdf

FIXTURE_DIR = Path(__file__).parent / "pdfs"


def _ensure_dirs():
    for subdir in ["valid", "edge_cases", "legal", "benchmarks"]:
        (FIXTURE_DIR / subdir).mkdir(parents=True, exist_ok=True)


def _add_text_page(doc: pymupdf.Document, text: str, font_size: float = 12):
    page = doc.new_page(width=595, height=842)  # A4
    page.insert_text((72, 72), text, fontsize=font_size)
    return page


def _add_multiline_page(doc: pymupdf.Document, lines: list[str], font_size: float = 12):
    page = doc.new_page(width=595, height=842)
    y = 72
    for line in lines:
        page.insert_text((72, y), line, fontsize=font_size)
        y += font_size + 6
    return page


# === VALID PDFs ===


def create_simple_1page():
    doc = pymupdf.open()
    text = "Documento de prueba con una sola pagina.\n"
    text += "Este es el contenido del documento."
    _add_text_page(doc, text)
    doc.save(str(FIXTURE_DIR / "valid" / "simple_1page.pdf"))
    doc.close()


def create_simple_5pages():
    doc = pymupdf.open()
    for i in range(5):
        _add_text_page(doc, f"Pagina {i + 1} de 5.\nContenido de la pagina numero {i + 1}.")
    doc.save(str(FIXTURE_DIR / "valid" / "simple_5pages.pdf"))
    doc.close()


def create_with_images():
    doc = pymupdf.open()
    _add_text_page(doc, "Documento con imagenes.")
    # Create a simple colored rectangle as image
    page = doc.new_page(width=595, height=842)
    shape = page.new_shape()
    shape.draw_rect(pymupdf.Rect(100, 200, 400, 500))
    shape.finish(color=(0, 0, 1), fill=(0.5, 0.5, 1))
    shape.commit()
    doc.save(str(FIXTURE_DIR / "valid" / "with_images.pdf"))
    doc.close()


def create_with_tables():
    doc = pymupdf.open()
    lines = [
        "Documento con tabla:",
        "",
        "| Nombre   | Edad | Ciudad     |",
        "|----------|------|------------|",
        "| Juan     | 30   | Madrid     |",
        "| Maria    | 25   | Barcelona  |",
        "| Carlos   | 35   | Valencia   |",
    ]
    _add_multiline_page(doc, lines)
    doc.save(str(FIXTURE_DIR / "valid" / "with_tables.pdf"))
    doc.close()


def create_mixed_content():
    doc = pymupdf.open()
    lines = [
        "# Titulo del Documento",
        "",
        "Este es un parrafo de texto normal con contenido variado.",
        "",
        "## Seccion 1",
        "",
        "- Item uno",
        "- Item dos",
        "- Item tres",
        "",
        "## Seccion 2",
        "",
        "1. Primero",
        "2. Segundo",
        "3. Tercero",
    ]
    _add_multiline_page(doc, lines)
    doc.save(str(FIXTURE_DIR / "valid" / "mixed_content.pdf"))
    doc.close()


def create_multi_column():
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    # Two columns of text
    col1 = [
        "Columna Izquierda:",
        "Primera linea izq.",
        "Segunda linea izq.",
        "Tercera linea izq.",
    ]
    col2 = [
        "Columna Derecha:",
        "Primera linea der.",
        "Segunda linea der.",
        "Tercera linea der.",
    ]
    y = 72
    for line in col1:
        page.insert_text((72, y), line, fontsize=11)
        y += 17
    y = 72
    for line in col2:
        page.insert_text((300, y), line, fontsize=11)
        y += 17
    doc.save(str(FIXTURE_DIR / "valid" / "multi_column.pdf"))
    doc.close()


def create_rotated_pages():
    doc = pymupdf.open()
    _add_text_page(doc, "Pagina normal sin rotacion.")
    page = doc.new_page(width=595, height=842)
    page.set_rotation(90)
    page.insert_text((72, 72), "Pagina rotada 90 grados.", fontsize=12)
    doc.save(str(FIXTURE_DIR / "valid" / "rotated_pages.pdf"))
    doc.close()


def create_low_quality():
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    # Very small text
    page.insert_text((72, 72), "Texto extremadamente pequeno que sera dificil de leer.", fontsize=4)
    page.insert_text((72, 100), "Segunda linea tambien pequena.", fontsize=4)
    doc.save(str(FIXTURE_DIR / "valid" / "low_quality.pdf"))
    doc.close()


def create_large_300pages():
    doc = pymupdf.open()
    for i in range(300):
        _add_text_page(doc, f"Pagina {i + 1} de 300.\nContenido de prueba para benchmark grande.")
    doc.save(str(FIXTURE_DIR / "valid" / "large_300pages.pdf"))
    doc.close()


# === EDGE CASE PDFs ===


def create_empty():
    doc = pymupdf.open()
    doc.new_page(width=595, height=842)
    doc.save(str(FIXTURE_DIR / "edge_cases" / "empty.pdf"))
    doc.close()


def create_blank_pages():
    doc = pymupdf.open()
    for _ in range(3):
        doc.new_page(width=595, height=842)
    doc.save(str(FIXTURE_DIR / "edge_cases" / "blank_pages.pdf"))
    doc.close()


def create_encrypted():
    doc = pymupdf.open()
    _add_text_page(doc, "Documento encriptado con password.")
    doc.save(
        str(FIXTURE_DIR / "edge_cases" / "encrypted.pdf"),
        encryption=pymupdf.PDF_ENCRYPT_AES_256,
        owner_pw="owner123",
        user_pw="user123",
    )
    doc.close()


def create_corrupted():
    valid_path = FIXTURE_DIR / "valid" / "simple_1page.pdf"
    corrupted_path = FIXTURE_DIR / "edge_cases" / "corrupted.pdf"
    if valid_path.exists():
        data = valid_path.read_bytes()
        # Truncate to 60% of original size
        corrupted_path.write_bytes(data[: int(len(data) * 0.6)])
    else:
        # Fallback: create minimal invalid PDF
        corrupted_path.write_bytes(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj")


def create_only_images():
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    # Draw several coloured rectangles, so the page looks like it has only images
    colors = [(1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 0)]
    for i, color in enumerate(colors):
        shape = page.new_shape()
        x = 72 + (i % 2) * 200
        y = 72 + (i // 2) * 200
        shape.draw_rect(pymupdf.Rect(x, y, x + 150, y + 150))
        shape.finish(color=color, fill=color)
        shape.commit()
    doc.save(str(FIXTURE_DIR / "edge_cases" / "only_images.pdf"))
    doc.close()


def create_unicode_content():
    doc = pymupdf.open()
    lines = [
        "Documento con caracteres especiales:",
        "Acentos: áéíóúñ",
        "Signos: ¿¡?!",
        "Simbolos: €®©™",
        "CJK: 日本語テスト",
        "Arabic: مرحبا بالعالم",
    ]
    _add_multiline_page(doc, lines)
    doc.save(str(FIXTURE_DIR / "edge_cases" / "unicode_content.pdf"))
    doc.close()


# === LEGAL PDFs ===


def create_decreto():
    doc = pymupdf.open()
    lines = [
        "DECRETO 123/2024",
        "",
        "DE LA PRESIDENCIA DEL GOBIERNO",
        "",
        "Por el que se aprueba el reglamento de uso y",
        "de los servicios publicos de la administracion.",
        "",
        "ARTICULO 1. Objeto.",
        "El presente decreto tiene por objeto regular",
        "el uso y disfrute de los servicios publicos.",
        "",
        "ARTICULO 2. Ambito de aplicacion.",
        "Este decreto sera de aplicacion en todo",
        "el territorio nacional.",
    ]
    _add_multiline_page(doc, lines)
    doc.save(str(FIXTURE_DIR / "legal" / "decreto.pdf"))
    doc.close()


def create_oficio():
    doc = pymupdf.open()
    lines = [
        "OFICIO NUM. 456/2024",
        "",
        "Asunto: Solicitud de informacion",
        "",
        "Estimado/a Sr./Sra.:",
        "",
        "Por medio del presente oficio, le solicitamos",
        "nos haga llegar la informacion solicitada",
        "en el plazo de diez dias habiles.",
        "",
        "Sin otro particular, le saludamos atentamente.",
        "",
        "Firmado: Director General",
    ]
    _add_multiline_page(doc, lines)
    doc.save(str(FIXTURE_DIR / "legal" / "oficio.pdf"))
    doc.close()


def create_resolucion():
    doc = pymupdf.open()
    lines = [
        "RESOLUCION 789/2024",
        "",
        "SUBSECRETARIA DE EDUCACION",
        "",
        "Visto el expediente numero 1234/2024,",
        "y considerrando que:",
        "",
        "PRIMERO.- Que el articulo 45 de la Ley 2/2006",
        "establece que los centros educativos deben",
        "cumplir con los requisitos establecidos.",
        "",
        "SEGUNDO.- Que la inspeccion realizada el dia",
        "15 de marzo de 2024 ha detectado incumplimientos.",
        "",
        "RESUELVO:",
        "Primero.- Iniciar expediente disciplinario.",
        "Segundo.- Notificar al interesado.",
    ]
    _add_multiline_page(doc, lines)
    doc.save(str(FIXTURE_DIR / "legal" / "resolucion.pdf"))
    doc.close()


def create_contrato():
    doc = pymupdf.open()
    lines = [
        "CONTRATO DE PRESTACION DE SERVICIOS",
        "",
        "Entre las partes:",
        "",
        "D./Dña. Juan Perez (Proveedor)",
        "y",
        "D./Dña. Maria Garcia (Cliente)",
        "",
        "CLAUSULA PRIMERA.- Objeto del contrato.",
        "El proveedor se compromete a prestar los",
        "servicios de asesoramiento juridico.",
        "",
        "CLAUSULA SEGUNDA.- Duracion.",
        "El contrato tendra una duracion de doce meses.",
        "",
        "CLAUSULA TERCERA.- Precio.",
        "El precio total asciende a 12.000 euros.",
    ]
    _add_multiline_page(doc, lines)
    doc.save(str(FIXTURE_DIR / "legal" / "contrato.pdf"))
    doc.close()


# === BENCHMARK PDFs ===


def create_benchmark_50pages():
    doc = pymupdf.open()
    for i in range(50):
        lines = [
            f"Pagina {i + 1} - Documento de benchmark",
            f"Contenido generico pagina {i + 1}.",
            "Este texto es para medir el rendimiento del pipeline.",
        ]
        _add_multiline_page(doc, lines)
    doc.save(str(FIXTURE_DIR / "benchmarks" / "bench_50pages.pdf"))
    doc.close()


def create_benchmark_100pages():
    doc = pymupdf.open()
    for i in range(100):
        lines = [
            f"Pagina {i + 1} - Documento de benchmark",
            f"Contenido generico pagina {i + 1}.",
            "Este texto es para medir el rendimiento del pipeline.",
        ]
        _add_multiline_page(doc, lines)
    doc.save(str(FIXTURE_DIR / "benchmarks" / "bench_100pages.pdf"))
    doc.close()


def create_benchmark_140pages():
    doc = pymupdf.open()
    for i in range(140):
        lines = [
            f"Pagina {i + 1} - Documento de benchmark",
            f"Contenido generico pagina {i + 1}.",
            "Este texto es para medir el rendimiento del pipeline.",
        ]
        _add_multiline_page(doc, lines)
    doc.save(str(FIXTURE_DIR / "benchmarks" / "bench_140pages.pdf"))
    doc.close()


# === Main ===

ALL_CREATORS = [
    # valid/
    create_simple_1page,
    create_simple_5pages,
    create_with_images,
    create_with_tables,
    create_mixed_content,
    create_multi_column,
    create_rotated_pages,
    create_low_quality,
    create_large_300pages,
    # edge_cases/
    create_empty,
    create_blank_pages,
    create_encrypted,
    create_corrupted,
    create_only_images,
    create_unicode_content,
    # legal/
    create_decreto,
    create_oficio,
    create_resolucion,
    create_contrato,
    # benchmarks/
    create_benchmark_50pages,
    create_benchmark_100pages,
    create_benchmark_140pages,
]


def main():
    print("Generating test PDF fixtures...")
    _ensure_dirs()

    for creator in ALL_CREATORS:
        name = creator.__name__.replace("create_", "")
        try:
            creator()
            print(f"  OK: {name}")
        except Exception as e:
            print(f"  FAIL: {name} — {e}")

    # Validate generated PDFs
    print("\nValidating generated PDFs...")
    valid_count = 0
    fail_count = 0
    for pdf_path in FIXTURE_DIR.rglob("*.pdf"):
        try:
            doc = pymupdf.open(str(pdf_path))
            pages = doc.page_count
            doc.close()
            size_kb = pdf_path.stat().st_size / 1024
            print(f"  OK: {pdf_path.relative_to(FIXTURE_DIR)} ({pages} pages, {size_kb:.1f} KB)")
            valid_count += 1
        except Exception as e:
            print(f"  FAIL: {pdf_path.relative_to(FIXTURE_DIR)} — {e}")
            fail_count += 1

    print(f"\nDone: {valid_count} valid, {fail_count} failed")
    return fail_count == 0


if __name__ == "__main__":
    success = main()
    raise SystemExit(0 if success else 1)

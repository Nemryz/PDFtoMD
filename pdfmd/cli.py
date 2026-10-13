"""CLI module — Typer CLI with progress bars and Rich output."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn

from pdfmd import __version__
from pdfmd.core import convert_pdf
from pdfmd.ocr_engine import TesseractNotFoundError
from pdfmd.security import validate_path

app = typer.Typer(
    name="pdfmd",
    help="Convert scanned PDFs to structured Markdown with OCR.",
    add_completion=False,
    invoke_without_command=True,
    no_args_is_help=True,
)
console = Console()


@app.command()
def convert(
    input_path: str = typer.Argument(..., help="Path to PDF file"),
    output: str | None = typer.Option(None, "-o", "--output", help="Output Markdown file path"),
    lang: str = typer.Option("spa", "--lang", "-l", help="OCR language (default: spa)"),
    dpi: int = typer.Option(300, "--dpi", "-d", help="Render DPI (default: 300)"),
    signers: str | None = typer.Option(
        None, "--signers", "-s", help="Comma-separated list of expected signers"
    ),
    pages: str | None = typer.Option(
        None, "--pages", "-p", help="Pages to process (e.g., '0,1,2' or '0-5')"
    ),
    classify: bool = typer.Option(
        False, "--classify", "-c", help="Enable smart page classification and adaptive OCR"
    ),
    min_confidence: float = typer.Option(
        0.70,
        "--min-confidence",
        help="Minimum confidence threshold (default: 70%). Pages below are flagged for review.",
    ),
    retry_threshold: float = typer.Option(
        0.50,
        "--retry-threshold",
        help="Retry threshold (default: 50%). Pages below are retried with enhanced params.",
    ),
    max_pages: int = typer.Option(
        0, "--max-pages", help="Maximum pages to process (0 = no limit)."
    ),
    max_memory: float = typer.Option(
        0.0, "--max-memory", help="Maximum memory in MB (0 = no limit)."
    ),
    version: bool = typer.Option(False, "--version", "-v", help="Show version"),
) -> None:
    """Convert a scanned PDF to structured Markdown with OCR."""

    if version:
        console.print(f"pdfmd v{__version__}")
        raise typer.Exit()

    # Validate input file
    input_file = Path(input_path)
    if not validate_path(input_path):
        console.print(f"[red]Error:[/red] Invalid path (possible traversal): {input_path}")
        raise typer.Exit(code=1)
    if not input_file.exists():
        console.print(f"[red]Error:[/red] File not found: {input_path}")
        raise typer.Exit(code=1)

    if not input_file.suffix.lower() == ".pdf":
        console.print(f"[red]Error:[/red] Not a PDF file: {input_path}")
        raise typer.Exit(code=1)

    # Determine output path
    if output:
        out_path = Path(output)
    else:
        out_path = input_file.with_suffix(".md")

    # Parse pages
    page_indices = None
    if pages:
        page_indices = _parse_pages(pages)

    # Enforce max-pages limit
    if max_pages > 0 and page_indices is not None:
        page_indices = page_indices[:max_pages]
    elif max_pages > 0 and page_indices is None:
        page_indices = list(range(max_pages))

    # Parse signers
    signer_list = None
    if signers:
        signer_list = [s.strip() for s in signers.split(",") if s.strip()]

    # Run conversion with progress
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Converting PDF to Markdown...", total=None)

            result = convert_pdf(
                input_path=str(input_file),
                output_path=str(out_path),
                lang=lang,
                dpi=dpi,
                pages=page_indices,
                signers=signer_list,
                classify=classify,
                min_confidence=min_confidence,
                retry_threshold=retry_threshold,
            )

            progress.update(task, completed=True)

    except TesseractNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Error:[/red] Conversion failed: {e}")
        raise typer.Exit(code=1)

    # Display results
    _display_results(result)


def _parse_pages(pages_str: str) -> list[int]:
    """Parse page specification string.

    Supports: '0,1,2' or '0-5' or '0,2-4,7'
    """
    indices: list[int] = []
    for part in pages_str.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            indices.extend(range(int(start), int(end) + 1))
        else:
            indices.append(int(part))
    return sorted(set(indices))


def _display_results(result) -> None:
    """Display conversion results with Rich formatting."""
    console.print()
    console.print(
        Panel(
            f"[green]✓[/green] Conversion complete!\n\n"
            f"Pages processed: {result.pages_processed}/{result.total_pages}\n"
            f"OCR pages: {result.pages_with_ocr}\n"
            f"Avg confidence: {result.avg_confidence:.1%}\n"
            f"Time: {result.elapsed_seconds:.1f}s\n"
            f"Output: {result.output_path}\n"
            f"Metadata: {result.metadata_path}",
            title="Result",
            border_style="green",
        )
    )

    if result.signature_report_path:
        console.print(f"Signature report: {result.signature_report_path}")

    if result.images_dir:
        console.print(f"Images: {result.images_dir}")

    # Display classification summary if available
    if hasattr(result, "classifications") and result.classifications:
        from collections import Counter

        counts = Counter(c.classification.value for c in result.classifications)
        blank_count = counts.get("blank", 0)
        console.print()
        console.print("[bold]Page Classification Summary:[/bold]")
        for classification, count in sorted(counts.items()):
            console.print(f"  {classification}: {count}")
        if blank_count:
            console.print(f"  [dim]({blank_count} blank pages skipped)[/dim]")

    if result.warnings:
        console.print()
        for w in result.warnings:
            console.print(f"[yellow]⚠[/yellow] {w}")


@app.command()
def info(
    input_path: str = typer.Argument(..., help="Path to PDF file"),
) -> None:
    """Show information about a PDF file without converting."""
    from pdfmd.pdf_reader import get_page_count, has_text_layer, open_pdf

    try:
        doc = open_pdf(input_path)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)

    total = get_page_count(doc)
    scanned = sum(1 for i in range(total) if not has_text_layer(doc[i]))
    digital = total - scanned

    doc.close()

    console.print(
        Panel(
            f"File: {input_path}\n"
            f"Total pages: {total}\n"
            f"Digital (text layer): {digital}\n"
            f"Scanned (need OCR): {scanned}",
            title="PDF Info",
        )
    )

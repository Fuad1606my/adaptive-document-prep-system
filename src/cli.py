import argparse
from rich.console import Console
from rich.table import Table

from src.config import PDF_PATH
from src.pdf_parser import extract_pdf_text, get_pdf_page_count
from src.section_mapper import split_sections, get_section_summary


console = Console()


def run_parse_command():
    """
    Parse the PDF and display section information.
    """
    console.print("[bold blue]Parsing SLATEFALL dossier PDF...[/bold blue]")

    page_count = get_pdf_page_count(PDF_PATH)
    full_text = extract_pdf_text(PDF_PATH)
    sections = split_sections(full_text)

    console.print(f"[green]PDF loaded successfully.[/green]")
    console.print(f"PDF path: {PDF_PATH}")
    console.print(f"Total pages: {page_count}")
    console.print(f"Parsed sections: {len(sections)}")

    table = Table(title="Parsed Document Sections")
    table.add_column("Section ID", justify="center")
    table.add_column("Title", style="cyan")
    table.add_column("Characters", justify="right")
    table.add_column("Preview", style="white")

    for section_id in sorted(sections.keys()):
        summary = get_section_summary(section_id, sections[section_id])
        table.add_row(
            str(summary["section_id"]),
            summary["title"],
            str(summary["characters"]),
            summary["preview"],
        )

    console.print(table)


def main():
    parser = argparse.ArgumentParser(
        description="Adaptive Document Preparation System CLI"
    )

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("parse", help="Parse PDF and show detected sections")

    args = parser.parse_args()

    if args.command == "parse":
        run_parse_command()
    else:
        console.print("[bold green]Adaptive Document Preparation System is ready![/bold green]")
        console.print("Available command:")
        console.print("  python -m src.cli parse")


if __name__ == "__main__":
    main()
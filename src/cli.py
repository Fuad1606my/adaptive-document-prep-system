import argparse
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.config import PDF_PATH
from src.pdf_parser import extract_pdf_text, get_pdf_page_count
from src.section_mapper import split_sections, get_section_summary
from src.kb_manager import (
    load_kb,
    save_kb,
    create_session_record,
    add_session,
    get_sessions_for_sections,
    get_wrong_topics_for_sections,
    get_kb_snapshot,
)


console = Console()


def run_parse_command():
    """
    Parse the PDF and display section information.
    """
    console.print("[bold blue]Parsing SLATEFALL dossier PDF...[/bold blue]")

    page_count = get_pdf_page_count(PDF_PATH)
    full_text = extract_pdf_text(PDF_PATH)
    sections = split_sections(full_text)

    console.print("[green]PDF loaded successfully.[/green]")
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


def run_kb_test_command():
    """
    Create a dummy session and save it to KB.
    This verifies KB read/write behavior.
    """
    console.print("[bold blue]Testing Knowledge Base save/load...[/bold blue]")

    dummy_questions = [
        {
            "question_id": "dummy_q_001",
            "section_id": 5,
            "topic": "Three-Two-One Rule",
            "question": "What is the Three-Two-One Rule used for?",
            "options": {
                "A": "Managing activations, sightlines, and extraction",
                "B": "Counting safehouses",
                "C": "Classifying adversaries",
                "D": "Selecting medical kits",
            },
            "correct_answer": "A",
            "user_answer": "B",
            "is_correct": False,
            "explanation": "The Three-Two-One Rule limits activations, maintains sightlines, and reserves an extraction route.",
        },
        {
            "question_id": "dummy_q_002",
            "section_id": 8,
            "topic": "Safehouse Provisioning",
            "question": "What does each safehouse maintain?",
            "options": {
                "A": "Only weapons",
                "B": "30-day rations, backup comms, baton cache, medical supplies, currency, and identity package",
                "C": "Only vehicles",
                "D": "No supplies",
            },
            "correct_answer": "B",
            "user_answer": "B",
            "is_correct": True,
            "explanation": "The dossier states that safehouses maintain rations, backup comms, baton replacements, medical supplies, currency, and identity packages.",
        },
    ]

    session = create_session_record(
        session_id="kb_test_session_001",
        sections=[5, 8],
        questions=dummy_questions,
        session_type="cold_start",
    )

    add_session(session)

    console.print("[green]Dummy session saved to KB successfully.[/green]")

    kb = load_kb()
    console.print(f"Total sessions in KB: {len(kb.get('sessions', []))}")

    history = get_sessions_for_sections([8])
    weak_topics = get_wrong_topics_for_sections([5, 8])
    snapshot = get_kb_snapshot()

    console.print(f"Sessions involving Section 8: {len(history)}")
    console.print(f"Weak topics found: {len(weak_topics)}")

    console.print(
        Panel.fit(
            str(snapshot),
            title="KB Snapshot Preview",
            border_style="green",
        )
    )


def main():
    parser = argparse.ArgumentParser(
        description="Adaptive Document Preparation System CLI"
    )

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("parse", help="Parse PDF and show detected sections")
    subparsers.add_parser("kb-test", help="Test KB save/load and snapshot")

    args = parser.parse_args()

    if args.command == "parse":
        run_parse_command()
    elif args.command == "kb-test":
        run_kb_test_command()
    else:
        console.print("[bold green]Adaptive Document Preparation System is ready![/bold green]")
        console.print("Available commands:")
        console.print("  python -m src.cli parse")
        console.print("  python -m src.cli kb-test")


if __name__ == "__main__":
    main()
    
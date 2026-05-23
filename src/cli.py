import argparse
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.config import PDF_PATH
from src.pdf_parser import extract_pdf_text, get_pdf_page_count
from src.section_mapper import split_sections, get_section_summary
from src.kb_manager import (
    load_kb,
    create_session_record,
    add_session,
    get_sessions_for_sections,
    get_wrong_topics_for_sections,
    get_mastered_questions_for_sections,
    get_kb_snapshot,
)
from src.mcq_generator import generate_mcqs_for_sections
from src.scoring import simulate_answers, score_questions


console = Console()


def load_sections():
    full_text = extract_pdf_text(PDF_PATH)
    return split_sections(full_text)


def run_parse_command():
    console.print("[bold blue]Parsing SLATEFALL dossier PDF...[/bold blue]")

    page_count = get_pdf_page_count(PDF_PATH)
    sections = load_sections()

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
        }
    ]

    session = create_session_record(
        session_id="kb_test_session_001",
        sections=[5, 8],
        questions=dummy_questions,
        session_type="cold_start",
    )

    add_session(session)
    snapshot = get_kb_snapshot()

    console.print("[green]Dummy session saved to KB successfully.[/green]")
    console.print(Panel.fit(str(snapshot), title="KB Snapshot Preview", border_style="green"))


def run_session_command(section_ids, n, simulate_mode):
    sections = load_sections()

    previous_sessions = get_sessions_for_sections(section_ids)
    session_type = "adaptive" if previous_sessions else "cold_start"

    weak_topics = get_wrong_topics_for_sections(section_ids)
    mastered_questions = get_mastered_questions_for_sections(section_ids)

    console.print(f"[bold blue]Starting prep session[/bold blue]")
    console.print(f"Sections: {section_ids}")
    console.print(f"Questions per section: {n}")
    console.print(f"Session type: [bold]{session_type}[/bold]")

    if weak_topics:
        console.print("[yellow]Historical weak topics detected:[/yellow]")
        for item in weak_topics[:5]:
            console.print(f"- {item['topic']} | wrong_count={item['wrong_count']}")

    questions = generate_mcqs_for_sections(
        sections=sections,
        selected_section_ids=section_ids,
        n_per_section=n,
        weak_topics=weak_topics,
        mastered_questions=mastered_questions,
    )

    answers = simulate_answers(questions, mode=simulate_mode)
    scored_questions = score_questions(questions, answers)

    session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    session_record = create_session_record(
        session_id=session_id,
        sections=section_ids,
        questions=scored_questions,
        session_type=session_type,
    )

    add_session(session_record)

    score = session_record["score"]

    console.print("[green]Session completed and saved to KB.[/green]")
    console.print(f"Session ID: {session_id}")
    console.print(f"Score: {score['correct']}/{score['total']} ({score['accuracy']}%)")

    table = Table(title="Generated MCQs and Results")
    table.add_column("#", justify="right")
    table.add_column("Section", justify="center")
    table.add_column("Topic", style="cyan")
    table.add_column("Correct?", justify="center")
    table.add_column("Adaptive Reason", style="yellow")

    for idx, q in enumerate(scored_questions, start=1):
        table.add_row(
            str(idx),
            str(q["section_id"]),
            q["topic"],
            "✅" if q["is_correct"] else "❌",
            q.get("adaptive_reason") or "-",
        )

    console.print(table)


def main():
    parser = argparse.ArgumentParser(
        description="Adaptive Document Preparation System CLI"
    )

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("parse", help="Parse PDF and show detected sections")
    subparsers.add_parser("kb-test", help="Test KB save/load and snapshot")

    run_parser = subparsers.add_parser("run-session", help="Run a prep session")
    run_parser.add_argument("--sections", nargs="+", type=int, required=True)
    run_parser.add_argument("--n", type=int, default=5)
    run_parser.add_argument(
        "--simulate",
        choices=["all_correct", "all_wrong", "mixed", "random"],
        default="mixed",
    )

    args = parser.parse_args()

    if args.command == "parse":
        run_parse_command()
    elif args.command == "kb-test":
        run_kb_test_command()
    elif args.command == "run-session":
        run_session_command(args.sections, args.n, args.simulate)
    else:
        console.print("[bold green]Adaptive Document Preparation System is ready![/bold green]")
        console.print("Available commands:")
        console.print("  python -m src.cli parse")
        console.print("  python -m src.cli kb-test")
        console.print("  python -m src.cli run-session --sections 5 8 --n 5 --simulate mixed")


if __name__ == "__main__":
    main()
    
from typing import List, Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.config import PDF_PATH
from src.pdf_parser import extract_pdf_text, get_pdf_page_count
from src.section_mapper import split_sections, get_section_summary
from src.kb_manager import (
    save_kb,
    get_kb_snapshot,
    get_sessions_for_sections,
    get_wrong_topics_for_sections,
    get_mastered_questions_for_sections,
    create_session_record,
    add_session,
)
from src.mcq_generator import generate_mcqs_for_sections
from src.scoring import simulate_answers, score_questions
from src.exporter import export_questions, export_kb_snapshot, get_scenario_dir
from datetime import datetime


app = FastAPI(
    title="Adaptive Document Preparation System API",
    description="Backend API for PDF-based adaptive MCQ preparation.",
    version="1.0.0",
)


class RunSessionRequest(BaseModel):
    sections: List[int]
    n: int = 5
    simulate: Literal["all_correct", "all_wrong", "mixed", "random"] = "mixed"


class RunScenarioResponse(BaseModel):
    message: str


def load_sections():
    full_text = extract_pdf_text(PDF_PATH)
    return split_sections(full_text)


def reset_kb():
    save_kb({"sessions": []})


def run_session_core(section_ids: List[int], n: int, simulate_mode: str):
    sections = load_sections()

    for section_id in section_ids:
        if section_id not in sections:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid section ID: {section_id}. Valid IDs are 1-10.",
            )

    previous_sessions = get_sessions_for_sections(section_ids)
    session_type = "adaptive" if previous_sessions else "cold_start"

    weak_topics = get_wrong_topics_for_sections(section_ids)
    mastered_questions = get_mastered_questions_for_sections(section_ids)

    questions = generate_mcqs_for_sections(
        sections=sections,
        selected_section_ids=section_ids,
        n_per_section=n,
        weak_topics=weak_topics,
        mastered_questions=mastered_questions,
    )

    answers = simulate_answers(questions, mode=simulate_mode)
    scored_questions = score_questions(questions, answers)

    session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

    session_record = create_session_record(
        session_id=session_id,
        sections=section_ids,
        questions=scored_questions,
        session_type=session_type,
    )

    add_session(session_record)

    return {
        "session": session_record,
        "historical_weak_topics": weak_topics,
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "Adaptive Document Preparation System API is running.",
    }


@app.get("/sections")
def list_sections():
    try:
        page_count = get_pdf_page_count(PDF_PATH)
        sections = load_sections()

        section_summaries = [
            get_section_summary(section_id, sections[section_id])
            for section_id in sorted(sections.keys())
        ]

        return {
            "pdf_path": str(PDF_PATH),
            "page_count": page_count,
            "total_sections": len(section_summaries),
            "sections": section_summaries,
        }

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/sessions/run")
def run_session(request: RunSessionRequest):
    try:
        return run_session_core(
            section_ids=request.sections,
            n=request.n,
            simulate_mode=request.simulate,
        )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/kb/snapshot")
def kb_snapshot():
    try:
        return get_kb_snapshot()

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/kb/reset")
def kb_reset():
    try:
        reset_kb()
        return {"message": "Knowledge base reset successfully."}

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/scenarios/a/run", response_model=RunScenarioResponse)
def run_scenario_a_api():
    try:
        reset_kb()

        result = run_session_core(
            section_ids=[3, 7],
            n=5,
            simulate_mode="mixed",
        )

        session_record = result["session"]
        output_dir = get_scenario_dir("scenario_a")

        export_questions(
            output_dir,
            "questions_scenario_a.json",
            session_record,
        )

        export_kb_snapshot(
            output_dir,
            "kb_snapshot_scenario_a.json",
            get_kb_snapshot(),
        )

        return {"message": "Scenario A completed and exported successfully."}

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/scenarios/b/run", response_model=RunScenarioResponse)
def run_scenario_b_api():
    try:
        reset_kb()

        scenario_steps = [
            {
                "name": "scenario_b_iter1",
                "sections": [5, 8],
                "questions_file": "questions_iter1.json",
                "snapshot_file": "kb_snapshot_iter1.json",
                "simulate": "mixed",
            },
            {
                "name": "scenario_b_iter2",
                "sections": [6, 8, 9],
                "questions_file": "questions_iter2.json",
                "snapshot_file": "kb_snapshot_iter2.json",
                "simulate": "mixed",
            },
            {
                "name": "scenario_b_iter3",
                "sections": [8],
                "questions_file": "questions_iter3.json",
                "snapshot_file": "kb_snapshot_iter3.json",
                "simulate": "mixed",
            },
        ]

        for step in scenario_steps:
            result = run_session_core(
                section_ids=step["sections"],
                n=5,
                simulate_mode=step["simulate"],
            )

            session_record = result["session"]
            output_dir = get_scenario_dir(step["name"])

            export_questions(
                output_dir,
                step["questions_file"],
                session_record,
            )

            export_kb_snapshot(
                output_dir,
                step["snapshot_file"],
                get_kb_snapshot(),
            )

        return {"message": "Scenario B completed and exported successfully."}

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from src.config import KB_PATH


def load_kb(kb_path: Path = KB_PATH) -> Dict[str, Any]:
    """
    Load the knowledge base from a JSON file.
    If the file does not exist or is empty, return a default KB structure.
    """
    if not kb_path.exists():
        return {"sessions": []}

    try:
        with open(kb_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        if "sessions" not in data:
            data["sessions"] = []

        return data

    except json.JSONDecodeError:
        return {"sessions": []}


def save_kb(kb: Dict[str, Any], kb_path: Path = KB_PATH) -> None:
    """
    Save the knowledge base to a JSON file.
    """
    kb_path.parent.mkdir(parents=True, exist_ok=True)

    with open(kb_path, "w", encoding="utf-8") as file:
        json.dump(kb, file, indent=2, ensure_ascii=False)


def create_session_record(
    session_id: str,
    sections: List[int],
    questions: List[Dict[str, Any]],
    session_type: str,
) -> Dict[str, Any]:
    """
    Create a complete session record.
    """
    total = len(questions)
    correct = sum(1 for q in questions if q.get("is_correct") is True)
    wrong = total - correct
    accuracy = round((correct / total) * 100, 2) if total else 0

    weak_topics = sorted(
        {
            q.get("topic", "Unknown Topic")
            for q in questions
            if q.get("is_correct") is False
        }
    )

    return {
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "session_type": session_type,
        "sections": sections,
        "questions": questions,
        "score": {
            "total": total,
            "correct": correct,
            "wrong": wrong,
            "accuracy": accuracy,
        },
        "weak_topics": weak_topics,
    }


def add_session(session_record: Dict[str, Any], kb_path: Path = KB_PATH) -> Dict[str, Any]:
    """
    Add a session record to the KB and save it.
    """
    kb = load_kb(kb_path)
    kb["sessions"].append(session_record)
    save_kb(kb, kb_path)
    return kb


def get_sessions_for_sections(
    section_ids: List[int],
    kb_path: Path = KB_PATH,
) -> List[Dict[str, Any]]:
    """
    Retrieve all previous sessions that include at least one of the requested sections.
    """
    kb = load_kb(kb_path)
    target_sections = set(section_ids)

    matched_sessions = []

    for session in kb.get("sessions", []):
        session_sections = set(session.get("sections", []))
        if target_sections.intersection(session_sections):
            matched_sessions.append(session)

    return matched_sessions


def get_wrong_topics_for_sections(
    section_ids: List[int],
    kb_path: Path = KB_PATH,
) -> List[Dict[str, Any]]:
    """
    Identify topics that were answered incorrectly in previous sessions
    involving the selected sections.
    """
    sessions = get_sessions_for_sections(section_ids, kb_path)
    topic_stats: Dict[str, Dict[str, Any]] = {}

    for session in sessions:
        for question in session.get("questions", []):
            section_id = question.get("section_id")
            is_correct = question.get("is_correct")
            topic = question.get("topic", "Unknown Topic")

            if section_id not in section_ids:
                continue

            if topic not in topic_stats:
                topic_stats[topic] = {
                    "topic": topic,
                    "wrong_count": 0,
                    "correct_count": 0,
                    "sections": set(),
                }

            topic_stats[topic]["sections"].add(section_id)

            if is_correct is False:
                topic_stats[topic]["wrong_count"] += 1
            elif is_correct is True:
                topic_stats[topic]["correct_count"] += 1

    result = []

    for topic, stats in topic_stats.items():
        if stats["wrong_count"] > 0:
            result.append(
                {
                    "topic": topic,
                    "wrong_count": stats["wrong_count"],
                    "correct_count": stats["correct_count"],
                    "sections": sorted(list(stats["sections"])),
                }
            )

    result.sort(key=lambda item: item["wrong_count"], reverse=True)
    return result


def get_mastered_questions_for_sections(
    section_ids: List[int],
    kb_path: Path = KB_PATH,
) -> List[str]:
    """
    Return questions previously answered correctly.
    This helps avoid excessive repetition.
    """
    sessions = get_sessions_for_sections(section_ids, kb_path)
    mastered = []

    for session in sessions:
        for question in session.get("questions", []):
            if (
                question.get("section_id") in section_ids
                and question.get("is_correct") is True
            ):
                mastered.append(question.get("question", ""))

    return mastered


def get_kb_snapshot(limit: int = 5, kb_path: Path = KB_PATH) -> Dict[str, Any]:
    """
    Return a human-readable snapshot of the top-N most recent sessions.
    """
    kb = load_kb(kb_path)
    sessions = kb.get("sessions", [])

    recent_sessions = sessions[-limit:]
    recent_sessions = list(reversed(recent_sessions))

    snapshot = {
        "snapshot_created_at": datetime.now().isoformat(timespec="seconds"),
        "total_sessions": len(sessions),
        "recent_sessions": [],
    }

    for session in recent_sessions:
        snapshot["recent_sessions"].append(
            {
                "session_id": session.get("session_id"),
                "timestamp": session.get("timestamp"),
                "session_type": session.get("session_type"),
                "sections": session.get("sections"),
                "score": session.get("score"),
                "weak_topics": session.get("weak_topics"),
                "question_count": len(session.get("questions", [])),
            }
        )

    return snapshot
    
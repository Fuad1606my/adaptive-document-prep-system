import json
from pathlib import Path
from typing import Any, Dict, List

from src.config import OUTPUTS_DIR


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, data: Any) -> None:
    ensure_dir(path.parent)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def export_questions(
    output_dir: Path,
    filename: str,
    session_record: Dict[str, Any],
) -> Path:
    """
    Export generated questions and scoring results for one session.
    """
    ensure_dir(output_dir)

    export_data = {
        "session_id": session_record.get("session_id"),
        "timestamp": session_record.get("timestamp"),
        "session_type": session_record.get("session_type"),
        "sections": session_record.get("sections"),
        "score": session_record.get("score"),
        "weak_topics": session_record.get("weak_topics"),
        "questions": session_record.get("questions", []),
    }

    path = output_dir / filename
    write_json(path, export_data)
    return path


def export_kb_snapshot(
    output_dir: Path,
    filename: str,
    snapshot: Dict[str, Any],
) -> Path:
    """
    Export KB snapshot for reviewer verification.
    """
    ensure_dir(output_dir)

    path = output_dir / filename
    write_json(path, snapshot)
    return path


def get_scenario_dir(name: str) -> Path:
    return OUTPUTS_DIR / name
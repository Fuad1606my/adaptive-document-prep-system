import json
import os
import re
from typing import Any, Dict, List, Optional

import requests


OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3.2:3b"
OLLAMA_TIMEOUT_SECONDS = 120

# Cloud-safe toggle:
# Local default = true, so Ollama works on your computer.
# Streamlit Cloud should set USE_OLLAMA=false so the app uses fallback generation.
USE_OLLAMA = os.getenv("USE_OLLAMA", "true").lower() == "true"


def is_ollama_available() -> bool:
    """
    Check whether Ollama local server is reachable.
    If USE_OLLAMA=false, skip Ollama completely.
    """
    if not USE_OLLAMA:
        return False

    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False


def _extract_json_object_or_array(text: str) -> Optional[Any]:
    """
    Extract valid JSON from an LLM response.
    Supports:
    1. {"questions": [...]}
    2. [...]
    3. JSON wrapped inside extra text
    """
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    object_match = re.search(r"\{\s*\"questions\"\s*:\s*\[.*\]\s*\}", text, re.DOTALL)
    if object_match:
        try:
            return json.loads(object_match.group(0))
        except json.JSONDecodeError:
            pass

    array_match = re.search(r"\[\s*\{.*\}\s*\]", text, re.DOTALL)
    if array_match:
        try:
            return json.loads(array_match.group(0))
        except json.JSONDecodeError:
            pass

    return None


def _get_question_list(parsed_json: Any) -> Optional[List[Dict[str, Any]]]:
    """
    Normalize either {"questions": [...]} or [...] into a list of questions.
    """
    if isinstance(parsed_json, dict):
        questions = parsed_json.get("questions")
        if isinstance(questions, list):
            return questions

    if isinstance(parsed_json, list):
        return parsed_json

    return None


def _validate_llm_questions(
    raw_questions: List[Dict[str, Any]],
    section_id: int,
    n: int,
    weak_topic_names: List[str],
) -> List[Dict[str, Any]]:
    """
    Validate and normalize LLM-created MCQs.
    Bad questions are skipped.
    """
    valid_questions = []

    for item in raw_questions:
        if len(valid_questions) >= n:
            break

        if not isinstance(item, dict):
            continue

        question = str(item.get("question", "")).strip()
        topic = str(item.get("topic", f"Section {section_id}")).strip()
        options = item.get("options", {})
        correct_answer = str(item.get("correct_answer", "")).strip().upper()
        explanation = str(item.get("explanation", "")).strip()

        if not question or not topic or not explanation:
            continue

        if not isinstance(options, dict):
            continue

        required_options = ["A", "B", "C", "D"]

        normalized_options = {}
        for key in required_options:
            value = options.get(key)
            if value is None:
                value = options.get(key.lower())

            value = str(value or "").strip()
            if not value:
                break

            normalized_options[key] = value

        if len(normalized_options) != 4:
            continue

        if correct_answer not in required_options:
            continue

        adaptive_reason = None
        if topic in weak_topic_names:
            adaptive_reason = f"Focused on previously missed topic: {topic}"

        valid_questions.append(
            {
                "section_id": section_id,
                "topic": topic,
                "question": question,
                "options": normalized_options,
                "correct_answer": correct_answer,
                "explanation": explanation,
                "adaptive_reason": adaptive_reason,
                "generator": "ollama_llm",
            }
        )

    return valid_questions


def generate_mcqs_with_ollama(
    section_id: int,
    section_title: str,
    section_text: str,
    n: int = 5,
    weak_topics: List[Dict[str, Any]] | None = None,
    mastered_questions: List[str] | None = None,
) -> Optional[List[Dict[str, Any]]]:
    """
    Generate MCQs using local Ollama.
    Returns None if Ollama is disabled, unavailable, or response validation fails.
    The caller should then use fallback generation.
    """
    if not USE_OLLAMA:
        return None

    weak_topics = weak_topics or []
    mastered_questions = mastered_questions or []

    if not is_ollama_available():
        return None

    weak_topic_names = [
        item.get("topic", "")
        for item in weak_topics
        if item.get("topic")
    ]

    weak_topic_text = ", ".join(weak_topic_names) if weak_topic_names else "None"
    mastered_text = "\n".join(mastered_questions[:8]) if mastered_questions else "None"

    # Keep context small for local models.
    section_excerpt = section_text[:3500]

    prompt = f"""
Generate exactly {n} multiple choice questions from the document section.

Return ONLY JSON.

The JSON must follow this exact structure:

{{
  "questions": [
    {{
      "topic": "short topic name",
      "question": "question text",
      "options": {{
        "A": "option A",
        "B": "option B",
        "C": "option C",
        "D": "option D"
      }},
      "correct_answer": "A",
      "explanation": "brief explanation"
    }}
  ]
}}

Rules:
- Return no markdown.
- Return no commentary.
- Every question must have A, B, C, D.
- correct_answer must be one of A, B, C, D.
- Questions must be based only on the section text.
- If weak topics are available, prioritize them.
- Avoid mastered questions.

Section ID: {section_id}
Section title: {section_title}

Weak topics:
{weak_topic_text}

Mastered questions to avoid:
{mastered_text}

Section text:
{section_excerpt}
""".strip()

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are a strict JSON generator for exam MCQs.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.1,
        },
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=OLLAMA_TIMEOUT_SECONDS,
        )
        response.raise_for_status()

        data = response.json()
        content = data.get("message", {}).get("content", "")

        parsed_json = _extract_json_object_or_array(content)
        if parsed_json is None:
            return None

        raw_questions = _get_question_list(parsed_json)
        if not raw_questions:
            return None

        valid_questions = _validate_llm_questions(
            raw_questions=raw_questions,
            section_id=section_id,
            n=n,
            weak_topic_names=weak_topic_names,
        )

        if not valid_questions:
            return None

        return valid_questions[:n]

    except Exception:
        return None
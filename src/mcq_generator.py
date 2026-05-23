import re
import uuid
from typing import Any, Dict, List

from src.section_mapper import SECTION_TITLES


def _clean_text(text: str) -> str:
    return " ".join(text.replace("\n", " ").split())


def _extract_candidate_sentences(section_text: str, max_sentences: int = 20) -> List[str]:
    """
    Extract useful factual-looking sentences from section text.
    This is a deterministic fallback when no external LLM is available.
    """
    cleaned = _clean_text(section_text)

    raw_sentences = re.split(r"(?<=[.!?])\s+", cleaned)

    candidates = []
    for sentence in raw_sentences:
        sentence = sentence.strip()

        if len(sentence) < 80 or len(sentence) > 260:
            continue

        lower = sentence.lower()

        useful_markers = [
            "is ",
            "are ",
            "was ",
            "were ",
            "has ",
            "have ",
            "includes",
            "requires",
            "classified",
            "maximum",
            "minimum",
            "primary",
            "standard",
            "documented",
            "operational",
            "section",
            "case",
            "tier",
            "safehouse",
            "doctrine",
            "rule",
            "power",
            "range",
            "duration",
            "mass",
        ]

        if any(marker in lower for marker in useful_markers):
            candidates.append(sentence)

        if len(candidates) >= max_sentences:
            break

    return candidates


def _guess_topic(section_id: int, sentence: str) -> str:
    """
    Guess a topic label from a sentence.
    This supports adaptive weak-area tracking.
    """
    section_title = SECTION_TITLES.get(section_id, f"Section {section_id}")
    lower = sentence.lower()

    topic_keywords = [
        ("Three-Two-One Rule", ["three-two-one", "three activations", "two active sightlines"]),
        ("Doctrine of Sequential Suspension", ["doctrine of sequential suspension", "dss"]),
        ("Tail-Strike Technique", ["tail-strike", "tail momentum"]),
        ("Drop-Tune Manoeuvre", ["drop-tune", "contact-exclusion"]),
        ("Safehouse Provisioning", ["safehouse", "rations", "backup comms", "identity package"]),
        ("Operational Territory", ["operational territory", "territory spans"]),
        ("Threat Tier Classification", ["tier", "threat tier", "casualty potential"]),
        ("Inertial Suspension", ["inertial suspension", "primary power"]),
        ("Mass Ceiling", ["mass ceiling", "240 kg"]),
        ("Duration and Range", ["duration", "range", "22 meters", "0.6 seconds"]),
        ("Echo Lock", ["echo lock"]),
        ("Drift Read", ["drift read"]),
        ("Cell Halcón", ["cell halcón", "halcón"]),
        ("Equipment Loadout", ["loadout", "field kit", "batons", "bracers"]),
        ("Case Files", ["case number", "outcome", "casualties"]),
    ]

    for topic, keywords in topic_keywords:
        if any(keyword in lower for keyword in keywords):
            return topic

    return section_title


def _make_options(correct_answer: str, section_id: int, topic: str) -> Dict[str, str]:
    """
    Create four MCQ options with one correct answer.
    Distractors are intentionally generic but plausible.
    """
    distractors_pool = [
        "It describes an unrelated administrative process.",
        "It only refers to public media restrictions.",
        "It is mainly a civilian biography detail.",
        "It refers to a retired equipment archive only.",
        "It describes a non-operational background note.",
        "It is a general historical footnote without tactical use.",
        "It only identifies a location name without any function.",
        "It describes a minor glossary term with no operational relevance.",
    ]

    options = {
        "A": correct_answer,
        "B": distractors_pool[(section_id + 1) % len(distractors_pool)],
        "C": distractors_pool[(section_id + 3) % len(distractors_pool)],
        "D": distractors_pool[(section_id + 5) % len(distractors_pool)],
    }

    return options


def generate_fallback_mcqs(
    section_id: int,
    section_text: str,
    n: int = 5,
    weak_topics: List[Dict[str, Any]] | None = None,
    mastered_questions: List[str] | None = None,
) -> List[Dict[str, Any]]:
    """
    Generate MCQs without using a paid API.
    This ensures the project runs locally for reviewers.
    """
    weak_topics = weak_topics or []
    mastered_questions = mastered_questions or []

    candidates = _extract_candidate_sentences(section_text, max_sentences=40)

    weak_topic_names = [item["topic"] for item in weak_topics]

    # Prioritize weak-topic sentences if this is an adaptive run.
    prioritized = []
    normal = []

    for sentence in candidates:
        topic = _guess_topic(section_id, sentence)
        if topic in weak_topic_names:
            prioritized.append(sentence)
        else:
            normal.append(sentence)

    ordered_sentences = prioritized + normal

    mcqs = []
    used_questions = set()

    for sentence in ordered_sentences:
        if len(mcqs) >= n:
            break

        topic = _guess_topic(section_id, sentence)

        question_text = (
            f"According to Section {section_id}, which statement best matches the topic "
            f"'{topic}'?"
        )

        if question_text in mastered_questions or question_text in used_questions:
            question_text = (
                f"In Section {section_id}, what is the most accurate detail about '{topic}'?"
            )

        if question_text in used_questions:
            continue

        options = _make_options(sentence, section_id, topic)

        adaptive_reason = None
        if topic in weak_topic_names:
            adaptive_reason = f"Focused on previously missed topic: {topic}"

        mcqs.append(
            {
                "question_id": f"q_{uuid.uuid4().hex[:8]}",
                "section_id": section_id,
                "topic": topic,
                "question": question_text,
                "options": options,
                "correct_answer": "A",
                "explanation": sentence,
                "adaptive_reason": adaptive_reason,
                "generator": "fallback_rule_based",
            }
        )

        used_questions.add(question_text)

    # If not enough factual sentences found, fill with generic section questions.
    while len(mcqs) < n:
        topic = SECTION_TITLES.get(section_id, f"Section {section_id}")
        question_text = f"What is Section {section_id} mainly about?"

        suffix = len(mcqs) + 1
        if suffix > 1:
            question_text = f"What is another important focus of Section {section_id}? ({suffix})"

        mcqs.append(
            {
                "question_id": f"q_{uuid.uuid4().hex[:8]}",
                "section_id": section_id,
                "topic": topic,
                "question": question_text,
                "options": {
                    "A": topic,
                    "B": "Unrelated financial accounting only",
                    "C": "Random social media content",
                    "D": "A cooking instruction section",
                },
                "correct_answer": "A",
                "explanation": f"Section {section_id} is titled '{topic}'.",
                "adaptive_reason": None,
                "generator": "fallback_rule_based",
            }
        )

    return mcqs


def generate_mcqs_for_sections(
    sections: Dict[int, str],
    selected_section_ids: List[int],
    n_per_section: int = 5,
    weak_topics: List[Dict[str, Any]] | None = None,
    mastered_questions: List[str] | None = None,
) -> List[Dict[str, Any]]:
    """
    Generate MCQs for selected sections.
    Currently uses a robust fallback generator.
    External LLM integration can be plugged in later.
    """
    all_questions = []

    for section_id in selected_section_ids:
        if section_id not in sections:
            raise ValueError(f"Invalid section ID: {section_id}")

        section_weak_topics = [
            item for item in (weak_topics or [])
            if section_id in item.get("sections", [])
        ]

        questions = generate_fallback_mcqs(
            section_id=section_id,
            section_text=sections[section_id],
            n=n_per_section,
            weak_topics=section_weak_topics,
            mastered_questions=mastered_questions or [],
        )

        all_questions.extend(questions)

    return all_questions
from src.mcq_generator import generate_fallback_mcqs


def test_generate_fallback_mcqs_returns_questions():
    section_text = """
    Section 5. Operational Tactics and Combat Doctrine

    The Doctrine of Sequential Suspension rests on six core principles.
    Sequence determines lethality. A single suspension rarely wins an engagement.
    Ordered chains of three define the doctrine.
    Acquisition is the vulnerability.
    Withdraw before exhaustion.
    """

    questions = generate_fallback_mcqs(
        section_id=5,
        section_text=section_text,
        n=2,
        weak_topics=[],
        mastered_questions=[],
    )

    assert isinstance(questions, list)
    assert len(questions) == 2


def test_fallback_question_has_required_fields():
    section_text = """
    Section 8. Known Bases, Safehouses, and Operational Territory

    Each safehouse maintains standardized provisioning.
    Safehouse provisioning includes rations, communication units, replacement sets,
    medical items, and local currency.
    """

    questions = generate_fallback_mcqs(
        section_id=8,
        section_text=section_text,
        n=1,
        weak_topics=[],
        mastered_questions=[],
    )

    question = questions[0]

    assert "question_id" in question
    assert question["section_id"] == 8
    assert "topic" in question
    assert "question" in question
    assert "options" in question
    assert "correct_answer" in question
    assert "explanation" in question
    assert "generator" in question


def test_fallback_question_has_four_options_and_valid_answer():
    section_text = """
    Section 5. Operational Tactics and Combat Doctrine

    Sequence determines lethality. A single suspension rarely wins an engagement.
    Ordered chains of three define the doctrine.
    """

    questions = generate_fallback_mcqs(
        section_id=5,
        section_text=section_text,
        n=1,
        weak_topics=[],
        mastered_questions=[],
    )

    question = questions[0]

    assert set(question["options"].keys()) == {"A", "B", "C", "D"}
    assert question["correct_answer"] in {"A", "B", "C", "D"}


def test_fallback_generator_metadata_is_rule_based():
    section_text = """
    Section 5. Operational Tactics and Combat Doctrine

    Acquisition is the vulnerability. Protect the targeting window.
    """

    questions = generate_fallback_mcqs(
        section_id=5,
        section_text=section_text,
        n=1,
        weak_topics=[],
        mastered_questions=[],
    )

    assert questions[0]["generator"] == "fallback_rule_based"
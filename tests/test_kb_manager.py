from src.kb_manager import create_session_record


def test_create_session_record_calculates_score():
    questions = [
        {
            "question_id": "q1",
            "section_id": 5,
            "topic": "Topic A",
            "question": "Question 1?",
            "is_correct": True,
        },
        {
            "question_id": "q2",
            "section_id": 5,
            "topic": "Topic B",
            "question": "Question 2?",
            "is_correct": False,
        },
    ]

    session = create_session_record(
        session_id="test_session",
        sections=[5],
        questions=questions,
        session_type="cold_start",
    )

    assert session["session_id"] == "test_session"
    assert session["session_type"] == "cold_start"
    assert session["sections"] == [5]
    assert session["score"]["total"] == 2
    assert session["score"]["correct"] == 1
    assert session["score"]["wrong"] == 1
    assert session["score"]["accuracy"] == 50.0
    assert "Topic B" in session["weak_topics"]


def test_create_session_record_with_all_correct_has_no_weak_topics():
    questions = [
        {
            "question_id": "q1",
            "section_id": 8,
            "topic": "Topic A",
            "question": "Question 1?",
            "is_correct": True,
        }
    ]

    session = create_session_record(
        session_id="test_session_all_correct",
        sections=[8],
        questions=questions,
        session_type="adaptive",
    )

    assert session["score"]["total"] == 1
    assert session["score"]["correct"] == 1
    assert session["score"]["wrong"] == 0
    assert session["weak_topics"] == []
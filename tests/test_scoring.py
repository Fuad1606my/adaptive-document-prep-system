from src.scoring import score_questions, simulate_answers


def sample_questions():
    return [
        {
            "question_id": "q1",
            "section_id": 5,
            "topic": "Test Topic",
            "question": "What is the correct option?",
            "options": {
                "A": "Correct option",
                "B": "Wrong option",
                "C": "Wrong option",
                "D": "Wrong option",
            },
            "correct_answer": "A",
            "explanation": "A is the correct answer.",
        },
        {
            "question_id": "q2",
            "section_id": 8,
            "topic": "Another Topic",
            "question": "Which option is correct?",
            "options": {
                "A": "Wrong option",
                "B": "Correct option",
                "C": "Wrong option",
                "D": "Wrong option",
            },
            "correct_answer": "B",
            "explanation": "B is the correct answer.",
        },
    ]


def test_score_questions_marks_correct_answer():
    questions = sample_questions()
    answers = {"q1": "A", "q2": "B"}

    scored = score_questions(questions, answers)

    assert scored[0]["is_correct"] is True
    assert scored[1]["is_correct"] is True
    assert scored[0]["clarification"] == "Correct."


def test_score_questions_marks_wrong_answer():
    questions = sample_questions()
    answers = {"q1": "B", "q2": "A"}

    scored = score_questions(questions, answers)

    assert scored[0]["is_correct"] is False
    assert scored[1]["is_correct"] is False
    assert "Wrong. Correct answer is A" in scored[0]["clarification"]
    assert "Wrong. Correct answer is B" in scored[1]["clarification"]


def test_simulate_answers_all_correct():
    questions = sample_questions()

    answers = simulate_answers(questions, mode="all_correct")

    assert answers["q1"] == "A"
    assert answers["q2"] == "B"


def test_simulate_answers_all_wrong():
    questions = sample_questions()

    answers = simulate_answers(questions, mode="all_wrong")

    assert answers["q1"] != "A"
    assert answers["q2"] != "B"


def test_simulate_answers_mixed_returns_answers_for_all_questions():
    questions = sample_questions()

    answers = simulate_answers(questions, mode="mixed")

    assert set(answers.keys()) == {"q1", "q2"}
    assert answers["q1"] in ["A", "B", "C", "D"]
    assert answers["q2"] in ["A", "B", "C", "D"]
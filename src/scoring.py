import random
from typing import Any, Dict, List


def simulate_answers(
    questions: List[Dict[str, Any]],
    mode: str = "mixed",
) -> Dict[str, str]:
    """
    Simulate user answers for evaluation.
    Allowed modes: all_correct, all_wrong, mixed, random
    """
    answers = {}

    for index, question in enumerate(questions):
        qid = question["question_id"]
        correct = question["correct_answer"]
        option_keys = list(question["options"].keys())

        wrong_options = [key for key in option_keys if key != correct]

        if mode == "all_correct":
            answers[qid] = correct
        elif mode == "all_wrong":
            answers[qid] = wrong_options[0]
        elif mode == "random":
            answers[qid] = random.choice(option_keys)
        else:
            # mixed: intentionally answer some wrong to demonstrate adaptive behavior
            if index % 3 == 0:
                answers[qid] = wrong_options[0]
            else:
                answers[qid] = correct

    return answers


def score_questions(
    questions: List[Dict[str, Any]],
    answers: Dict[str, str],
) -> List[Dict[str, Any]]:
    """
    Attach user_answer and is_correct to every question.
    """
    scored_questions = []

    for question in questions:
        qid = question["question_id"]
        user_answer = answers.get(qid)
        correct_answer = question["correct_answer"]

        scored = dict(question)
        scored["user_answer"] = user_answer
        scored["is_correct"] = user_answer == correct_answer

        if scored["is_correct"]:
            scored["clarification"] = "Correct."
        else:
            correct_text = question["options"].get(correct_answer, "")
            scored["clarification"] = (
                f"Wrong. Correct answer is {correct_answer}: {correct_text}. "
                f"Clarification: {question.get('explanation', '')}"
            )

        scored_questions.append(scored)

    return scored_questions
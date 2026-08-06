"""Tests for deterministic interview report fields."""

from app.interview.nodes.generate_report import (
    _build_report_context,
    _build_structured_report,
    _build_summary,
)


def evaluation(score: int) -> dict:
    return {
        "dimensions": [
            {"dimension": "technical_correctness", "score": score},
            {"dimension": "implementation_depth", "score": score},
            {"dimension": "architecture_tradeoffs", "score": score},
            {"dimension": "personal_contribution", "score": score},
            {"dimension": "production_awareness", "score": score},
            {"dimension": "clarity", "score": score},
        ]
    }


def test_zero_score_answer_is_not_treated_as_fake_finish():
    state = {
        "questions": [{"question_id": "q1", "question_text": "Question"}],
        "answers": [{"answer_text": "I do not know"}],
        "evaluations": [evaluation(0)],
        "analyses": [{}],
        "claim_statuses": {},
        "contradictions": [],
    }

    summary = _build_summary(state)

    assert summary["overall_score"] == 0
    assert summary["questions_asked"] == 1
    assert summary["questions_answered"] == 1


def test_fake_finish_answer_is_excluded_from_structured_questions():
    state = {
        "questions": [
            {"question_id": "q1", "question_text": "Answered"},
            {"question_id": "q2", "question_text": "Forced finish"},
        ],
        "answers": [
            {"answer_text": "A real answer"},
            {"answer_text": "[END OF INTERVIEW]"},
        ],
        "evaluations": [evaluation(80), evaluation(0)],
        "analyses": [{}, {}],
        "claim_statuses": {"claim-1": {"status": "VERIFIED"}},
        "contradictions": [],
        "coverage": {},
    }

    report = _build_structured_report(state)
    summary = _build_summary(state)

    assert len(report["question_details"]) == 1
    assert report["ability_scores"]["technical_correctness"] == 80
    assert summary["overall_score"] == 80
    assert summary["questions_answered"] == 1

    context = _build_report_context(state)
    # The forced-finish question is excluded entirely, so asked == answered.
    assert "Questions Asked: 1" in context
    assert "Questions Answered: 1" in context
    assert "Authoritative Overall Score: 80.0/100" in context
    assert "[END OF INTERVIEW]" not in context

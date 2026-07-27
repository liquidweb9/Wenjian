"""Generate final interview report."""

from app.interview.state import InterviewState
from app.llm.agnes_api import AgnesGateway
from app.llm.model_router import get_tier
from app.observability.logging import logger

REPORT_PROMPT = """You are an interview report generator. Create a comprehensive interview report based on the complete interview data.

Hard requirements:
- Treat the deterministic metrics in the context as authoritative. Copy the overall score exactly; never recalculate or replace it.
- Clearly distinguish questions asked from questions answered.
- An unanswered question caused by "[END OF INTERVIEW]" is not a scored zero answer.
- USER_REQUESTED means the interview ended early at the candidate's request, not that report generation is incomplete.
- Never invent the current date, number of claims, scores, answers, technologies, or candidate facts.
- Do not output placeholders such as "[current date]".
- Base every conclusion on evidence shown in the context and state uncertainty when evidence is insufficient.

The report should include:
1. Overall score and confidence level
2. Ability profile across all dimensions
3. Topic-by-topic results
4. Claim verification status
5. Strongest project areas
6. Highest-risk claims
7. Contradictions found
8. Per-question summary with scores
9. Complete reference answers
10. Suggested resume improvements
11. Learning plan recommendations
12. Areas to focus in next mock interview

Be objective and evidence-based."""


async def generate_report_node(state: InterviewState) -> dict:
    """Generate the final interview report."""
    try:
        llm = AgnesGateway()
        report = await llm.generate_text(
            task_name="report_generation",
            system_prompt=REPORT_PROMPT,
            user_prompt=_build_report_context(state),
            model_tier=get_tier("report_generation"),
            temperature=0.3,
        )

        logger.info("report_generated", interview_id=state.get("interview_id"))

        return {
            "final_report": {
                "report_text": report,
                "interview_id": state.get("interview_id"),
                "summary": _build_summary(state),
                **_build_structured_report(state),
            },
            "finished": True,
            "stop_reason": "COMPLETED",
        }

    except Exception as e:
        logger.error("report_failed", error=str(e))
        return {
            "final_report": {
                "report_text": "Report generation failed. Basic results available.",
                "interview_id": state.get("interview_id"),
                "summary": _build_summary(state),
            },
            "finished": True,
            "stop_reason": "REPORT_FAILED",
        }


def _build_report_context(state: InterviewState) -> str:
    """Build context string for report generation."""
    summary = _build_summary(state)
    parts = [
        f"Target Role: {state.get('target_role', 'N/A')}",
        f"Questions Asked: {summary['questions_asked']}",
        f"Questions Answered: {summary['questions_answered']}",
        f"Max Turns: {state.get('max_turns', 0)}",
        f"Termination Reason: {state.get('stop_reason') or 'COMPLETED'}",
        f"Authoritative Overall Score: {summary['overall_score']}/100",
        f"Verified Claims: {summary['claims_verified']}",
        f"Contradictions Found: {summary['contradictions_found']}",
        "",
        "=== CLAIM STATUSES ===",
    ]
    for cid, status in state.get("claim_statuses", {}).items():
        parts.append(f"{cid}: {status.get('status', 'UNKNOWN')} (confidence: {status.get('confidence', 0)})")

    parts.append("")
    parts.append("=== QUESTIONS & ANSWERS ===")
    for i, q in enumerate(state.get("questions", [])):
        a = state.get("answers", [])[i] if i < len(state.get("answers", [])) else {}
        answer_text = a.get("answer_text", "")
        # Skip fake "[END OF INTERVIEW]" answer
        if answer_text.strip() == "[END OF INTERVIEW]":
            continue
        parts.append(f"Q{i+1}: {q.get('question_text', '')}")
        parts.append(f"A: {answer_text[:2000]}")
        if i < len(state.get("evaluations", [])):
            ev = state.get("evaluations", [])[i]
            for d in ev.get("dimensions", []):
                parts.append(f"  {d.get('dimension')}: {d.get('score')}/{d.get('max_score', 100)}")
        parts.append("")

    parts.append("=== COVERAGE ===")
    for tid, cov in state.get("coverage", {}).items():
        parts.append(f"{tid}: {cov:.0%}")

    return "\n".join(parts)


def _build_summary(state: InterviewState) -> dict:
    """Build a summary dict from interview data using weighted scoring."""
    from app.interview.rubrics import calculate_weighted_score

    answers = state.get("answers", [])
    evaluations = state.get("evaluations", [])

    real_evals = [
        evaluation
        for index, evaluation in enumerate(evaluations)
        if index < len(answers)
        and answers[index].get("answer_text", "").strip()
        and answers[index].get("answer_text", "").strip() != "[END OF INTERVIEW]"
    ]
    answered_count = sum(
        1
        for answer in answers
        if answer.get("answer_text", "").strip()
        and answer.get("answer_text", "").strip() != "[END OF INTERVIEW]"
    )
    asked_count = len(state.get("questions", []))

    if not real_evals:
        overall = 0
    else:
        total_weighted = [calculate_weighted_score(ev) for ev in real_evals]
        overall = sum(total_weighted) / len(total_weighted)

    summary = {
        "overall_score": round(overall, 1),
        "total_questions": asked_count,
        "questions_asked": asked_count,
        "questions_answered": answered_count,
        "claims_verified": sum(
            1 for s in state.get("claim_statuses", {}).values()
            if s.get("status") == "VERIFIED"
        ),
        "contradictions_found": len(state.get("contradictions", [])),
    }
    return summary


def _build_structured_report(state: InterviewState) -> dict:
    """Build deterministic fields consumed by the report UI."""
    from app.interview.rubrics import calculate_weighted_score

    questions = state.get("questions", [])
    answers = state.get("answers", [])
    evaluations = state.get("evaluations", [])
    analyses = state.get("analyses", [])
    question_details = []
    dimension_scores: dict[str, list[float]] = {}

    for index, question in enumerate(questions):
        answer = answers[index] if index < len(answers) else {}
        answer_text = answer.get("answer_text", "")
        if answer_text.strip() == "[END OF INTERVIEW]":
            continue

        evaluation = evaluations[index] if index < len(evaluations) else None
        analysis = analyses[index] if index < len(analyses) else None
        if evaluation and answer_text.strip():
            for dimension in evaluation.get("dimensions", []):
                name = dimension.get("dimension")
                if name:
                    dimension_scores.setdefault(name, []).append(
                        float(dimension.get("score", 0))
                    )

        question_details.append({
            "question_id": question.get("question_id"),
            "question_text": question.get("question_text", ""),
            "topic_id": question.get("topic_id"),
            "depth": question.get("depth"),
            "answer_text": answer_text or None,
            "score": (
                round(calculate_weighted_score(evaluation), 1)
                if evaluation and answer_text.strip()
                else None
            ),
            "evaluation": evaluation,
            "analysis": analysis,
        })

    ability_scores = {
        name: round(sum(scores) / len(scores), 1)
        for name, scores in dimension_scores.items()
        if scores
    }
    return {
        "ability_scores": ability_scores,
        "claim_statuses": state.get("claim_statuses", {}),
        "question_details": question_details,
        "contradictions": state.get("contradictions", []),
        "coverage": state.get("coverage", {}),
    }

"""Interview report API endpoints."""


from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy import select

from app.interview.rubrics import calculate_weighted_score
from app.persistence.database import async_session_factory
from app.persistence.models import (
    Interview,
    InterviewAnswer,
    InterviewQuestion,
    InterviewReport,
)

router = APIRouter(prefix="/interviews", tags=["reports"])


class ExportRequest(BaseModel):
    format: str = "json"  # "json" or "markdown"


@router.get("/{interview_id}/report")
async def get_report(interview_id: str):
    """Get interview report."""
    async with async_session_factory() as session:
        result = await session.execute(
            select(InterviewReport).where(InterviewReport.interview_id == interview_id)
        )
        report = result.scalar_one_or_none()

        if not report:
            interview_result = await session.execute(
                select(Interview).where(Interview.interview_id == interview_id)
            )
            interview = interview_result.scalar_one_or_none()
            if not interview:
                raise HTTPException(status_code=404, detail="Interview not found")
            return {"interview_id": interview_id, "report": None, "status": interview.status}

        enriched = await _enrich_report_from_database(
            session, interview_id, dict(report.data)
        )
        return {
            "interview_id": interview_id,
            "report": enriched,
            "created_at": report.created_at.isoformat() if report.created_at else None,
        }


@router.post("/{interview_id}/report/export")
async def export_report(interview_id: str, body: ExportRequest = ExportRequest()):
    """Export interview report as JSON or Markdown."""
    async with async_session_factory() as session:
        result = await session.execute(
            select(InterviewReport).where(InterviewReport.interview_id == interview_id)
        )
        report = result.scalar_one_or_none()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        if body.format == "markdown":
            md = _report_to_markdown(report.data)
            return PlainTextResponse(content=md, media_type="text/markdown")
        else:
            return report.data


def _report_to_markdown(data: dict) -> str:
    """Basic conversion of report dict to Markdown."""
    lines: list[str] = []
    lines.append("# Interview Report\n")

    score = data.get("overall_score") or data.get("score")
    if score is not None:
        lines.append(f"## Overall Score: {score}/100\n")

    summary = data.get("summary") or data.get("overall_summary")
    if summary:
        lines.append("## Summary\n")
        lines.append(str(summary))
        lines.append("")

    abilities = data.get("abilities") or data.get("ability_scores")
    if isinstance(abilities, dict):
        lines.append("## Ability Scores\n")
        for name, s in abilities.items():
            lines.append(f"- **{name}**: {s}")
        lines.append("")

    text = data.get("report_text") or data.get("text")
    if isinstance(text, str):
        lines.append("## Detailed Report\n")
        lines.append(text)
        lines.append("")

    suggestions = data.get("resume_suggestions") or data.get("suggestions")
    if isinstance(suggestions, list):
        lines.append("## Resume Suggestions\n")
        for s in suggestions:
            lines.append(f"- {s}")
        lines.append("")

    return "\n".join(lines)


async def _enrich_report_from_database(session, interview_id: str, data: dict) -> dict:
    """Backfill structured fields for reports created by older versions."""
    questions_result = await session.execute(
        select(InterviewQuestion).where(
            InterviewQuestion.interview_id == interview_id
        ).order_by(InterviewQuestion.created_at.asc())
    )
    answers_result = await session.execute(
        select(InterviewAnswer).where(
            InterviewAnswer.interview_id == interview_id
        ).order_by(InterviewAnswer.created_at.asc())
    )
    questions = questions_result.scalars().all()
    answers = answers_result.scalars().all()
    answers_by_question = {answer.question_id: answer for answer in answers}

    details = []
    ability_values: dict[str, list[float]] = {}
    scored_answers = []
    for question_row in questions:
        question = question_row.data or {}
        answer = answers_by_question.get(question_row.question_id)
        evaluation = answer.evaluation if answer else None
        answer_text = answer.answer_text if answer else None
        if answer_text and answer_text.strip() == "[END OF INTERVIEW]":
            continue

        score = None
        if evaluation and answer_text:
            score = round(calculate_weighted_score(evaluation), 1)
            scored_answers.append(score)
            for dimension in evaluation.get("dimensions", []):
                name = dimension.get("dimension")
                if name:
                    ability_values.setdefault(name, []).append(
                        float(dimension.get("score", 0))
                    )

        details.append({
            "question_id": question_row.question_id,
            "question_text": question.get("question_text", ""),
            "topic_id": question.get("topic_id"),
            "depth": question.get("depth"),
            "answer_text": answer_text,
            "score": score,
            "evaluation": evaluation,
            "analysis": answer.analysis if answer else None,
        })

    if details:
        data["question_details"] = details
    if ability_values:
        data["ability_scores"] = {
            name: round(sum(values) / len(values), 1)
            for name, values in ability_values.items()
        }

    summary = data.get("summary")
    if not isinstance(summary, dict):
        summary = {}
    summary.update({
        "overall_score": (
            round(sum(scored_answers) / len(scored_answers), 1)
            if scored_answers else 0
        ),
        "total_questions": len(details),
        "questions_asked": len(details),
        "questions_answered": sum(
            1 for detail in details if detail.get("answer_text")
        ),
    })
    data["summary"] = summary
    return data

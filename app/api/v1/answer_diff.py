"""Answer version diff API for Phase 2.4.

Exposes per-question answer versions so the frontend can render a same-question
re-answer comparison. Versions are derived from persisted InterviewAnswer rows;
diffs between consecutive versions are computed on the fly with AnswerDiffer.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.abilities.answer_diff import AnswerDiffer
from app.core.deps import get_current_user
from app.interview.rubrics import calculate_weighted_score
from app.persistence.database import get_session
from app.persistence.models import Interview, InterviewAnswer, User

router = APIRouter(prefix="/interviews", tags=["answer-diff"])


def _answer_score(evaluation: dict | None) -> float | None:
    """Extract a weighted overall score from an answer evaluation."""
    if not isinstance(evaluation, dict):
        return None
    try:
        return round(calculate_weighted_score(evaluation), 1)
    except Exception:
        return None


@router.get("/{interview_id}/questions/{question_id}/versions")
async def get_answer_versions(
    interview_id: str,
    question_id: str,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """List answer versions for a question with diff summaries.

    Args:
        interview_id: Interview ID
        question_id: Question ID
        user: Current authenticated user
        session: Database session

    Returns:
        Per-question version list with diffs between consecutive versions

    Raises:
        HTTPException: 404 if the interview is not found or not owned by user
    """
    interview = await session.get(Interview, interview_id)
    if not interview or interview.user_id != user.user_id:
        raise HTTPException(status_code=404, detail="Interview not found")

    result = await session.execute(
        select(InterviewAnswer)
        .where(
            InterviewAnswer.interview_id == interview_id,
            InterviewAnswer.question_id == question_id,
        )
        .order_by(InterviewAnswer.created_at.asc())
    )
    answers = list(result.scalars().all())

    if not answers:
        return {"interview_id": interview_id, "question_id": question_id, "versions": []}

    differ = AnswerDiffer()
    versions: list[dict[str, Any]] = []
    previous_text: str | None = None

    for version_number, answer in enumerate(answers, start=1):
        diff = None
        if previous_text is not None:
            diff = differ.compute_diff(previous_text, answer.answer_text)
        versions.append({
            "version_number": version_number,
            "answer_id": answer.answer_id,
            "answer_text": answer.answer_text,
            "created_at": answer.created_at.isoformat() if answer.created_at else None,
            "score": _answer_score(answer.evaluation),
            "diff": diff,
        })
        previous_text = answer.answer_text

    return {
        "interview_id": interview_id,
        "question_id": question_id,
        "versions": versions,
    }

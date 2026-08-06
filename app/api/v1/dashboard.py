"""Dashboard aggregation endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.persistence.database import get_session
from app.persistence.models import (
    Interview,
    InterviewReport,
    ResumeRevision,
    ResumeSource,
    User,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
async def get_dashboard_summary(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Aggregated stats for the dashboard landing page (scoped to the current user)."""

    total_resumes_r = await session.execute(
        select(func.count(ResumeSource.resume_id)).where(
            ResumeSource.user_id == user.user_id
        )
    )
    total_resumes = total_resumes_r.scalar() or 0

    pending_r = await session.execute(
        select(func.count(ResumeRevision.revision_id))
        .join(ResumeSource, ResumeSource.resume_id == ResumeRevision.resume_id)
        .where(
            ResumeRevision.status == "PARSED_UNCONFIRMED",
            ResumeSource.user_id == user.user_id,
        )
    )
    pending_reviews = pending_r.scalar() or 0

    total_interviews_r = await session.execute(
        select(func.count(Interview.interview_id)).where(
            Interview.user_id == user.user_id
        )
    )
    total_interviews = total_interviews_r.scalar() or 0

    completed_r = await session.execute(
        select(func.count(Interview.interview_id)).where(
            Interview.status == "finished",
            Interview.user_id == user.user_id,
        )
    )
    completed_interviews = completed_r.scalar() or 0

    in_progress_r = await session.execute(
        select(func.count(Interview.interview_id)).where(
            Interview.status == "in_progress",
            Interview.user_id == user.user_id,
        )
    )
    in_progress_count = in_progress_r.scalar() or 0

    # Recent resumes (last 5, current user only)
    recent_resumes_r = await session.execute(
        select(
            ResumeSource.resume_id,
            ResumeSource.file_name,
            ResumeSource.source_type,
            ResumeSource.created_at,
            ResumeRevision.status,
        )
        .join(ResumeRevision, ResumeRevision.resume_id == ResumeSource.resume_id)
        .where(ResumeSource.user_id == user.user_id)
        .order_by(ResumeSource.created_at.desc())
        .limit(5)
    )
    recent_resumes = [
        {
            "resume_id": row[0],
            "file_name": row[1],
            "source_type": row[2].value if hasattr(row[2], "value") else str(row[2]),
            "created_at": row[3].isoformat() if row[3] else None,
            "status": row[4].value if hasattr(row[4], "value") else str(row[4]) if row[4] else None,
        }
        for row in recent_resumes_r.all()
    ]

    # In-progress interviews (last 5)
    in_progress_list_r = await session.execute(
        select(
            Interview.interview_id,
            Interview.resume_id,
            Interview.target_role,
            Interview.mode,
            Interview.status,
            Interview.max_turns,
            Interview.created_at,
        )
        .where(
            Interview.status == "in_progress",
            Interview.user_id == user.user_id,
        )
        .order_by(Interview.created_at.desc())
        .limit(5)
    )
    in_progress_interviews = [
        {
            "interview_id": row[0],
            "resume_id": row[1],
            "target_role": row[2],
            "mode": row[3],
            "status": row[4],
            "max_turns": row[5],
            "created_at": row[6].isoformat() if row[6] else None,
        }
        for row in in_progress_list_r.all()
    ]

    # Average score from reports (best-effort — scores live in nested JSON)
    avg_score = None
    reports_r = await session.execute(
        select(InterviewReport.data)
        .join(Interview, Interview.interview_id == InterviewReport.interview_id)
        .where(Interview.user_id == user.user_id)
        .limit(100)
    )
    scores = []
    for (data,) in reports_r.all():
        if isinstance(data, dict) and "overall_score" in data:
            scores.append(data["overall_score"])
        elif isinstance(data, dict) and "score" in data:
            scores.append(data["score"])
    if scores:
        avg_score = round(sum(scores) / len(scores), 1)

    return {
        "total_resumes": total_resumes,
        "total_interviews": total_interviews,
        "pending_reviews": pending_reviews,
        "completed_interviews": completed_interviews,
        "in_progress_count": in_progress_count,
        "average_score": avg_score,
        "recent_resumes": recent_resumes,
        "in_progress_interviews": in_progress_interviews,
    }

"""Training plan API for Phase 2.4.

Lists, generates, and updates actionable training tasks derived from the
ability profile of a resume.
"""

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.abilities.aggregator import AbilityAggregator
from app.abilities.training_plan import TrainingPlanGenerator
from app.api.v1.abilities import _load_report_rows, _observations_by_competency
from app.core.deps import get_current_user
from app.core.ids import new_id
from app.persistence.database import get_session
from app.persistence.models import ResumeSource, TrainingTask, User

router = APIRouter(prefix="/training-plans", tags=["training-plans"])

_ALLOWED_STATUSES = {"PENDING", "IN_PROGRESS", "COMPLETED", "DISMISSED"}

_COMPETENCY_TITLES: dict[str, str] = {
    "technical_correctness": "技术正确性",
    "implementation_depth": "实现深度",
    "architecture_tradeoffs": "架构权衡",
    "personal_contribution": "个人贡献",
    "production_awareness": "生产意识",
    "clarity": "表达清晰度",
}


class UpdateTaskStatusRequest(BaseModel):
    status: str


def _competency_title(code: str) -> str:
    return _COMPETENCY_TITLES.get(code, code)


def _task_to_dict(task: TrainingTask) -> dict[str, Any]:
    return {
        "task_id": task.task_id,
        "task_type": task.task_type,
        "competency_code": task.competency_code,
        "title": task.title,
        "description": task.description,
        "completion_criteria": task.completion_criteria or [],
        "status": task.status,
        "priority": task.priority,
        "resume_id": task.resume_id,
        "interview_id": task.interview_id,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
    }


@router.get("")
async def list_tasks(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    resume_id: str | None = None,
):
    """List training tasks owned by the current user.

    Args:
        resume_id: Optional filter by resume
        user: Current authenticated user
        session: Database session

    Returns:
        List of training tasks sorted by priority descending
    """
    stmt = select(TrainingTask).where(TrainingTask.user_id == user.user_id)
    if resume_id:
        resume = await session.get(ResumeSource, resume_id)
        if not resume or resume.user_id != user.user_id:
            raise HTTPException(status_code=404, detail="Resume not found")
        stmt = stmt.where(TrainingTask.resume_id == resume_id)
    stmt = stmt.order_by(TrainingTask.priority.desc(), TrainingTask.created_at.asc())

    result = await session.execute(stmt)
    tasks = result.scalars().all()
    return {"tasks": [_task_to_dict(task) for task in tasks]}


@router.post("/{resume_id}/generate")
async def generate_tasks(
    resume_id: str,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Generate training tasks from the resume's ability profile.

    Replaces any pending/in-progress tasks for the resume with a freshly
    generated plan; completed and dismissed tasks are preserved.

    Args:
        resume_id: Resume ID
        user: Current authenticated user
        session: Database session

    Returns:
        The generated task list

    Raises:
        HTTPException: 404 if resume not found or not owned by user
    """
    resume = await session.get(ResumeSource, resume_id)
    if not resume or resume.user_id != user.user_id:
        raise HTTPException(status_code=404, detail="Resume not found")

    rows = await _load_report_rows(session, resume_id, user.user_id)
    observations_by_competency, history_by_competency, _ = _observations_by_competency(rows)

    generator = TrainingPlanGenerator()
    aggregator = AbilityAggregator()
    generated: list[dict[str, Any]] = []

    for code, observations in observations_by_competency.items():
        profile = aggregator.aggregate_observations(observations)
        history = history_by_competency[code]
        interview_id = history[-1]["interview_id"] if history else ""
        tasks = generator.generate_tasks(
            ability_profile=profile,
            competency_code=code,
            competency_title=_competency_title(code),
            interview_id=interview_id,
            resume_id=resume_id,
            user_id=user.user_id,
        )
        generated.extend(tasks)

    if generated:
        await session.execute(
            delete(TrainingTask).where(
                TrainingTask.resume_id == resume_id,
                TrainingTask.user_id == user.user_id,
                TrainingTask.status.in_(["PENDING", "IN_PROGRESS"]),
            )
        )

    for task in generated:
        session.add(
            TrainingTask(
                task_id=new_id("task"),
                user_id=user.user_id,
                resume_id=resume_id,
                interview_id=task["interview_id"],
                task_type=task["task_type"],
                competency_code=task["competency_code"],
                title=task["title"],
                description=task["description"],
                completion_criteria=task["completion_criteria"],
                status="PENDING",
                priority=int(round(task["priority"] * 100)),
            )
        )

    await session.commit()

    result = await session.execute(
        select(TrainingTask)
        .where(
            TrainingTask.resume_id == resume_id,
            TrainingTask.user_id == user.user_id,
        )
        .order_by(TrainingTask.priority.desc())
    )
    return {"tasks": [_task_to_dict(t) for t in result.scalars().all()]}


@router.patch("/{task_id}")
async def update_task_status(
    task_id: str,
    body: UpdateTaskStatusRequest,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Update a training task's status.

    Args:
        task_id: Task ID
        body: New status
        user: Current authenticated user
        session: Database session

    Returns:
        The updated task

    Raises:
        HTTPException: 404 if task not found or not owned by user; 400 on bad status
    """
    if body.status not in _ALLOWED_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status: {body.status}")

    task = await session.get(TrainingTask, task_id)
    if not task or task.user_id != user.user_id:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = body.status
    if body.status == "COMPLETED":
        task.completed_at = datetime.utcnow()
    await session.commit()
    await session.refresh(task)
    return _task_to_dict(task)

"""Repository layer for database operations with permission enforcement.

M2.6: All repositories enforce object-level permissions (user can only access own data).
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Sequence

from app.persistence.models import (
    User, ResumeSource, Interview, InterviewReport,
    JobTarget, AbilityProfile, TrainingTask,
)
from app.core.exceptions import PermissionDeniedError


# ============================================================
# User Repository (M2.6)
# ============================================================

class UserRepository:
    """User account operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: str) -> User | None:
        """Get user by ID."""
        result = await self.session.execute(
            select(User).where(User.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email."""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        """Create a new user."""
        self.session.add(user)
        return user

    async def update_last_login(self, user_id: str) -> None:
        """Update user's last login timestamp."""
        from datetime import datetime
        user = await self.get_by_id(user_id)
        if user:
            user.last_login_at = datetime.utcnow()


# ============================================================
# Resume Repository (with permission checks)
# ============================================================

class ResumeRepository:
    """Resume operations with user ownership enforcement."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, resume_id: str, user_id: str) -> ResumeSource | None:
        """Get resume by ID, enforcing ownership.

        Args:
            resume_id: Resume ID
            user_id: Current user ID

        Returns:
            ResumeSource if found and owned by user, None otherwise
        """
        result = await self.session.execute(
            select(ResumeSource).where(
                and_(
                    ResumeSource.resume_id == resume_id,
                    ResumeSource.user_id == user_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: str, limit: int = 100, offset: int = 0) -> Sequence[ResumeSource]:
        """List resumes owned by user."""
        result = await self.session.execute(
            select(ResumeSource)
            .where(ResumeSource.user_id == user_id)
            .order_by(ResumeSource.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def create(self, resume: ResumeSource) -> ResumeSource:
        """Create a new resume."""
        self.session.add(resume)
        return resume

    async def delete(self, resume_id: str, user_id: str) -> bool:
        """Delete resume, enforcing ownership.

        Args:
            resume_id: Resume ID
            user_id: Current user ID

        Returns:
            True if deleted, False if not found

        Raises:
            PermissionDeniedError if user doesn't own the resume
        """
        resume = await self.get_by_id(resume_id, user_id)
        if not resume:
            return False

        await self.session.delete(resume)
        return True


# ============================================================
# Interview Repository (with permission checks)
# ============================================================

class InterviewRepository:
    """Interview operations with user ownership enforcement."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, interview_id: str, user_id: str) -> Interview | None:
        """Get interview by ID, enforcing ownership.

        Args:
            interview_id: Interview ID
            user_id: Current user ID

        Returns:
            Interview if found and owned by user, None otherwise
        """
        result = await self.session.execute(
            select(Interview).where(
                and_(
                    Interview.interview_id == interview_id,
                    Interview.user_id == user_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: str, limit: int = 100, offset: int = 0) -> Sequence[Interview]:
        """List interviews owned by user."""
        result = await self.session.execute(
            select(Interview)
            .where(Interview.user_id == user_id)
            .order_by(Interview.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def create(self, interview: Interview) -> Interview:
        """Create a new interview."""
        self.session.add(interview)
        return interview

    async def delete(self, interview_id: str, user_id: str) -> bool:
        """Delete interview, enforcing ownership.

        Args:
            interview_id: Interview ID
            user_id: Current user ID

        Returns:
            True if deleted, False if not found

        Raises:
            PermissionDeniedError if user doesn't own the interview
        """
        interview = await self.get_by_id(interview_id, user_id)
        if not interview:
            return False

        await self.session.delete(interview)
        return True


# ============================================================
# Report Repository (with permission checks)
# ============================================================

class ReportRepository:
    """Report operations with user ownership enforcement."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_interview_id(self, interview_id: str, user_id: str) -> InterviewReport | None:
        """Get report by interview ID, enforcing ownership.

        First checks if user owns the interview, then retrieves report.
        """
        # Check interview ownership
        interview_result = await self.session.execute(
            select(Interview).where(
                and_(
                    Interview.interview_id == interview_id,
                    Interview.user_id == user_id,
                )
            )
        )
        interview = interview_result.scalar_one_or_none()
        if not interview:
            return None

        # Get report
        report_result = await self.session.execute(
            select(InterviewReport).where(InterviewReport.interview_id == interview_id)
        )
        return report_result.scalar_one_or_none()


# ============================================================
# Job Target Repository (with permission checks)
# ============================================================

class JobTargetRepository:
    """Job target operations with user ownership enforcement."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, job_target_id: str, user_id: str) -> JobTarget | None:
        """Get job target by ID, enforcing ownership.

        Allows access to templates (user_id is None) and user-owned targets.
        """
        result = await self.session.execute(
            select(JobTarget).where(
                and_(
                    JobTarget.job_target_id == job_target_id,
                    (JobTarget.user_id == user_id) | (JobTarget.is_template == True),
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_templates(self) -> Sequence[JobTarget]:
        """List all job target templates (public)."""
        result = await self.session.execute(
            select(JobTarget).where(JobTarget.is_template == True)
        )
        return result.scalars().all()

    async def list_by_user(self, user_id: str) -> Sequence[JobTarget]:
        """List job targets owned by user."""
        result = await self.session.execute(
            select(JobTarget).where(JobTarget.user_id == user_id)
        )
        return result.scalars().all()

    async def create(self, job_target: JobTarget) -> JobTarget:
        """Create a new job target."""
        self.session.add(job_target)
        return job_target


# ============================================================
# Ability Profile Repository (with permission checks)
# ============================================================

class AbilityProfileRepository:
    """Ability profile operations with user ownership enforcement."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_user(self, user_id: str, resume_id: str | None = None) -> Sequence[AbilityProfile]:
        """List ability profiles owned by user.

        Args:
            user_id: Current user ID
            resume_id: Optional filter by resume ID
        """
        query = select(AbilityProfile).where(AbilityProfile.user_id == user_id)

        if resume_id:
            query = query.where(AbilityProfile.resume_id == resume_id)

        result = await self.session.execute(query)
        return result.scalars().all()


# ============================================================
# Training Task Repository (with permission checks)
# ============================================================

class TrainingTaskRepository:
    """Training task operations with user ownership enforcement."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_user(
        self,
        user_id: str,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[TrainingTask]:
        """List training tasks owned by user.

        Args:
            user_id: Current user ID
            status: Optional filter by status
            limit: Max results
            offset: Pagination offset
        """
        query = select(TrainingTask).where(TrainingTask.user_id == user_id)

        if status:
            query = query.where(TrainingTask.status == status)

        query = query.order_by(TrainingTask.priority.desc(), TrainingTask.created_at.desc())
        query = query.limit(limit).offset(offset)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def update_status(self, task_id: str, user_id: str, status: str) -> bool:
        """Update task status, enforcing ownership.

        Args:
            task_id: Task ID
            user_id: Current user ID
            status: New status

        Returns:
            True if updated, False if not found
        """
        result = await self.session.execute(
            select(TrainingTask).where(
                and_(
                    TrainingTask.task_id == task_id,
                    TrainingTask.user_id == user_id,
                )
            )
        )
        task = result.scalar_one_or_none()

        if not task:
            return False

        task.status = status
        if status == "COMPLETED":
            from datetime import datetime
            task.completed_at = datetime.utcnow()

        return True

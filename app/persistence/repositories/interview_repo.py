"""Interview repository for database operations."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.persistence.models import (
    Interview, InterviewQuestion, InterviewAnswer, InterviewReport,
)


class InterviewRepository:
    """Repository for interview-related database operations.

    Does NOT commit transactions — the caller is responsible for session.commit().
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_interview(self, interview: Interview) -> None:
        self.session.add(interview)

    async def get_interview(self, interview_id: str) -> Interview | None:
        result = await self.session.execute(
            select(Interview).where(Interview.interview_id == interview_id)
        )
        return result.scalar_one_or_none()

    async def add_question(self, question: InterviewQuestion) -> None:
        self.session.add(question)

    async def add_answer(self, answer: InterviewAnswer) -> None:
        self.session.add(answer)

    async def add_report(self, report: InterviewReport) -> None:
        self.session.add(report)

    async def get_report(self, interview_id: str) -> InterviewReport | None:
        result = await self.session.execute(
            select(InterviewReport).where(InterviewReport.interview_id == interview_id)
        )
        return result.scalar_one_or_none()

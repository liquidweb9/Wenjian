"""FastAPI dependency injection helpers."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.persistence.database import get_session
from app.persistence.repositories.resume_repo import ResumeRepository
from app.persistence.repositories.interview_repo import InterviewRepository
from app.resume.service import ResumeService
from app.llm.agnes_api import AgnesGateway


async def get_resume_repo(session: AsyncSession = Depends(get_session)):
    return ResumeRepository(session)


async def get_interview_repo(session: AsyncSession = Depends(get_session)):
    return InterviewRepository(session)


def get_resume_service() -> ResumeService:
    return ResumeService()


def get_llm_gateway() -> AgnesGateway:
    return AgnesGateway()


__all__ = [
    "settings",
    "get_session",
    "get_resume_repo",
    "get_interview_repo",
    "get_resume_service",
    "get_llm_gateway",
]

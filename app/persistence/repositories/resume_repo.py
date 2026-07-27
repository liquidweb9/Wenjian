"""Resume repository for database operations."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.persistence.models import (
    ResumeSource, ResumeRevision, ResumeBlock, ResumeProfile, ResumeClaim,
)
from app.core.enums import ResumeStatus


class ResumeRepository:
    """Repository for resume-related database operations.

    Does NOT commit transactions — the caller is responsible for session.commit().
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_source(self, source: ResumeSource) -> None:
        self.session.add(source)

    async def get_source(self, resume_id: str) -> ResumeSource | None:
        result = await self.session.execute(
            select(ResumeSource).where(ResumeSource.resume_id == resume_id)
        )
        return result.scalar_one_or_none()

    async def add_revision(self, revision: ResumeRevision) -> None:
        self.session.add(revision)

    async def add_blocks(self, blocks: list[ResumeBlock]) -> None:
        self.session.add_all(blocks)

    async def update_revision_status(self, revision_id: str, status: ResumeStatus) -> None:
        result = await self.session.execute(
            select(ResumeRevision).where(ResumeRevision.revision_id == revision_id)
        )
        rev = result.scalar_one_or_none()
        if rev:
            rev.status = status

    async def get_revision(self, revision_id: str) -> ResumeRevision | None:
        result = await self.session.execute(
            select(ResumeRevision).where(ResumeRevision.revision_id == revision_id)
        )
        return result.scalar_one_or_none()

    async def add_profile(self, profile: ResumeProfile) -> None:
        self.session.add(profile)

    async def add_claim(self, claim: ResumeClaim) -> None:
        self.session.add(claim)

    async def get_claims_by_resume(self, resume_id: str) -> list[ResumeClaim]:
        result = await self.session.execute(
            select(ResumeClaim).where(ResumeClaim.resume_id == resume_id)
        )
        return list(result.scalars().all())

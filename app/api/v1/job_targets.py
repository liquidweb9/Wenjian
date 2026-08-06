"""Job Target API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.ids import new_id
from app.job_target.jd_parser import JDParser
from app.llm.agnes_api import AgnesGateway
from app.persistence.database import get_session
from app.persistence.models import JobRequirement, JobTarget, User

router = APIRouter(prefix="/job-targets", tags=["job-targets"])


# ============================================================
# Request/Response Models
# ============================================================

class RequirementCreate(BaseModel):
    """Request model for creating a requirement."""
    competency_code: str
    title: str
    description: str | None = None
    importance: float = Field(ge=0.0, le=1.0)
    expected_level: int = Field(ge=1, le=5)
    evidence_expectation: list[str] = Field(min_length=2)


class JobTargetCreate(BaseModel):
    """Request model for creating a job target."""
    title: str
    level: str = Field(pattern="^(intern|junior|mid|senior|staff)$")
    interview_round: str = Field(
        default="technical",
        pattern="^(resume|project|technical|system_design)$"
    )
    description: str | None = None
    source: str = Field(default="manual", pattern="^(template|pasted_jd|manual)$")
    raw_jd: str | None = None
    requirements: list[RequirementCreate]


class JobTargetUpdate(BaseModel):
    """Request model for updating a job target (all fields optional)."""
    title: str | None = None
    level: str | None = Field(default=None, pattern="^(intern|junior|mid|senior|staff)$")
    interview_round: str | None = Field(
        default=None,
        pattern="^(resume|project|technical|system_design)$"
    )
    description: str | None = None
    source: str | None = Field(default=None, pattern="^(template|pasted_jd|manual)$")
    raw_jd: str | None = None
    requirements: list[RequirementCreate] | None = None

    @model_validator(mode="after")
    def reject_null_required_fields(self) -> "JobTargetUpdate":
        """Reject explicit null for non-nullable DB columns."""
        for field in ("title", "level", "interview_round", "source"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self


class ParseJDRequest(BaseModel):
    """Request model for parsing JD text."""
    jd_text: str = Field(min_length=10)


class RequirementResponse(BaseModel):
    """Response model for a requirement."""
    requirement_id: str
    competency_code: str
    title: str
    description: str | None
    importance: float
    expected_level: int
    evidence_expectation: list[str]

    class Config:
        from_attributes = True


class JobTargetResponse(BaseModel):
    """Response model for a job target."""
    job_target_id: str
    title: str
    level: str
    interview_round: str
    description: str | None
    source: str
    raw_jd: str | None
    requirements: list[RequirementResponse]
    created_at: str

    class Config:
        from_attributes = True


class ParseJDResponse(BaseModel):
    """Response model for JD parsing."""
    requirements: list[RequirementCreate]
    inferred_level: str | None
    inferred_round: str | None


def _build_job_target_response(job_target: JobTarget) -> JobTargetResponse:
    """Build a JobTargetResponse from a JobTarget model instance."""
    return JobTargetResponse(
        job_target_id=job_target.job_target_id,
        title=job_target.title,
        level=job_target.level,
        interview_round=job_target.interview_round,
        description=job_target.description,
        source=job_target.source,
        raw_jd=job_target.raw_jd,
        requirements=[
            RequirementResponse(
                requirement_id=req.requirement_id,
                competency_code=req.competency_code,
                title=req.title,
                description=req.description,
                importance=req.importance,
                expected_level=req.expected_level,
                evidence_expectation=req.evidence_expectation,
            )
            for req in job_target.requirements
        ],
        created_at=job_target.created_at.isoformat(),
    )


# ============================================================
# Endpoints
# ============================================================

@router.post("", response_model=JobTargetResponse, status_code=status.HTTP_201_CREATED)
async def create_job_target(
    data: JobTargetCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
):
    """Create a new job target with requirements.

    Args:
        data: Job target creation data
        user: Authenticated user
        db: Database session

    Returns:
        Created job target with requirements
    """
    # Create job target
    job_target = JobTarget(
        job_target_id=new_id("jt"),
        user_id=user.user_id,
        title=data.title,
        level=data.level,
        interview_round=data.interview_round,
        description=data.description,
        source=data.source,
        raw_jd=data.raw_jd,
    )
    db.add(job_target)

    # Create requirements
    for req_data in data.requirements:
        requirement = JobRequirement(
            requirement_id=new_id("req"),
            job_target_id=job_target.job_target_id,
            competency_code=req_data.competency_code,
            title=req_data.title,
            description=req_data.description or "",
            importance=req_data.importance,
            expected_level=req_data.expected_level,
            evidence_expectation=req_data.evidence_expectation,
        )
        db.add(requirement)

    await db.commit()
    await db.refresh(job_target)
    await db.refresh(job_target, attribute_names=["requirements"])

    return _build_job_target_response(job_target)


@router.get("/{job_target_id}", response_model=JobTargetResponse)
async def get_job_target(
    job_target_id: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
):
    """Get a job target by ID.

    Args:
        job_target_id: Job target ID
        user: Authenticated user
        db: Database session

    Returns:
        Job target with requirements

    Raises:
        HTTPException: 404 if job target not found or not owned by user
    """
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    stmt = (
        select(JobTarget)
        .where(JobTarget.job_target_id == job_target_id)
        .options(selectinload(JobTarget.requirements))
    )
    result = await db.execute(stmt)
    job_target = result.scalar_one_or_none()

    if not job_target or job_target.user_id != user.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job target {job_target_id} not found",
        )

    return JobTargetResponse(
        job_target_id=job_target.job_target_id,
        title=job_target.title,
        level=job_target.level,
        interview_round=job_target.interview_round,
        description=job_target.description,
        source=job_target.source,
        raw_jd=job_target.raw_jd,
        requirements=[
            RequirementResponse(
                requirement_id=req.requirement_id,
                competency_code=req.competency_code,
                title=req.title,
                description=req.description,
                importance=req.importance,
                expected_level=req.expected_level,
                evidence_expectation=req.evidence_expectation,
            )
            for req in job_target.requirements
        ],
        created_at=job_target.created_at.isoformat(),
    )


@router.post("/parse-jd", response_model=ParseJDResponse)
async def parse_jd(
    data: ParseJDRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
):
    """Parse JD text and extract structured requirements.

    This is a helper endpoint for users editing job targets.
    It parses JD text but doesn't save - user can review and edit before saving.

    Args:
        data: JD text to parse
        user: Authenticated user
        db: Database session

    Returns:
        Parsed requirements (not saved)
    """
    # Create LLM gateway
    gateway = AgnesGateway()

    # Parse JD
    parser = JDParser(llm=gateway)
    try:
        result = await parser.parse_jd(data.jd_text)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Convert to response format
    return ParseJDResponse(
        requirements=[
            RequirementCreate(
                competency_code=req.competency_code,
                title=req.title,
                description=req.description,
                importance=req.importance,
                expected_level=req.expected_level,
                evidence_expectation=req.evidence_expectation,
            )
            for req in result.requirements
        ],
        inferred_level=result.inferred_level,
        inferred_round=result.inferred_round,
    )


@router.patch("/{job_target_id}", response_model=JobTargetResponse)
async def update_job_target(
    job_target_id: str,
    data: JobTargetUpdate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
):
    """Update an existing job target.

    Args:
        job_target_id: Job target ID
        data: Fields to update
        user: Authenticated user
        db: Database session

    Returns:
        Updated job target with requirements

    Raises:
        HTTPException: 404 if job target not found or not owned by user
    """
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    stmt = (
        select(JobTarget)
        .where(JobTarget.job_target_id == job_target_id)
        .options(selectinload(JobTarget.requirements))
    )
    result = await db.execute(stmt)
    job_target = result.scalar_one_or_none()

    if not job_target or job_target.user_id != user.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job target {job_target_id} not found",
        )

    update_data = data.model_dump(exclude_unset=True)
    update_data.pop("requirements", None)  # handled below from parsed models

    for field, value in update_data.items():
        setattr(job_target, field, value)

    if data.requirements is not None:
        job_target.requirements.clear()  # delete-orphan cascades the delete
        for req_data in data.requirements:
            job_target.requirements.append(
                JobRequirement(
                    requirement_id=new_id("req"),
                    job_target_id=job_target.job_target_id,
                    competency_code=req_data.competency_code,
                    title=req_data.title,
                    description=req_data.description or "",
                    importance=req_data.importance,
                    expected_level=req_data.expected_level,
                    evidence_expectation=req_data.evidence_expectation,
                )
            )

    await db.commit()
    await db.refresh(job_target)
    await db.refresh(job_target, attribute_names=["requirements"])

    return _build_job_target_response(job_target)


@router.get("", response_model=list[JobTargetResponse])
async def list_job_targets(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
    level: str | None = None,
):
    """List job targets owned by the current user.

    Args:
        user: Authenticated user
        db: Database session
        level: Optional filter by level

    Returns:
        List of job targets
    """
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    stmt = (
        select(JobTarget)
        .where(JobTarget.user_id == user.user_id)
        .options(selectinload(JobTarget.requirements))
    )

    if level:
        stmt = stmt.where(JobTarget.level == level)

    result = await db.execute(stmt)
    job_targets = result.scalars().all()

    return [
        JobTargetResponse(
            job_target_id=jt.job_target_id,
            title=jt.title,
            level=jt.level,
            interview_round=jt.interview_round,
            description=jt.description,
            source=jt.source,
            raw_jd=jt.raw_jd,
            requirements=[
                RequirementResponse(
                    requirement_id=req.requirement_id,
                    competency_code=req.competency_code,
                    title=req.title,
                    description=req.description,
                    importance=req.importance,
                    expected_level=req.expected_level,
                    evidence_expectation=req.evidence_expectation,
                )
                for req in jt.requirements
            ],
            created_at=jt.created_at.isoformat(),
        )
        for jt in job_targets
    ]

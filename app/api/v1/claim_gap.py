"""Claim Gap Analysis API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.persistence.database import get_session
from app.persistence.models import JobTarget, ResumeClaim, ResumeSource, User
from app.planning import (
    ClaimGapAnalyzer,
    ClaimMapper,
    InterviewPlanBuilder,
)

router = APIRouter(prefix="/claim-gap", tags=["claim-gap"])


# ============================================================
# Request/Response Models
# ============================================================

class ClaimGapRequest(BaseModel):
    """Request model for claim gap analysis."""
    resume_id: str
    job_target_id: str


class CompetencyMappingResponse(BaseModel):
    """Response model for competency mapping."""
    claim_id: str
    competency_code: str
    mapping_strength: float
    mapping_reason: str


class RequirementMappingResponse(BaseModel):
    """Response model for requirement mapping."""
    claim_id: str
    requirement_id: str
    competency_code: str
    relevance: float
    coverage_level: int
    mapping_reason: str


class GapResponse(BaseModel):
    """Response model for a gap."""
    gap_type: str
    claim_id: str | None
    requirement_id: str | None
    competency_code: str
    priority: float
    reason_codes: list[str]
    explanation: str
    claim_text: str | None
    requirement_title: str | None
    requirement_importance: float | None
    requirement_expected_level: int | None
    claim_coverage_level: int | None


class CoverageStatsResponse(BaseModel):
    """Response model for coverage statistics."""
    total_requirements: int
    covered_requirements: int
    uncovered_requirements: int
    weak_evidence_count: int
    high_priority_gaps: int
    coverage_percentage: float


class InterviewTargetResponse(BaseModel):
    """Response model for interview target."""
    claim_id: str | None
    requirement_id: str | None
    competency_code: str
    priority: float
    reason_codes: list[str]
    explanation: str
    gap_type: str
    claim_text: str | None
    requirement_title: str | None


class ClaimGapResponse(BaseModel):
    """Response model for claim gap analysis."""
    resume_id: str
    job_target_id: str
    gaps: list[GapResponse]
    coverage_stats: CoverageStatsResponse
    interview_plan: dict  # InterviewPlan details
    high_priority_targets: list[str]


# ============================================================
# Endpoints
# ============================================================

@router.post("", response_model=ClaimGapResponse)
async def analyze_claim_gap(
    data: ClaimGapRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
):
    """Analyze claim gap between resume and job target.

    Args:
        data: Resume ID and job target ID
        user: Authenticated user
        db: Database session

    Returns:
        Claim gap analysis with interview plan

    Raises:
        HTTPException: 404 if resume or job target not found or not owned by user
    """
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    # 1. Verify resume ownership
    stmt = select(ResumeSource).where(
        ResumeSource.resume_id == data.resume_id,
        ResumeSource.user_id == user.user_id,
    )
    resume = (await db.execute(stmt)).scalar_one_or_none()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume {data.resume_id} not found",
        )

    # 2. Fetch job target with requirements (ownership checked)
    stmt = (
        select(JobTarget)
        .where(
            JobTarget.job_target_id == data.job_target_id,
            JobTarget.user_id == user.user_id,
        )
        .options(selectinload(JobTarget.requirements))
    )
    result = await db.execute(stmt)
    job_target = result.scalar_one_or_none()

    if not job_target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job target {data.job_target_id} not found",
        )

    # 3. Fetch resume claims (may be empty — analyzer marks all requirements uncovered)
    stmt = select(ResumeClaim).where(ResumeClaim.resume_id == data.resume_id)
    result = await db.execute(stmt)
    claims = result.scalars().all()

    # 3. Prepare requirements for mapping
    requirements = [
        {
            "requirement_id": req.requirement_id,
            "competency_code": req.competency_code,
            "title": req.title,
            "importance": req.importance,
            "expected_level": req.expected_level,
        }
        for req in job_target.requirements
    ]

    # 4. Map claims to requirements
    mapper = ClaimMapper()
    claim_mappings = [
        mapper.map_claim(
            claim_id=claim.claim_id,
            claim_text=claim.data.get("claim_text", ""),
            requirements=requirements,
        )
        for claim in claims
    ]

    # 5. Analyze gaps
    analyzer = ClaimGapAnalyzer()
    gap_result = analyzer.analyze_gaps(claim_mappings, requirements)

    # 6. Build interview plan
    builder = InterviewPlanBuilder()
    interview_plan = builder.build_plan(gap_result)

    # 7. Build response
    return ClaimGapResponse(
        resume_id=data.resume_id,
        job_target_id=data.job_target_id,
        gaps=[
            GapResponse(
                gap_type=gap.gap_type.value,
                claim_id=gap.claim_id,
                requirement_id=gap.requirement_id,
                competency_code=gap.competency_code,
                priority=gap.priority,
                reason_codes=[rc.value for rc in gap.reason_codes],
                explanation=gap.explanation,
                claim_text=gap.claim_text,
                requirement_title=gap.requirement_title,
                requirement_importance=gap.requirement_importance,
                requirement_expected_level=gap.requirement_expected_level,
                claim_coverage_level=gap.claim_coverage_level,
            )
            for gap in gap_result.gaps
        ],
        coverage_stats=CoverageStatsResponse(
            total_requirements=gap_result.coverage_stats.total_requirements,
            covered_requirements=gap_result.coverage_stats.covered_requirements,
            uncovered_requirements=gap_result.coverage_stats.uncovered_requirements,
            weak_evidence_count=gap_result.coverage_stats.weak_evidence_count,
            high_priority_gaps=gap_result.coverage_stats.high_priority_gaps,
            coverage_percentage=gap_result.coverage_stats.coverage_percentage,
        ),
        interview_plan={
            "total_targets": interview_plan.total_targets,
            "high_priority_count": interview_plan.high_priority_count,
            "targets": [
                InterviewTargetResponse(
                    claim_id=target.claim_id,
                    requirement_id=target.requirement_id,
                    competency_code=target.competency_code,
                    priority=target.priority,
                    reason_codes=target.reason_codes,
                    explanation=target.explanation,
                    gap_type=target.gap_type,
                    claim_text=target.claim_text,
                    requirement_title=target.requirement_title,
                ).model_dump()
                for target in interview_plan.targets
            ],
        },
        high_priority_targets=gap_result.high_priority_targets,
    )


@router.get("/resume/{resume_id}/job-target/{job_target_id}", response_model=ClaimGapResponse)
async def get_claim_gap(
    resume_id: str,
    job_target_id: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
):
    """Get claim gap analysis (same as POST but via GET for caching).

    Args:
        resume_id: Resume ID
        job_target_id: Job target ID
        user: Authenticated user
        db: Database session

    Returns:
        Claim gap analysis
    """
    # Reuse the POST endpoint logic
    request = ClaimGapRequest(resume_id=resume_id, job_target_id=job_target_id)
    return await analyze_claim_gap(request, user, db)

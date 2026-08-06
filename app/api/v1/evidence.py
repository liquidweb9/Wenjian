"""Evidence API endpoints for Phase 2.

Provides REST API access to evidence tracking data including verification points,
transitions, and contradictions.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.persistence.database import get_session
from app.persistence.models import (
    Interview,
    ResumeClaim,
    ResumeSource,
    User,
    VerificationPoint,
)
from app.persistence.repositories.evidence_repo import EvidenceRepository

router = APIRouter(prefix="/evidence", tags=["evidence"])


async def _vp_owned_by(
    session: AsyncSession, verification_point_id: str, user_id: str
) -> bool:
    """True if the verification point's claim belongs to the given user."""
    result = await session.execute(
        select(VerificationPoint.verification_point_id)
        .join(ResumeClaim, ResumeClaim.claim_id == VerificationPoint.claim_id)
        .join(ResumeSource, ResumeSource.resume_id == ResumeClaim.resume_id)
        .where(
            VerificationPoint.verification_point_id == verification_point_id,
            ResumeSource.user_id == user_id,
        )
    )
    return result.scalar_one_or_none() is not None


async def _claim_owned_by(
    session: AsyncSession, claim_id: str, user_id: str
) -> bool:
    """True if the claim's resume belongs to the given user."""
    result = await session.execute(
        select(ResumeClaim.claim_id)
        .join(ResumeSource, ResumeSource.resume_id == ResumeClaim.resume_id)
        .where(ResumeClaim.claim_id == claim_id, ResumeSource.user_id == user_id)
    )
    return result.scalar_one_or_none() is not None


async def _interview_owned_by(
    session: AsyncSession, interview_id: str, user_id: str
) -> bool:
    """True if the interview belongs to the given user."""
    result = await session.execute(
        select(Interview.interview_id).where(
            Interview.interview_id == interview_id,
            Interview.user_id == user_id,
        )
    )
    return result.scalar_one_or_none() is not None


# ============================================================
# Response Schemas
# ============================================================

class EvidenceSpanSchema:
    """Evidence span in response."""
    def __init__(self, start: int, end: int, text: str, quote_hash: str):
        self.start = start
        self.end = end
        self.text = text
        self.quote_hash = quote_hash

    def to_dict(self) -> dict:
        return {
            "start": self.start,
            "end": self.end,
            "text": self.text,
            "quote_hash": self.quote_hash,
        }


class VerificationPointResponse:
    """Verification point response schema."""
    def __init__(
        self,
        verification_point_id: str,
        claim_id: str,
        competency_code: str,
        aspect: str,
        current_state: str,
        strength: float | None,
        confidence: str | None,
        evidence_count: int,
        transition_count: int,
        has_contradictions: bool,
        created_at: str,
        updated_at: str,
    ):
        self.verification_point_id = verification_point_id
        self.claim_id = claim_id
        self.competency_code = competency_code
        self.aspect = aspect
        self.current_state = current_state
        self.strength = strength
        self.confidence = confidence
        self.evidence_count = evidence_count
        self.transition_count = transition_count
        self.has_contradictions = has_contradictions
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self) -> dict:
        return {
            "verification_point_id": self.verification_point_id,
            "claim_id": self.claim_id,
            "competency_code": self.competency_code,
            "aspect": self.aspect,
            "current_state": self.current_state,
            "strength": self.strength,
            "confidence": self.confidence,
            "evidence_count": self.evidence_count,
            "transition_count": self.transition_count,
            "has_contradictions": self.has_contradictions,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class TransitionResponse:
    """Evidence transition response schema."""
    def __init__(
        self,
        transition_id: str,
        verification_point_id: str,
        from_state: str,
        to_state: str,
        reason_code: str,
        answer_id: str | None,
        evidence_spans: list[dict] | None,
        policy_version: str,
        created_at: str,
    ):
        self.transition_id = transition_id
        self.verification_point_id = verification_point_id
        self.from_state = from_state
        self.to_state = to_state
        self.reason_code = reason_code
        self.answer_id = answer_id
        self.evidence_spans = evidence_spans
        self.policy_version = policy_version
        self.created_at = created_at

    def to_dict(self) -> dict:
        return {
            "transition_id": self.transition_id,
            "verification_point_id": self.verification_point_id,
            "from_state": self.from_state,
            "to_state": self.to_state,
            "reason_code": self.reason_code,
            "answer_id": self.answer_id,
            "evidence_spans": self.evidence_spans,
            "policy_version": self.policy_version,
            "created_at": self.created_at,
        }


class ContradictionResponse:
    """Contradiction response schema."""
    def __init__(
        self,
        contradiction_id: str,
        verification_point_id: str,
        claim_id: str,
        contradiction_type: str,
        severity: str,
        description: str,
        clarification_question: str | None,
        conflicting_answers: list[dict],
        resolution_status: str,
        created_at: str,
    ):
        self.contradiction_id = contradiction_id
        self.verification_point_id = verification_point_id
        self.claim_id = claim_id
        self.contradiction_type = contradiction_type
        self.severity = severity
        self.description = description
        self.clarification_question = clarification_question
        self.conflicting_answers = conflicting_answers
        self.resolution_status = resolution_status
        self.created_at = created_at

    def to_dict(self) -> dict:
        return {
            "contradiction_id": self.contradiction_id,
            "verification_point_id": self.verification_point_id,
            "claim_id": self.claim_id,
            "contradiction_type": self.contradiction_type,
            "severity": self.severity,
            "description": self.description,
            "clarification_question": self.clarification_question,
            "conflicting_answers": self.conflicting_answers,
            "resolution_status": self.resolution_status,
            "created_at": self.created_at,
        }


# ============================================================
# API Endpoints
# ============================================================

@router.get("/verification-points/{claim_id}")
async def get_verification_points_for_claim(
    claim_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)] = ...,
):
    """Get all verification points for a claim.

    Args:
        claim_id: Resume claim ID
        session: Database session

    Returns:
        List of verification points with evidence counts
    """
    if not await _claim_owned_by(session, claim_id, user.user_id):
        raise HTTPException(status_code=404, detail="Claim not found")
    evidence_repo = EvidenceRepository(session)

    # Get verification points
    vps = await evidence_repo.get_verification_points_for_claim(claim_id)

    if not vps:
        return {"verification_points": []}

    # Get evidence and transition counts for each VP
    result = []
    for vp in vps:
        # Get evidence count
        evidence_list = await evidence_repo.get_evidence_for_verification_point(
            vp.verification_point_id
        )
        evidence_count = len(evidence_list)

        # Get transition count
        transitions = await evidence_repo.get_transitions_for_verification_point(
            vp.verification_point_id
        )
        transition_count = len(transitions)

        # Check for contradictions
        contradictions = await evidence_repo.get_contradictions_for_verification_point(
            vp.verification_point_id
        )
        has_contradictions = len(contradictions) > 0

        # Build response
        vp_response = VerificationPointResponse(
            verification_point_id=vp.verification_point_id,
            claim_id=vp.claim_id,
            competency_code=vp.competency_code,
            aspect=vp.aspect,
            current_state=vp.current_state,
            strength=vp.strength,
            confidence=vp.confidence,
            evidence_count=evidence_count,
            transition_count=transition_count,
            has_contradictions=has_contradictions,
            created_at=vp.created_at.isoformat(),
            updated_at=vp.updated_at.isoformat(),
        )
        result.append(vp_response.to_dict())

    return {"verification_points": result}


@router.get("/transitions/{verification_point_id}")
async def get_transitions_for_verification_point(
    verification_point_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)] = ...,
):
    """Get transition history for a verification point.

    Args:
        verification_point_id: Verification point ID
        session: Database session

    Returns:
        List of transitions in chronological order
    """
    if not await _vp_owned_by(session, verification_point_id, user.user_id):
        raise HTTPException(status_code=404, detail="Verification point not found")
    evidence_repo = EvidenceRepository(session)

    # Get verification point
    vp = await evidence_repo.get_verification_point(verification_point_id)
    if not vp:
        raise HTTPException(status_code=404, detail="Verification point not found")

    # Get transitions
    transitions = await evidence_repo.get_transitions_for_verification_point(
        verification_point_id
    )

    result = []
    for transition in transitions:
        transition_response = TransitionResponse(
            transition_id=transition.transition_id,
            verification_point_id=transition.verification_point_id,
            from_state=transition.from_state,
            to_state=transition.to_state,
            reason_code=transition.reason_code,
            answer_id=transition.answer_id,
            evidence_spans=transition.evidence_spans,
            policy_version=transition.policy_version,
            created_at=transition.created_at.isoformat(),
        )
        result.append(transition_response.to_dict())

    return {
        "verification_point_id": verification_point_id,
        "current_state": vp.current_state,
        "transitions": result,
    }


@router.get("/contradictions/{interview_id}")
async def get_contradictions_for_interview(
    interview_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)] = ...,
    resolution_status: str | None = None,
):
    """Get contradictions for an interview.

    Args:
        interview_id: Interview ID
        resolution_status: Optional filter by resolution status (UNRESOLVED/CLARIFIED/CONFIRMED)
        session: Database session

    Returns:
        List of contradictions
    """
    if not await _interview_owned_by(session, interview_id, user.user_id):
        raise HTTPException(status_code=404, detail="Interview not found")
    evidence_repo = EvidenceRepository(session)

    # Get contradictions
    contradictions = await evidence_repo.get_contradictions_for_interview(interview_id)

    # Filter by resolution status if provided
    if resolution_status:
        contradictions = [
            c for c in contradictions
            if c.resolution_status == resolution_status
        ]

    result = []
    for contradiction in contradictions:
        contradiction_response = ContradictionResponse(
            contradiction_id=contradiction.contradiction_id,
            verification_point_id=contradiction.verification_point_id,
            claim_id=contradiction.claim_id,
            contradiction_type=contradiction.contradiction_type,
            severity=contradiction.severity,
            description=contradiction.description,
            clarification_question=contradiction.clarification_question,
            conflicting_answers=contradiction.conflicting_answers,
            resolution_status=contradiction.resolution_status,
            created_at=contradiction.created_at.isoformat(),
        )
        result.append(contradiction_response.to_dict())

    return {
        "interview_id": interview_id,
        "total_count": len(result),
        "contradictions": result,
    }


@router.get("/evidence/{verification_point_id}")
async def get_evidence_for_verification_point(
    verification_point_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)] = ...,
):
    """Get all evidence for a verification point.

    Args:
        verification_point_id: Verification point ID
        session: Database session

    Returns:
        List of evidence records with spans
    """
    if not await _vp_owned_by(session, verification_point_id, user.user_id):
        raise HTTPException(status_code=404, detail="Verification point not found")
    evidence_repo = EvidenceRepository(session)

    # Get verification point
    vp = await evidence_repo.get_verification_point(verification_point_id)
    if not vp:
        raise HTTPException(status_code=404, detail="Verification point not found")

    # Get evidence
    evidence_list = await evidence_repo.get_evidence_for_verification_point(
        verification_point_id
    )

    result = []
    for evidence in evidence_list:
        result.append({
            "evidence_id": evidence.evidence_id,
            "answer_id": evidence.answer_id,
            "evidence_type": evidence.evidence_type,
            "spans": evidence.spans,
            "summary": evidence.summary,
            "extracted_by": evidence.extracted_by,
            "confidence": evidence.confidence,
            "created_at": evidence.created_at.isoformat(),
        })

    return {
        "verification_point_id": verification_point_id,
        "aspect": vp.aspect,
        "current_state": vp.current_state,
        "evidence_count": len(result),
        "evidence": result,
    }

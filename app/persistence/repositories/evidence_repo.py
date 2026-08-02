"""Evidence repository for Phase 2 database operations."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.persistence.models import (
    VerificationPoint,
    Evidence,
    EvidenceTransition,
    Contradiction,
)


class EvidenceRepository:
    """Repository for evidence-related database operations.

    Does NOT commit transactions — the caller is responsible for session.commit().
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    # ============================================================
    # VerificationPoint operations
    # ============================================================

    async def add_verification_point(self, vp: VerificationPoint) -> None:
        """Add a new verification point."""
        self.session.add(vp)

    async def get_verification_point(
        self, verification_point_id: str
    ) -> VerificationPoint | None:
        """Get verification point by ID."""
        result = await self.session.execute(
            select(VerificationPoint).where(
                VerificationPoint.verification_point_id == verification_point_id
            )
        )
        return result.scalar_one_or_none()

    async def get_verification_points_for_claim(
        self, claim_id: str
    ) -> list[VerificationPoint]:
        """Get all verification points for a claim."""
        result = await self.session.execute(
            select(VerificationPoint)
            .where(VerificationPoint.claim_id == claim_id)
            .order_by(VerificationPoint.created_at)
        )
        return list(result.scalars().all())

    async def update_verification_point_state(
        self,
        verification_point_id: str,
        new_state: str,
        strength: float | None = None,
        confidence: str | None = None,
        unresolved_reason_codes: list | None = None,
    ) -> None:
        """Update verification point state."""
        vp = await self.get_verification_point(verification_point_id)
        if vp:
            vp.current_state = new_state
            if strength is not None:
                vp.strength = strength
            if confidence is not None:
                vp.confidence = confidence
            if unresolved_reason_codes is not None:
                vp.unresolved_reason_codes = unresolved_reason_codes

    # ============================================================
    # Evidence operations
    # ============================================================

    async def add_evidence(self, evidence: Evidence) -> None:
        """Add new evidence record."""
        self.session.add(evidence)

    async def get_evidence_for_verification_point(
        self, verification_point_id: str
    ) -> list[Evidence]:
        """Get all evidence for a verification point."""
        result = await self.session.execute(
            select(Evidence)
            .where(Evidence.verification_point_id == verification_point_id)
            .order_by(Evidence.created_at)
        )
        return list(result.scalars().all())

    async def get_evidence_for_answer(self, answer_id: str) -> list[Evidence]:
        """Get all evidence extracted from an answer."""
        result = await self.session.execute(
            select(Evidence)
            .where(Evidence.answer_id == answer_id)
            .order_by(Evidence.created_at)
        )
        return list(result.scalars().all())

    # ============================================================
    # EvidenceTransition operations
    # ============================================================

    async def add_transition(self, transition: EvidenceTransition) -> None:
        """Record a state transition."""
        self.session.add(transition)

    async def get_transitions_for_verification_point(
        self, verification_point_id: str
    ) -> list[EvidenceTransition]:
        """Get transition history for a verification point."""
        result = await self.session.execute(
            select(EvidenceTransition)
            .where(EvidenceTransition.verification_point_id == verification_point_id)
            .order_by(EvidenceTransition.created_at)
        )
        return list(result.scalars().all())

    # ============================================================
    # Contradiction operations
    # ============================================================

    async def add_contradiction(self, contradiction: Contradiction) -> None:
        """Record a detected contradiction."""
        self.session.add(contradiction)

    async def get_contradictions_for_verification_point(
        self, verification_point_id: str
    ) -> list[Contradiction]:
        """Get contradictions for a verification point."""
        result = await self.session.execute(
            select(Contradiction)
            .where(Contradiction.verification_point_id == verification_point_id)
            .order_by(Contradiction.created_at)
        )
        return list(result.scalars().all())

    async def get_contradictions_for_interview(
        self, interview_id: str
    ) -> list[Contradiction]:
        """Get all contradictions in an interview."""
        result = await self.session.execute(
            select(Contradiction)
            .where(Contradiction.interview_id == interview_id)
            .order_by(Contradiction.created_at)
        )
        return list(result.scalars().all())

    async def get_unresolved_contradictions_for_claim(
        self, claim_id: str
    ) -> list[Contradiction]:
        """Get unresolved contradictions for a claim."""
        result = await self.session.execute(
            select(Contradiction)
            .where(
                Contradiction.claim_id == claim_id,
                Contradiction.resolution_status == "UNRESOLVED",
            )
            .order_by(Contradiction.created_at)
        )
        return list(result.scalars().all())

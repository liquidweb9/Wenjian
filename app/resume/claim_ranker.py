"""Rank claims by priority using code-calculated scoring with LLM sub-scores."""

from app.resume.schemas import ResumeClaim
from app.llm.agnes_api import AgnesGateway


class ClaimRanker:
    """Rank claims by importance using a weighted formula."""

    def __init__(self, target_role: str = "", llm_gateway: AgnesGateway | None = None):
        self.target_role = target_role
        self.llm = llm_gateway or AgnesGateway()

    async def rank(self, claims: list[ResumeClaim]) -> list[ResumeClaim]:
        """Sort claims by calculated priority."""
        for claim in claims:
            claim.priority = self._calculate_priority(claim)
        claims.sort(key=lambda c: c.priority, reverse=True)
        return claims

    def _calculate_priority(self, claim: ResumeClaim) -> int:
        # 0.30 × role relevance + 0.20 × prominence + 0.20 × claimed level
        # + 0.15 × verification value + 0.15 × risk level
        role_relevance = self._score_role_relevance(claim)
        prominence = self._score_prominence(claim)
        level_score = self._score_level(claim)
        verification_value = self._score_verification_value(claim)
        risk = self._score_risk(claim)

        priority = (
            0.30 * role_relevance
            + 0.20 * prominence
            + 0.20 * level_score
            + 0.15 * verification_value
            + 0.15 * risk
        )

        return max(1, min(100, int(priority)))

    def _score_role_relevance(self, claim: ResumeClaim) -> float:
        if not self.target_role:
            return 50
        keywords = self.target_role.lower().split()
        techs = " ".join(claim.technologies).lower()
        text = claim.claim_text.lower()
        matches = sum(1 for k in keywords if k in text or k in techs)
        return min(100, matches * 20) if matches else 30

    def _score_prominence(self, claim: ResumeClaim) -> float:
        keywords = ["lead", "design", "architect", "responsible", "核心", "主导", "负责"]
        text = claim.claim_text.lower()
        matches = sum(1 for kw in keywords if kw in text)
        return min(100, matches * 20)

    def _score_level(self, claim: ResumeClaim) -> float:
        level_scores = {"know": 20, "use": 40, "implement": 60, "design": 80, "production": 100}
        return level_scores.get(claim.expected_level, 40)

    def _score_verification_value(self, claim: ResumeClaim) -> float:
        return min(100, len(claim.verification_points) * 15)

    def _score_risk(self, claim: ResumeClaim) -> float:
        risk_scores = {
            "UNVERIFIED_IMPROVEMENT": 80,
            "MISSING_METRICS": 70,
            "UNCLEAR_OWNERSHIP": 60,
            "TECH_STACK_DENSITY": 50,
        }
        if not claim.risk_flags:
            return 20
        return max(risk_scores.get(flag, 30) for flag in claim.risk_flags)

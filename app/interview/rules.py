"""Decision rule engine - code-controlled routing logic."""

from app.interview.state import InterviewState
from app.core.enums import ClaimStatusEnum


def has_contradiction(state: InterviewState) -> bool:
    """Check if there are unresolved contradictions."""
    contradictions = state.get("contradictions", [])
    return any(not c.get("resolved", False) for c in contradictions)


def get_latest_evaluation(state: InterviewState) -> dict | None:
    evaluations = state.get("evaluations", [])
    return evaluations[-1] if evaluations else None


def get_latest_analysis(state: InterviewState) -> dict | None:
    analyses = state.get("analyses", [])
    return analyses[-1] if analyses else None


def current_claim_is_verified(state: InterviewState) -> bool:
    claim_id = state.get("current_claim_id")
    if not claim_id:
        return False
    status = state.get("claim_statuses", {}).get(claim_id, {}).get("status", "")
    return status in (
        ClaimStatusEnum.VERIFIED.value,
        ClaimStatusEnum.UNSUPPORTED.value,
        ClaimStatusEnum.SKIPPED.value,
    )


def all_high_priority_covered(state: InterviewState) -> bool:
    """Check if all high-priority claims are covered."""
    for claim in state.get("resume_claims", []):
        if claim.get("priority", 0) >= 70:
            cs = state.get("claim_statuses", {}).get(claim.get("claim_id", ""), {})
            if cs.get("status") == ClaimStatusEnum.UNTOUCHED.value:
                return False
    return True


def questions_for_current_claim(state: InterviewState) -> int:
    claim_id = state.get("current_claim_id")
    if not claim_id:
        return 0
    return sum(
        1 for q in state.get("questions", [])
        if q.get("claim_id") == claim_id
    )


class Decision:
    def __init__(self, action: str, reason: str = "", target: str = "", depth: int = 1):
        self.action = action
        self.reason = reason
        self.target = target
        self.depth = depth

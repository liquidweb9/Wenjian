"""Select current topic, claim, and verification point."""

from app.core.enums import ClaimStatusEnum, NextAction
from app.interview.state import InterviewState
from app.observability.logging import logger


async def select_target_node(state: InterviewState) -> dict:
    """Select what to focus on next based on evidence state."""
    claim_statuses = state.get("claim_statuses", {})
    contradictions = state.get("contradictions", [])
    plan = state.get("interview_plan", {})

    # 1. Check for contradictions (highest priority)
    active_contradictions = [c for c in contradictions if not c.get("resolved", False)]
    if active_contradictions:
        logger.info("target_contradiction", count=len(active_contradictions))
        # Find the claim involved in the contradiction
        contra = active_contradictions[0]
        return {
            "current_claim_id": contra.get("claim_id"),
            "current_verification_point_id": contra.get("verification_point_id"),
            "current_depth": state.get("current_depth", 1),
            "next_action": NextAction.FOLLOW_UP.value,
        }

    # 2. Find next unverified claim with highest priority
    highest_priority = -1
    best_claim_id = None
    best_topic_id = None
    topics = plan.get("topics", [])

    for topic in topics:
        for claim_id in topic.get("related_claim_ids", []):
            status_info = claim_statuses.get(claim_id, {})
            status = status_info.get("status", ClaimStatusEnum.UNTOUCHED.value)

            if status in (ClaimStatusEnum.VERIFIED.value, ClaimStatusEnum.SKIPPED.value, ClaimStatusEnum.UNSUPPORTED.value):
                continue

            # Find claim priority from resume_claims
            for rc in state.get("resume_claims", []):
                if rc.get("claim_id") == claim_id:
                    priority = rc.get("priority", 50)
                    if priority > highest_priority:
                        highest_priority = priority
                        best_claim_id = claim_id
                        best_topic_id = topic.get("topic_id")
                    break

    if best_claim_id is None:
        # All claims covered
        logger.info("all_claims_covered")
        return {
            "next_action": NextAction.FINISH.value,
            "stop_reason": "ALL_CLAIMS_COVERED",
        }

    # Get verification points for this claim
    claim_obj = None
    for rc in state.get("resume_claims", []):
        if rc.get("claim_id") == best_claim_id:
            claim_obj = rc
            break

    vpoints = claim_obj.get("verification_points", []) if claim_obj else []
    status_info = claim_statuses.get(best_claim_id, {})
    verified = set(status_info.get("verified_points", []))

    # Find next unverified verification point
    next_vp = None
    for vp in vpoints:
        if vp.get("point_id") not in verified:
            next_vp = vp
            break

    depth = next_vp.get("target_depth", 1) if next_vp else 1

    logger.info("target_selected", claim_id=best_claim_id, vp=next_vp.get("point_id") if next_vp else None)

    return {
        "current_claim_id": best_claim_id,
        "current_topic_id": best_topic_id,
        "current_verification_point_id": next_vp.get("point_id") if next_vp else None,
        "current_depth": depth,
        "next_action": NextAction.FOLLOW_UP.value,
    }

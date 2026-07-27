"""Initialize interview state - no LLM call."""

from app.interview.state import InterviewState
from app.core.ids import new_interview_id, new_thread_id
from app.observability.logging import logger
from app.core.enums import ClaimStatusEnum


async def initialize_node(state: InterviewState) -> dict:
    """Initialize the interview state.

    If interview_id/thread_id are already set (by the API), preserve them
    so the graph config thread_id matches the business thread_id.
    Otherwise generate new IDs (for direct graph invocation in tests).
    """
    interview_id = state.get("interview_id") or new_interview_id()
    thread_id = state.get("thread_id") or new_thread_id()

    # Initialize claim statuses
    claim_statuses = {}
    for claim in state.get("resume_claims", []):
        cid = claim.get("claim_id", "")
        claim_statuses[cid] = {
            "claim_id": cid,
            "status": ClaimStatusEnum.UNTOUCHED.value,
            "verified_points": [],
            "partial_points": [],
            "missing_points": [],
            "supporting_evidence_ids": [],
            "contradiction_ids": [],
            "confidence": 0.0,
        }

    # Initialize coverage tracking
    coverage = {}
    for topic in state.get("interview_plan", {}).get("topics", []):
        coverage[topic.get("topic_id", "")] = 0.0

    logger.info("interview_initialized", interview_id=interview_id, thread_id=thread_id)

    return {
        "interview_id": interview_id,
        "thread_id": thread_id,
        "turn_count": 0,
        "current_depth": 1,
        "questions": [],
        "answers": [],
        "analyses": [],
        "evaluations": [],
        "claim_statuses": claim_statuses,
        "contradictions": [],
        "evidence_items": [],
        "coverage": coverage,
        "ability_profile": {
            "technical_correctness": 0,
            "implementation_depth": 0,
            "architecture_tradeoffs": 0,
            "personal_contribution": 0,
            "production_awareness": 0,
            "clarity": 0,
        },
        "next_action": None,
        "stop_reason": None,
        "finished": False,
        "current_topic_id": None,
        "current_claim_id": None,
        "current_verification_point_id": None,
        "current_question": None,
        "latest_coaching": None,
        "final_report": None,
    }

"""Update evidence ledger and claim statuses based on latest evaluation."""

from app.interview.state import InterviewState
from app.core.enums import ClaimStatusEnum
from app.core.ids import new_id
from app.observability.logging import logger
from app.interview.schemas import EvidenceItem


def _count_vpoints(state: InterviewState, claim_id: str) -> int:
    """Count total verification points for a claim."""
    for rc in state.get("resume_claims", []):
        if rc.get("claim_id") == claim_id:
            return len(rc.get("verification_points", []))
    return 1


async def update_evidence_node(state: InterviewState) -> dict:
    """Update claim statuses and evidence based on latest analysis/evaluation."""
    claim_statuses = dict(state.get("claim_statuses", {}))
    evaluations = state.get("evaluations", [])
    analyses = state.get("analyses", [])
    answers = state.get("answers", [])
    questions = state.get("questions", [])
    evidence_items = list(state.get("evidence_items", []))
    current_claim_id = state.get("current_claim_id")

    if not evaluations or not current_claim_id:
        return {}

    latest_eval = evaluations[-1]
    latest_analysis = analyses[-1] if analyses else {}
    latest_answer = answers[-1] if answers else {}
    latest_question = questions[-1] if questions else {}
    current_vp_id = state.get("current_verification_point_id")

    # Create evidence item from the latest answer
    if latest_answer and latest_analysis:
        evidence = EvidenceItem(
            evidence_id=new_id("ev"),
            claim_id=current_claim_id,
            verification_point_id=current_vp_id,
            question_id=latest_question.get("question_id", ""),
            answer_id=latest_answer.get("answer_id", ""),
            evidence_text=latest_answer.get("answer_text", "")[:500],
            evidence_type="technical",
            strength=latest_eval.get("evaluation_confidence", 0.5) if latest_eval else 0.5,
            confidence=latest_eval.get("evaluation_confidence", 0.5) if latest_eval else 0.5,
        )
        evidence_items.append(evidence.model_dump(mode="json"))

    # Update claim status
    if current_claim_id in claim_statuses:
        status = claim_statuses[current_claim_id]

        if current_vp_id:
            missing = latest_analysis.get("missing_expected_points", [])
            addressed = latest_analysis.get("addressed_expected_points", [])

            if not missing and addressed:
                if current_vp_id not in status["verified_points"]:
                    status["verified_points"].append(current_vp_id)
            elif addressed:
                if current_vp_id not in status["partial_points"]:
                    status["partial_points"].append(current_vp_id)
            else:
                if current_vp_id not in status["missing_points"]:
                    status["missing_points"].append(current_vp_id)

        # Update overall status
        verified_count = len(status["verified_points"])
        total_vpoints = _count_vpoints(state, current_claim_id)
        contradictions = latest_analysis.get("possible_contradictions", [])

        if contradictions:
            status["status"] = ClaimStatusEnum.CONTRADICTORY.value
        elif verified_count >= total_vpoints and total_vpoints > 0:
            status["status"] = ClaimStatusEnum.VERIFIED.value
        elif verified_count > 0:
            status["status"] = ClaimStatusEnum.PARTIALLY_VERIFIED.value
        else:
            status["status"] = ClaimStatusEnum.IN_PROGRESS.value

        status["confidence"] = max(0.1, min(1.0, verified_count / max(total_vpoints, 1)))
        claim_statuses[current_claim_id] = status

    # Update coverage
    coverage = dict(state.get("coverage", {}))
    plan = state.get("interview_plan", {})
    for topic in plan.get("topics", []):
        related = topic.get("related_claim_ids", [])
        if current_claim_id in related:
            tid = topic.get("topic_id", "")
            covered = sum(
                1 for cid in related
                if claim_statuses.get(cid, {}).get("status") in (
                    ClaimStatusEnum.VERIFIED.value,
                    ClaimStatusEnum.PARTIALLY_VERIFIED.value,
                )
            )
            coverage[tid] = covered / max(len(related), 1)

    logger.info("evidence_updated",
                claim_id=current_claim_id,
                status=claim_statuses.get(current_claim_id, {}).get("status"),
                evidence_count=len(evidence_items))

    return {
        "claim_statuses": claim_statuses,
        "coverage": coverage,
        "evidence_items": evidence_items,
    }

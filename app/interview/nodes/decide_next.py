"""Decide next action using rule engine (code decides, LLM only suggests)."""

from app.interview.state import InterviewState
from app.interview.rules import (
    Decision, has_contradiction, get_latest_evaluation,
    get_latest_analysis, questions_for_current_claim,
)
from app.core.enums import NextAction, ClaimStatusEnum
from app.observability.logging import logger


async def decide_next_node(state: InterviewState) -> dict:
    """Determine next action based on rules and evidence."""
    # 0. Respect external FINISH command (e.g., user clicked "结束面试")
    next_action = state.get("next_action")
    if next_action == NextAction.FINISH.value:
        logger.info("decide_external_finish", reason=state.get("stop_reason"))
        return _apply_decision(Decision(action=NextAction.FINISH.value, reason=state.get("stop_reason", "EXTERNAL")))

    turn_count = state.get("turn_count", 0)
    max_turns = state.get("max_turns", 15)

    # 1. Max turns reached
    if turn_count >= max_turns:
        decision = Decision(action=NextAction.FINISH.value, reason="MAX_TURNS")
        logger.info("decide_max_turns")
        return _apply_decision(decision)

    # 2. High-priority contradiction
    if has_contradiction(state):
        decision = Decision(action=NextAction.FOLLOW_UP.value, reason="CONTRADICTION")
        logger.info("decide_contradiction")
        return _apply_decision(decision)

    # 3. Check latest evaluation
    latest_eval = get_latest_evaluation(state)
    latest_analysis = get_latest_analysis(state)

    if latest_eval:
        # Low relevance → clarify
        if latest_analysis and latest_analysis.get("answer_relevance", 1.0) < 0.35:
            decision = Decision(
                action=NextAction.CLARIFY.value,
                reason="LOW_RELEVANCE",
                depth=max(1, state.get("current_depth", 1) - 1),
            )
            return _apply_decision(decision)

        # Implementation missing → follow up at same depth
        has_low_impl = any(
            d.get("score", 100) < 60
            for d in latest_eval.get("dimensions", [])
            if d.get("dimension") == "implementation_depth"
        )
        if has_low_impl and state.get("current_depth", 1) <= 3:
            decision = Decision(
                action=NextAction.FOLLOW_UP.value,
                reason="LOW_IMPLEMENTATION",
                depth=state.get("current_depth", 1),
            )
            return _apply_decision(decision)

        # High score → increase difficulty
        total_score = _calculate_total_score(latest_eval)
        if total_score >= 80 and state.get("current_depth", 1) < 7:
            decision = Decision(
                action=NextAction.INCREASE_DIFFICULTY.value,
                reason="HIGH_SCORE",
                depth=state.get("current_depth", 1) + 1,
            )
            return _apply_decision(decision)

    # 4. Check if current claim is done
    claim_id = state.get("current_claim_id")
    if claim_id:
        claim_status = state.get("claim_statuses", {}).get(claim_id, {})
        status = claim_status.get("status", ClaimStatusEnum.UNTOUCHED.value)
        if status in (
            ClaimStatusEnum.VERIFIED.value,
            ClaimStatusEnum.UNSUPPORTED.value,
            ClaimStatusEnum.CONTRADICTORY.value,
        ):
            decision = Decision(action=NextAction.SWITCH_CLAIM.value, reason="CLAIM_DONE")
            return _apply_decision(decision)

        # Check question limit for current claim
        plan = state.get("interview_plan", {})
        for topic in plan.get("topics", []):
            if claim_id in topic.get("related_claim_ids", []):
                max_questions = topic.get("max_questions", 5)
                if questions_for_current_claim(state) >= max_questions:
                    decision = Decision(action=NextAction.SWITCH_CLAIM.value, reason="QUESTION_LIMIT")
                    return _apply_decision(decision)

    # 5. Default: follow up
    decision = Decision(
        action=NextAction.FOLLOW_UP.value,
        reason="CONTINUE_DEEPENING",
        depth=min(7, state.get("current_depth", 1) + 1),
    )
    return _apply_decision(decision)


def _apply_decision(decision: Decision) -> dict:
    """Convert a Decision into the state update dict."""
    return {
        "next_action": decision.action,
        "stop_reason": decision.reason,
        "current_depth": decision.depth,
    }


def _calculate_total_score(evaluation: dict) -> float:
    from app.interview.rubrics import calculate_weighted_score
    return calculate_weighted_score(evaluation)

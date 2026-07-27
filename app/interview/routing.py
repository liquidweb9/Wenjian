"""LangGraph routing functions - determine next node based on state."""

from app.interview.state import InterviewState
from app.core.enums import NextAction


def route_after_select(state: InterviewState) -> str:
    """After target selected, generate question if there's a target."""
    action = state.get("next_action")
    if action == NextAction.FINISH.value:
        return "generate_report"
    return "generate_question"


def route_after_decide(state: InterviewState) -> str:
    """Route based on decide_next output."""
    action = state.get("next_action")

    route_map = {
        NextAction.FOLLOW_UP.value: "generate_question",
        NextAction.CLARIFY.value: "generate_question",
        NextAction.INCREASE_DIFFICULTY.value: "generate_question",
        NextAction.SWITCH_CLAIM.value: "select_target",
        NextAction.SWITCH_TOPIC.value: "select_target",
        NextAction.FINISH.value: "generate_report",
    }

    return route_map.get(action, "generate_report")

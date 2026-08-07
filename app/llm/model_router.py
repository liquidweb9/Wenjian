"""Route LLM tasks to appropriate model tiers."""

from typing import Literal

ModelTier = Literal["fast", "balanced", "judge"]

# Task-to-tier mapping
TASK_TIER: dict[str, ModelTier] = {
    # Fast tasks
    "section_classification": "fast",
    "low_risk_fix": "fast",
    # Balanced tasks
    "profile_builder": "balanced",
    "claim_extractor": "balanced",
    "interview_planner": "balanced",
    "question_generation": "balanced",
    "answer_analysis": "balanced",
    # Judge tasks
    "answer_scoring": "judge",
    "contradiction_judge": "judge",
    "report_generation": "judge",
    "coaching": "judge",
}


def get_tier(task_name: str) -> ModelTier:
    return TASK_TIER.get(task_name, "balanced")


def resolve_tier(task_name: str, interview_tier: str | None = None) -> ModelTier:
    """Resolve the effective tier for a call.

    A per-interview tier (selected by the user, stored in graph state) takes
    precedence over the platform's per-task routing. ``None``/unknown values
    fall back to the task-based mapping, so existing behavior is preserved when
    no tier is selected.
    """
    if interview_tier in ("fast", "balanced", "judge"):
        return interview_tier
    return get_tier(task_name)

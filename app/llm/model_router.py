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

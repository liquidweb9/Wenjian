"""Interview state definition for LangGraph."""

from typing import TypedDict, Any


class InterviewState(TypedDict):
    # Identifiers
    interview_id: str
    thread_id: str
    resume_id: str
    resume_revision_id: str

    # Configuration
    target_role: str
    job_description: str | None
    interview_mode: str

    # Resume data
    resume_profile: dict
    resume_claims: list[dict]
    interview_plan: dict

    # Current targeting
    current_topic_id: str | None
    current_claim_id: str | None
    current_verification_point_id: str | None
    current_depth: int
    current_question: dict | None

    # History
    questions: list[dict]
    answers: list[dict]
    analyses: list[dict]
    evaluations: list[dict]

    # Evidence tracking
    claim_statuses: dict[str, Any]
    contradictions: list[dict]
    evidence_items: list[dict]
    coverage: dict[str, float]
    ability_profile: dict[str, float]

    # Flow control
    turn_count: int
    max_turns: int
    next_action: str | None
    stop_reason: str | None
    finished: bool

    # Outputs
    latest_coaching: dict | None
    final_report: dict | None

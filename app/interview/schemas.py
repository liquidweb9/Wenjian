"""Data models for the interview workflow."""

from pydantic import BaseModel, Field


class InterviewQuestion(BaseModel):
    question_id: str
    question_text: str
    topic_id: str
    claim_id: str | None = None
    verification_point_id: str | None = None
    question_type: str = "technical"
    depth: int = 1
    difficulty: int = 1
    expected_points: list[str] = Field(default_factory=list)
    strong_signals: list[str] = Field(default_factory=list)
    weak_signals: list[str] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
    follow_up_candidates: list[str] = Field(default_factory=list)


class AnswerAnalysis(BaseModel):
    answer_summary: str
    claims_made: list[str] = Field(default_factory=list)
    technical_points: list[str] = Field(default_factory=list)
    personal_contribution_evidence: list[str] = Field(default_factory=list)
    addressed_expected_points: list[str] = Field(default_factory=list)
    partially_addressed_points: list[str] = Field(default_factory=list)
    missing_expected_points: list[str] = Field(default_factory=list)
    vague_statements: list[str] = Field(default_factory=list)
    possible_errors: list[str] = Field(default_factory=list)
    possible_contradictions: list[str] = Field(default_factory=list)
    unsupported_metrics: list[str] = Field(default_factory=list)
    answer_relevance: float = 1.0
    information_density: float = 0.5
    follow_up_value: float = 0.5
    recommended_follow_up_target: str | None = None


class DimensionScore(BaseModel):
    dimension: str
    score: int
    max_score: int = 100
    reason: str = ""
    answer_evidence: list[str] = Field(default_factory=list)
    missing_points: list[str] = Field(default_factory=list)
    confidence: float = 1.0


class AnswerEvaluation(BaseModel):
    dimensions: list[DimensionScore] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    factual_errors: list[str] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    key_missing_points: list[str] = Field(default_factory=list)
    demonstrated_level: str = "unknown"
    evaluation_confidence: float = 1.0
    model_recommended_action: str = "follow_up"
    model_recommended_depth: int = 1


class EvidenceItem(BaseModel):
    evidence_id: str
    claim_id: str
    verification_point_id: str | None = None
    question_id: str
    answer_id: str
    evidence_text: str
    evidence_type: str = "general"
    strength: float = 0.5
    confidence: float = 1.0


class ClaimStatus(BaseModel):
    claim_id: str
    status: str = "UNTOUCHED"
    verified_points: list[str] = Field(default_factory=list)
    partial_points: list[str] = Field(default_factory=list)
    missing_points: list[str] = Field(default_factory=list)
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    contradiction_ids: list[str] = Field(default_factory=list)
    confidence: float = 0.0


class AnswerCoaching(BaseModel):
    score_summary: str = ""
    question_analysis: str = ""
    what_was_good: list[str] = Field(default_factory=list)
    what_to_improve: list[str] = Field(default_factory=list)
    concise_answer: str = ""
    complete_answer: str = ""
    expert_answer: str = ""
    answer_framework: list[str] = Field(default_factory=list)
    likely_follow_up_questions: list[str] = Field(default_factory=list)
    knowledge_gaps: list[str] = Field(default_factory=list)
    confirmed_candidate_facts: list[str] = Field(default_factory=list)
    requires_candidate_confirmation: list[str] = Field(default_factory=list)
    generic_technical_content: list[str] = Field(default_factory=list)

import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import (
    BlockType,
    ExtractionMethod,
    ResumeStatus,
    SourceType,
)
from app.persistence.database import Base

# ============================================================
# Phase 2 M2.6: User Authentication
# ============================================================

class User(Base):
    """User accounts for authentication and data ownership."""
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    last_login_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)


# ============================================================
# Phase 1: Resume Processing
# ============================================================

class ResumeSource(Base):
    __tablename__ = "resume_sources"

    resume_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.user_id"), index=True)
    source_id: Mapped[str] = mapped_column(String(64))
    file_name: Mapped[str] = mapped_column(String(256))
    source_type: Mapped[SourceType] = mapped_column(SAEnum(SourceType))
    sha256: Mapped[str | None] = mapped_column(String(64))
    file_size: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    revisions: Mapped[list["ResumeRevision"]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )


class ResumeRevision(Base):
    __tablename__ = "resume_revisions"

    revision_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    resume_id: Mapped[str] = mapped_column(String(64), ForeignKey("resume_sources.resume_id"))
    status: Mapped[ResumeStatus] = mapped_column(SAEnum(ResumeStatus), default=ResumeStatus.UPLOADED)

    raw_text: Mapped[str | None] = mapped_column(Text)
    normalized_text: Mapped[str | None] = mapped_column(Text)
    extraction_method: Mapped[ExtractionMethod | None] = mapped_column(SAEnum(ExtractionMethod))
    extraction_quality: Mapped[float | None] = mapped_column(Float)
    extraction_warnings: Mapped[list | None] = mapped_column(JSON)
    parser_name: Mapped[str | None] = mapped_column(String(64))
    parser_version: Mapped[str | None] = mapped_column(String(32))

    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    source: Mapped["ResumeSource"] = relationship(back_populates="revisions")
    blocks: Mapped[list["ResumeBlock"]] = relationship(back_populates="revision")


class ResumeBlock(Base):
    __tablename__ = "resume_blocks"

    block_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    revision_id: Mapped[str] = mapped_column(String(64), ForeignKey("resume_revisions.revision_id"))
    text: Mapped[str] = mapped_column(Text)
    raw_text: Mapped[str | None] = mapped_column(Text)
    block_type: Mapped[BlockType] = mapped_column(SAEnum(BlockType), default=BlockType.UNKNOWN)
    source_location: Mapped[dict | None] = mapped_column(JSON)
    style_hints: Mapped[dict] = mapped_column(JSON, default=dict)
    warnings: Mapped[list] = mapped_column(JSON, default=list)
    block_index: Mapped[int] = mapped_column(Integer, default=0)

    revision: Mapped["ResumeRevision"] = relationship(back_populates="blocks")


class ResumeProfile(Base):
    __tablename__ = "resume_profiles"

    profile_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    resume_id: Mapped[str] = mapped_column(String(64), ForeignKey("resume_sources.resume_id"))
    revision_id: Mapped[str] = mapped_column(String(64), ForeignKey("resume_revisions.revision_id"))
    data: Mapped[dict] = mapped_column(JSON)
    confidence: Mapped[float] = mapped_column(Float)
    warnings: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)


class ResumeClaim(Base):
    __tablename__ = "resume_claims"

    claim_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    resume_id: Mapped[str] = mapped_column(String(64), ForeignKey("resume_sources.resume_id"))
    data: Mapped[dict] = mapped_column(JSON)
    priority: Mapped[int] = mapped_column(Integer, default=50)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    disabled: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)


class Interview(Base):
    __tablename__ = "interviews"

    interview_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.user_id"), index=True)
    thread_id: Mapped[str] = mapped_column(String(64), unique=True)
    resume_id: Mapped[str] = mapped_column(String(64), ForeignKey("resume_sources.resume_id"))
    job_target_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("job_targets.job_target_id", ondelete="SET NULL"),
        nullable=True,
    )
    target_role: Mapped[str] = mapped_column(String(256))
    job_description: Mapped[str | None] = mapped_column(Text)
    mode: Mapped[str] = mapped_column(String(32), default="simulation")
    max_turns: Mapped[int] = mapped_column(Integer, default=15)
    status: Mapped[str] = mapped_column(String(32), default="created")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    finished_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)

    questions: Mapped[list["InterviewQuestion"]] = relationship(
        back_populates="interview", cascade="all, delete-orphan"
    )
    answers: Mapped[list["InterviewAnswer"]] = relationship(
        back_populates="interview", cascade="all, delete-orphan"
    )


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    question_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    interview_id: Mapped[str] = mapped_column(String(64), ForeignKey("interviews.interview_id"))
    data: Mapped[dict] = mapped_column(JSON)  # Full question object from graph state
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    interview: Mapped["Interview"] = relationship(back_populates="questions")


class InterviewAnswer(Base):
    __tablename__ = "interview_answers"

    answer_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    interview_id: Mapped[str] = mapped_column(String(64), ForeignKey("interviews.interview_id"))
    question_id: Mapped[str] = mapped_column(String(64), ForeignKey("interview_questions.question_id"))
    answer_text: Mapped[str] = mapped_column(Text)
    analysis: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    evaluation: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    interview: Mapped["Interview"] = relationship(back_populates="answers")


class InterviewReport(Base):
    __tablename__ = "interview_reports"

    report_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    interview_id: Mapped[str] = mapped_column(String(64), ForeignKey("interviews.interview_id"))
    data: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)


class LLMCall(Base):
    __tablename__ = "llm_calls"

    call_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    interview_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("interviews.interview_id"))
    task_name: Mapped[str] = mapped_column(String(64))
    model: Mapped[str] = mapped_column(String(64))
    prompt_version: Mapped[str | None] = mapped_column(String(32))
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32))
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)


class PromptVersion(Base):
    """Phase 2 M2.3: Versioned prompts for regression testing."""
    __tablename__ = "prompt_versions"

    prompt_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    task_name: Mapped[str] = mapped_column(String(128), index=True)
    version: Mapped[int] = mapped_column(Integer)
    system_prompt: Mapped[str] = mapped_column(Text)
    input_schema: Mapped[dict | None] = mapped_column(JSON)
    output_model: Mapped[str | None] = mapped_column(String(128))
    rules: Mapped[str | None] = mapped_column(Text)
    examples: Mapped[list | None] = mapped_column(JSON)
    forbid_list: Mapped[list | None] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)


# ============================================================
# Phase 2 M2.1: Job Target & Claim Gap
# ============================================================

class Competency(Base):
    """Competency catalog with level descriptors."""
    __tablename__ = "competencies"

    competency_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    code: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(64))  # backend, agent, devops, etc
    title: Mapped[str] = mapped_column(String(256))
    description: Mapped[str] = mapped_column(Text)
    level_descriptors: Mapped[dict] = mapped_column(JSON)  # L1-L5 behavioral descriptions
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)


class JobTarget(Base):
    """Job target definition - can be template or user-created."""
    __tablename__ = "job_targets"

    job_target_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("users.user_id"), index=True)
    title: Mapped[str] = mapped_column(String(256))
    company_name: Mapped[str | None] = mapped_column(String(256))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    level: Mapped[str] = mapped_column(String(32))  # intern, junior, mid, senior, staff, custom
    interview_round: Mapped[str] = mapped_column(String(32))  # resume, project, technical, system_design, hr, custom
    source: Mapped[str] = mapped_column(String(32))  # template, pasted_jd, manual
    raw_jd: Mapped[str | None] = mapped_column(Text)
    parser_prompt_version: Mapped[str | None] = mapped_column(String(32))
    is_template: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    requirements: Mapped[list["JobRequirement"]] = relationship(
        back_populates="job_target", cascade="all, delete-orphan"
    )


class JobRequirement(Base):
    """Structured requirements extracted from JD or template."""
    __tablename__ = "job_requirements"

    requirement_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    job_target_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("job_targets.job_target_id", ondelete="CASCADE"),
    )

    job_target: Mapped["JobTarget"] = relationship(back_populates="requirements")
    competency_code: Mapped[str] = mapped_column(String(128))  # Links to Competency.code
    title: Mapped[str] = mapped_column(String(256))
    description: Mapped[str] = mapped_column(Text)
    importance: Mapped[float] = mapped_column(Float)  # 0.0-1.0
    expected_level: Mapped[int] = mapped_column(Integer)  # 1-5
    evidence_expectation: Mapped[list] = mapped_column(JSON)  # List of expected evidence points
    source_span: Mapped[dict | None] = mapped_column(JSON)  # Link back to JD text
    is_user_confirmed: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)


class ClaimCompetencyMapping(Base):
    """Maps resume claims to competencies."""
    __tablename__ = "claim_competency_mappings"

    mapping_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    claim_id: Mapped[str] = mapped_column(String(64), ForeignKey("resume_claims.claim_id"))
    competency_code: Mapped[str] = mapped_column(String(128))
    mapping_strength: Mapped[float] = mapped_column(Float)  # 0.0-1.0
    mapping_reason: Mapped[str] = mapped_column(Text)
    mapping_source: Mapped[str] = mapped_column(String(32))  # rule, llm, user
    prompt_version: Mapped[str | None] = mapped_column(String(32))
    user_confirmed: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)


class ClaimRequirementMapping(Base):
    """Maps claims to job requirements for gap analysis."""
    __tablename__ = "claim_requirement_mappings"

    mapping_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    claim_id: Mapped[str] = mapped_column(String(64), ForeignKey("resume_claims.claim_id"))
    requirement_id: Mapped[str] = mapped_column(String(64), ForeignKey("job_requirements.requirement_id"))
    relevance: Mapped[float] = mapped_column(Float)  # 0.0-1.0
    evidence_strength: Mapped[float] = mapped_column(Float)  # 0.0-1.0
    verification_priority: Mapped[float] = mapped_column(Float)  # Computed priority score
    reason_codes: Mapped[list] = mapped_column(JSON)  # e.g., ["HIGH_JOB_IMPORTANCE", "WEAK_EXISTING_EVIDENCE"]
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)


# ============================================================
# Phase 2 M2.2: Evidence Engine 2.0
# ============================================================

class VerificationPoint(Base):
    """Verification points for tracking claim evidence."""
    __tablename__ = "verification_points"

    verification_point_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    claim_id: Mapped[str] = mapped_column(String(64), ForeignKey("resume_claims.claim_id"), index=True)
    competency_code: Mapped[str] = mapped_column(String(128))
    requirement_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("job_requirements.requirement_id"))
    aspect: Mapped[str] = mapped_column(Text)  # What specific aspect is being verified
    expected_evidence: Mapped[dict] = mapped_column(JSON)  # Expected evidence types and criteria
    current_state: Mapped[str] = mapped_column(String(50), default="UNSEEN", index=True)  # EvidenceState enum
    strength: Mapped[float | None] = mapped_column(Float)  # 0.0-1.0
    confidence: Mapped[str | None] = mapped_column(String(20))  # LOW/MEDIUM/HIGH
    unresolved_reason_codes: Mapped[list | None] = mapped_column(JSON)  # Reasons if not VERIFIED
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class Evidence(Base):
    """Evidence records linking to specific answer spans."""
    __tablename__ = "evidence"

    evidence_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    verification_point_id: Mapped[str] = mapped_column(String(64), ForeignKey("verification_points.verification_point_id"), index=True)
    interview_id: Mapped[str] = mapped_column(String(64), ForeignKey("interviews.interview_id"))
    answer_id: Mapped[str] = mapped_column(String(64), ForeignKey("interview_answers.answer_id"), index=True)
    evidence_type: Mapped[str] = mapped_column(String(50))  # DIRECT/INDIRECT/CONTEXTUAL
    spans: Mapped[list | None] = mapped_column(JSON, nullable=True)  # [{start, end, text, quote_hash}]
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_by: Mapped[str | None] = mapped_column(String(50), nullable=True)  # MODEL/ANALYST
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0.0-1.0
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)


class EvidenceTransition(Base):
    """Audit trail for evidence state machine transitions."""
    __tablename__ = "evidence_transitions"

    transition_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    verification_point_id: Mapped[str] = mapped_column(String(64), ForeignKey("verification_points.verification_point_id"), index=True)
    from_state: Mapped[str] = mapped_column(String(50))
    to_state: Mapped[str] = mapped_column(String(50))
    reason_code: Mapped[str | None] = mapped_column(String(50))  # FIRST_INQUIRY, EVIDENCE_SPANS_FOUND, etc
    interview_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("interviews.interview_id"))
    answer_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("interview_answers.answer_id"))
    evidence_spans: Mapped[list | None] = mapped_column(JSON, nullable=True)  # Snapshot of extracted spans
    policy_version: Mapped[str | None] = mapped_column(String(32))
    prompt_version: Mapped[str | None] = mapped_column(String(32))
    model_name: Mapped[str | None] = mapped_column(String(128))
    evaluation_id: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)


class Contradiction(Base):
    """Detected contradictions requiring clarification."""
    __tablename__ = "contradictions"

    contradiction_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    verification_point_id: Mapped[str] = mapped_column(String(64), ForeignKey("verification_points.verification_point_id"), index=True)
    interview_id: Mapped[str] = mapped_column(String(64), ForeignKey("interviews.interview_id"))
    claim_id: Mapped[str] = mapped_column(String(64), ForeignKey("resume_claims.claim_id"))
    contradiction_type: Mapped[str] = mapped_column(String(50))  # FACTUAL/TIMELINE/ROLE/SCOPE
    severity: Mapped[str | None] = mapped_column(String(20))  # LOW/MEDIUM/HIGH
    description: Mapped[str] = mapped_column(Text)
    clarification_question: Mapped[str | None] = mapped_column(Text)
    conflicting_answers: Mapped[list | None] = mapped_column(JSON, nullable=True)  # [{answer_id, text}]
    resolution_status: Mapped[str] = mapped_column(String(50), default="UNRESOLVED", index=True)
    resolution_answer_id: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    resolved_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)


# ============================================================
# Phase 2 M2.3: Evals & Calibration
# ============================================================

class RubricVersion(Base):
    """Phase 2 M2.3: Version-controlled scoring rubrics."""
    __tablename__ = "rubric_versions"

    rubric_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    rubric_name: Mapped[str] = mapped_column(String(128), index=True)
    version: Mapped[int] = mapped_column(Integer)
    dimension_weights: Mapped[dict] = mapped_column(JSON)  # {dimension_name: weight}
    dimension_descriptors: Mapped[dict] = mapped_column(JSON)  # {dimension_name: description}
    scoring_guidelines: Mapped[str | None] = mapped_column(Text)
    level_descriptors: Mapped[dict | None] = mapped_column(JSON)  # {level: description}
    max_score: Mapped[int] = mapped_column(Integer, default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)


# ============================================================
# Phase 2 M2.5: Cross-session Ability Profile
# ============================================================

class AbilityObservation(Base):
    """Single-interview competency observations."""
    __tablename__ = "ability_observations"

    observation_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    interview_id: Mapped[str] = mapped_column(String(64), ForeignKey("interviews.interview_id"), index=True)
    resume_id: Mapped[str] = mapped_column(String(64), ForeignKey("resume_sources.resume_id"), index=True)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.user_id"), index=True)
    competency_code: Mapped[str] = mapped_column(String(128), index=True)
    question_form: Mapped[str | None] = mapped_column(String(50))  # CONCEPT/PROJECT_DETAIL/DEBUGGING/etc
    observed_level: Mapped[int] = mapped_column(Integer)  # 1-5
    confidence: Mapped[str] = mapped_column(String(20))  # LOW/MEDIUM/HIGH
    supporting_evidence_ids: Mapped[list] = mapped_column(JSON)  # Links to Evidence records
    rubric_version: Mapped[str] = mapped_column(String(32))
    observation_metadata: Mapped[dict | None] = mapped_column("metadata", JSON)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)


class AbilityProfile(Base):
    """Cross-session ability aggregation."""
    __tablename__ = "ability_profiles"

    profile_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.user_id"), index=True)
    resume_id: Mapped[str] = mapped_column(String(64), ForeignKey("resume_sources.resume_id"), index=True)
    competency_code: Mapped[str] = mapped_column(String(128), index=True)

    # Aggregated metrics
    interview_count: Mapped[int] = mapped_column(Integer, default=0)
    question_form_count: Mapped[dict] = mapped_column(JSON)  # {form_name: count}
    level_trend: Mapped[list] = mapped_column(JSON)  # [level1, level2, ...]
    current_level: Mapped[int] = mapped_column(Integer)
    stability: Mapped[str] = mapped_column(String(20))  # LOW/MEDIUM/HIGH

    # Transfer status
    transfer_status: Mapped[str] = mapped_column(String(50))  # UNTESTED/PARTIAL/DEMONSTRATED
    counterfactual_performance: Mapped[dict | None] = mapped_column(JSON)

    # Metadata
    first_observed_at: Mapped[datetime.datetime] = mapped_column(DateTime)
    last_observed_at: Mapped[datetime.datetime] = mapped_column(DateTime)
    observation_ids: Mapped[list] = mapped_column(JSON)  # Links to AbilityObservation records
    profile_metadata: Mapped[dict | None] = mapped_column("metadata", JSON)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class AnswerVersion(Base):
    """Answer retry tracking with diff analysis."""
    __tablename__ = "answer_versions"

    version_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    answer_id: Mapped[str] = mapped_column(String(64), ForeignKey("interview_answers.answer_id"), index=True)
    interview_id: Mapped[str] = mapped_column(String(64), ForeignKey("interviews.interview_id"))
    question_id: Mapped[str] = mapped_column(String(64), ForeignKey("interview_questions.question_id"))
    version_number: Mapped[int] = mapped_column(Integer)
    answer_text: Mapped[str] = mapped_column(Text)
    diff_from_previous: Mapped[dict | None] = mapped_column(JSON)  # Diff structure
    new_evidence_detected: Mapped[bool] = mapped_column(default=False)
    is_coaching_repetition: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)


class TrainingTask(Base):
    """Actionable training tasks from evidence gaps."""
    __tablename__ = "training_tasks"

    task_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.user_id"), index=True)
    resume_id: Mapped[str] = mapped_column(String(64), ForeignKey("resume_sources.resume_id"), index=True)
    interview_id: Mapped[str] = mapped_column(String(64), ForeignKey("interviews.interview_id"), index=True)

    task_type: Mapped[str] = mapped_column(String(50))  # EVIDENCE_COMPLETION/CONCEPT_REVIEW/etc
    competency_code: Mapped[str] = mapped_column(String(128))
    title: Mapped[str] = mapped_column(String(256))
    description: Mapped[str] = mapped_column(Text)
    completion_criteria: Mapped[list] = mapped_column(JSON)

    # Links to source
    claim_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("resume_claims.claim_id"))
    verification_point_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("verification_points.verification_point_id"))

    status: Mapped[str] = mapped_column(String(32), default="PENDING")  # PENDING/IN_PROGRESS/COMPLETED/DISMISSED
    priority: Mapped[int] = mapped_column(Integer, default=50)

    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    completed_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)

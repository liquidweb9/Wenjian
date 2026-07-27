import datetime
from sqlalchemy import String, Text, Float, Integer, DateTime, ForeignKey, JSON, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.persistence.database import Base
from app.core.enums import (
    ResumeStatus, SourceType, ExtractionMethod, BlockType,
    ClaimType, ExpectedLevel, VerificationCategory, ClaimStatusEnum,
)


class ResumeSource(Base):
    __tablename__ = "resume_sources"

    resume_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_id: Mapped[str] = mapped_column(String(64))
    file_name: Mapped[str] = mapped_column(String(256))
    source_type: Mapped[SourceType] = mapped_column(SAEnum(SourceType))
    sha256: Mapped[str | None] = mapped_column(String(64))
    file_size: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    revisions: Mapped[list["ResumeRevision"]] = relationship(back_populates="source")


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
    thread_id: Mapped[str] = mapped_column(String(64), unique=True)
    resume_id: Mapped[str] = mapped_column(String(64), ForeignKey("resume_sources.resume_id"))
    target_role: Mapped[str] = mapped_column(String(256))
    job_description: Mapped[str | None] = mapped_column(Text)
    mode: Mapped[str] = mapped_column(String(32), default="simulation")
    max_turns: Mapped[int] = mapped_column(Integer, default=15)
    status: Mapped[str] = mapped_column(String(32), default="created")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    finished_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    question_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    interview_id: Mapped[str] = mapped_column(String(64), ForeignKey("interviews.interview_id"))
    data: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)


class InterviewAnswer(Base):
    __tablename__ = "interview_answers"

    answer_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    interview_id: Mapped[str] = mapped_column(String(64), ForeignKey("interviews.interview_id"))
    question_id: Mapped[str] = mapped_column(String(64), ForeignKey("interview_questions.question_id"))
    answer_text: Mapped[str] = mapped_column(Text)
    analysis: Mapped[dict | None] = mapped_column(JSON)
    evaluation: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)


class InterviewReport(Base):
    __tablename__ = "interview_reports"

    report_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    interview_id: Mapped[str] = mapped_column(String(64), ForeignKey("interviews.interview_id"), unique=True)
    data: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)


class LLMCall(Base):
    """Audit log for every LLM API call."""
    __tablename__ = "llm_calls"

    call_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    task_name: Mapped[str] = mapped_column(String(128))
    model: Mapped[str] = mapped_column(String(128))
    model_tier: Mapped[str] = mapped_column(String(32))
    prompt_version: Mapped[str | None] = mapped_column(String(32))
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32))  # "ok" or "error"
    error_code: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)


class PromptVersion(Base):
    """Track prompt versions for audit and evaluation."""
    __tablename__ = "prompt_versions"

    prompt_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    task_name: Mapped[str] = mapped_column(String(128))
    version: Mapped[int] = mapped_column(Integer, default=1)
    system_prompt: Mapped[str] = mapped_column(Text)
    input_schema: Mapped[dict | None] = mapped_column(JSON)
    output_model: Mapped[str | None] = mapped_column(String(128))
    rules: Mapped[str | None] = mapped_column(Text)
    examples: Mapped[list | None] = mapped_column(JSON)
    forbid_list: Mapped[list | None] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

from pydantic import BaseModel, Field


class DateRange(BaseModel):
    start: str | None = None
    end: str | None = None
    raw: str | None = None


class ResumeEntry(BaseModel):
    entry_id: str
    section: str
    title: str
    organization: str | None = None
    role: str | None = None
    date_range: DateRange | None = None
    summary: str | None = None
    bullets: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    source_block_ids: list[str] = Field(default_factory=list)
    confidence: float = 1.0


class ResumeProfile(BaseModel):
    resume_id: str
    revision_id: str
    candidate_name: str | None = None
    headline: str | None = None
    education: list[ResumeEntry] = Field(default_factory=list)
    experiences: list[ResumeEntry] = Field(default_factory=list)
    projects: list[ResumeEntry] = Field(default_factory=list)
    research: list[ResumeEntry] = Field(default_factory=list)
    competitions: list[ResumeEntry] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    extraction_confidence: float = 1.0
    warnings: list[str] = Field(default_factory=list)


class VerificationPoint(BaseModel):
    point_id: str
    description: str
    category: str = "implementation"
    target_depth: int = Field(ge=1, le=7, default=3)
    importance: int = Field(ge=1, le=10, default=5)


class ResumeClaim(BaseModel):
    claim_id: str
    entry_id: str
    source_block_ids: list[str] = Field(default_factory=list)
    claim_text: str
    claim_type: str = "implementation"
    technologies: list[str] = Field(default_factory=list)
    expected_level: str = "use"
    verification_points: list[VerificationPoint] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    priority: int = Field(ge=1, le=100, default=50)
    confidence: float = Field(ge=0, le=1, default=0.5)


class InterviewPlan(BaseModel):
    target_role: str
    total_minutes: int = 30
    max_turns: int = 15
    topics: list["TopicPlan"] = Field(default_factory=list)
    behavioral_question_count: int = 1
    closing_question_count: int = 0
    warnings: list[str] = Field(default_factory=list)


class TopicPlan(BaseModel):
    topic_id: str
    name: str
    related_claim_ids: list[str] = Field(default_factory=list)
    weight: int = Field(ge=0, le=100, default=20)
    target_depth: int = Field(ge=1, le=7, default=3)
    min_questions: int = 1
    max_questions: int = 5
    required_dimensions: list[str] = Field(default_factory=list)
    reason: str = ""

"""Repository layer exports."""

# Legacy repositories (Phase 1 - no auth)
from app.persistence.repositories.resume_repo import ResumeRepository as ResumeRepo
from app.persistence.repositories.interview_repo import InterviewRepository as InterviewRepo
from app.persistence.repositories.evidence_repo import EvidenceRepository as EvidenceRepo

# Auth-enabled repositories (M2.6)
from app.persistence.repositories.user_repo import (
    UserRepository,
    ResumeRepository as AuthResumeRepository,
    InterviewRepository as AuthInterviewRepository,
    ReportRepository,
    JobTargetRepository,
    AbilityProfileRepository,
    TrainingTaskRepository,
)

__all__ = [
    # Legacy (backward compat)
    "ResumeRepo",
    "InterviewRepo",
    "EvidenceRepo",
    # Auth-enabled
    "UserRepository",
    "AuthResumeRepository",
    "AuthInterviewRepository",
    "ReportRepository",
    "JobTargetRepository",
    "AbilityProfileRepository",
    "TrainingTaskRepository",
]

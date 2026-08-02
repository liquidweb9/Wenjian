"""Job target system for Phase 2.

Provides job target templates and JD parsing functionality.
"""

from app.job_target.templates import (
    JobTargetTemplate,
    RequirementTemplate,
    JobLevel,
    InterviewRound,
    ALL_TEMPLATES,
    get_template_by_id,
    list_templates,
    get_template_ids,
)

__all__ = [
    "JobTargetTemplate",
    "RequirementTemplate",
    "JobLevel",
    "InterviewRound",
    "ALL_TEMPLATES",
    "get_template_by_id",
    "list_templates",
    "get_template_ids",
]

"""Tests for claim extraction budgets and source filtering."""

from app.resume.claim_extractor import ClaimExtractor
from app.resume.claim_selection import select_core_claims
from app.resume.schemas import ResumeClaim, ResumeEntry, ResumeProfile


def entry(entry_id: str, section: str) -> ResumeEntry:
    return ResumeEntry(
        entry_id=entry_id,
        section=section,
        title=entry_id,
    )


def claim(entry_id: str, index: int) -> ResumeClaim:
    return ResumeClaim(
        claim_id=f"model-claim-{index}",
        entry_id=entry_id,
        claim_text=f"Claim {index} for {entry_id}",
    )


def test_claim_budget_excludes_education_and_limits_each_entry():
    profile = ResumeProfile(
        resume_id="res-test",
        revision_id="rev-test",
        education=[entry("edu-1", "education")],
        experiences=[entry("exp-1", "experience")],
        projects=[entry("project-1", "project")],
    )
    claims = (
        [claim("edu-1", index) for index in range(5)]
        + [claim("exp-1", index) for index in range(5, 10)]
        + [claim("project-1", index) for index in range(10, 15)]
    )

    limited = ClaimExtractor()._limit_claims(claims, profile)

    assert len(limited) == 6
    assert all(item.entry_id != "edu-1" for item in limited)
    assert sum(item.entry_id == "exp-1" for item in limited) == 3
    assert sum(item.entry_id == "project-1" for item in limited) == 3


def test_legacy_claim_selection_uses_profile_sections():
    profile = {
        "education": [{"entry_id": "edu-1"}],
        "experiences": [{"entry_id": "exp-1"}],
        "projects": [{"entry_id": "project-1"}],
        "research": [],
    }
    claims = (
        [{"claim_id": f"edu-{i}", "entry_id": "edu-1", "claim_text": f"edu {i}"} for i in range(4)]
        + [{"claim_id": f"exp-{i}", "entry_id": "exp-1", "claim_text": f"exp {i}"} for i in range(5)]
        + [{"claim_id": f"project-{i}", "entry_id": "project-1", "claim_text": f"project {i}"} for i in range(5)]
    )

    selected = select_core_claims(claims, profile)

    assert len(selected) == 6
    assert all(item["entry_id"] != "edu-1" for item in selected)

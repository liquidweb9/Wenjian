"""Ability profile API endpoints for Phase 2.4.

Provides cross-session ability profiles aggregated from finished interview
reports for a given resume.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.abilities.aggregator import AbilityAggregator
from app.core.deps import get_current_user
from app.persistence.database import get_session
from app.persistence.models import (
    Interview,
    InterviewReport,
    ResumeSource,
    User,
)

router = APIRouter(prefix="/abilities", tags=["abilities"])

# Reports do not persist question_form yet (M2.4 multi-form wiring is pending),
# so verification-angle labels are derived from the 7-level depth model. Depth 7
# maps to "evolution" rather than "counterfactual" so transfer ability is never
# inferred from depth alone.
_DEPTH_ANGLES: dict[int, str] = {
    1: "background",
    2: "background",
    3: "detail",
    4: "detail",
    5: "deep",
    6: "deep",
    7: "evolution",
}


def _evidence_metrics(claim_statuses: dict[str, Any]) -> dict[str, Any]:
    """Aggregate verification-point evidence metrics from claim statuses.

    Claim statuses initialized by the graph carry verified/partial/missing
    point arrays (see initialize.py); legacy reports may only have a status
    string or a status-less dict, in which case each claim counts as one point.
    The two formats can be mixed within one report, so each claim is classified
    independently.
    """
    verified = 0
    partial = 0
    missing = 0
    legacy_total = 0
    legacy_verified = 0

    for status in claim_statuses.values():
        if isinstance(status, dict) and status.get("verified_points") is not None:
            verified += len(status["verified_points"])
            partial += len(status.get("partial_points", []))
            missing += len(status.get("missing_points", []))
        else:
            legacy_total += 1
            status_value = (
                status
                if isinstance(status, str)
                else status.get("status") if isinstance(status, dict) else None
            )
            if status_value == "VERIFIED":
                legacy_verified += 1

    total_points = verified + partial + missing + legacy_total
    verified_count = verified + legacy_verified

    strength = verified_count / total_points if total_points else 0.0

    # VERIFIED only when every addressed point is fully verified.
    if total_points and verified_count == total_points:
        evidence_status = "VERIFIED"
    elif verified_count > 0:
        evidence_status = "PARTIALLY_SUPPORTED"
    else:
        evidence_status = "UNVERIFIED"

    return {
        "verification_points_addressed": total_points,
        "verification_points_verified": verified_count,
        "evidence_strength": strength,
        "evidence_status": evidence_status,
    }


def _unresolved_contradictions(report_data: dict) -> int:
    """Count unresolved contradictions recorded in one report.

    Report contradictions are stored in state format (see update_evidence.py)
    and carry a ``resolved`` boolean that defaults to False. Persisted data does
    not attribute a contradiction to a rubric dimension, so the count is
    report-level rather than per-competency.
    """
    contradictions = report_data.get("contradictions") or []
    return sum(
        1
        for c in contradictions
        if not (isinstance(c, dict) and c.get("resolved", False))
    )


def _build_observation(
    report_data: dict,
    competency: str,
    created_at: str | None,
) -> dict | None:
    """Build an AbilityAggregator-compatible observation from one report.

    Args:
        report_data: Report.data dict
        competency: Competency code whose ability_scores entry to use
        created_at: Report creation timestamp

    Returns:
        Observation dict, or None if the report has no score for the competency
    """
    ability_scores = report_data.get("ability_scores") or report_data.get("abilities") or {}
    question_details = report_data.get("question_details") or report_data.get("questions") or []
    claim_statuses = report_data.get("claim_statuses") or report_data.get("claims") or {}

    score = ability_scores.get(competency)
    if not isinstance(score, (int, float)):
        return None

    answered = [
        qd for qd in question_details
        if isinstance(qd, dict) and qd.get("score") is not None
    ]
    depths = [int(qd.get("depth") or 0) for qd in answered]

    forms = [str(qd["question_form"]) for qd in answered if qd.get("question_form")]
    if not forms:
        forms = sorted({_DEPTH_ANGLES[d] for d in depths if d in _DEPTH_ANGLES})

    metrics = _evidence_metrics(claim_statuses)

    return {
        "question_count": len(answered),
        "question_forms": forms,
        "avg_score": float(score),
        "max_depth": max(depths) if depths else 0,
        **metrics,
        "contradiction_count": _unresolved_contradictions(report_data),
        "created_at": created_at,
    }


async def _load_report_rows(
    session: AsyncSession,
    resume_id: str,
    user_id: str,
) -> list[tuple[Any, Any]]:
    """Load finished interview reports for a resume owned by a user."""
    stmt = (
        select(Interview, InterviewReport)
        .join(InterviewReport, InterviewReport.interview_id == Interview.interview_id)
        .where(
            Interview.resume_id == resume_id,
            Interview.user_id == user_id,
        )
        .order_by(Interview.created_at.asc())
    )
    result = await session.execute(stmt)
    return list(result.all())


def _observations_by_competency(
    rows: list[tuple[Any, Any]],
) -> tuple[dict[str, list[dict]], dict[str, list[dict]], set[str]]:
    """Build per-competency observations and history from report rows.

    Shared by the ability profile endpoint and the training plan generator so
    both derive identical observations from the same reports.

    Returns:
        (observations, history, contributing_interviews)
    """
    observations_by_competency: dict[str, list[dict]] = {}
    history_by_competency: dict[str, list[dict]] = {}
    contributing_interviews: set[str] = set()

    for interview, report in rows:
        report_data = report.data if isinstance(report.data, dict) else {}
        ability_scores = report_data.get("ability_scores") or report_data.get("abilities") or {}
        created_at = report.created_at.isoformat() if report.created_at else None

        for competency in ability_scores:
            obs = _build_observation(report_data, competency, created_at)
            if obs is None:
                continue
            observations_by_competency.setdefault(competency, []).append(obs)
            history_by_competency.setdefault(competency, []).append(
                {
                    "interview_id": interview.interview_id,
                    "score": obs["avg_score"],
                    "created_at": created_at,
                }
            )
            contributing_interviews.add(interview.interview_id)

    return observations_by_competency, history_by_competency, contributing_interviews


@router.get("/profile/{resume_id}")
async def get_ability_profile(
    resume_id: str,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Aggregate cross-session ability profile for a resume.

    Derives per-interview observations from finished interview reports and
    aggregates them per competency using AbilityAggregator.

    Args:
        resume_id: Resume ID
        user: Current authenticated user
        session: Database session

    Returns:
        Per-competency aggregated profile with per-interview score history

    Raises:
        HTTPException: 404 if resume not found or not owned by user
    """
    resume = await session.get(ResumeSource, resume_id)
    if not resume or resume.user_id != user.user_id:
        raise HTTPException(status_code=404, detail="Resume not found")

    rows = await _load_report_rows(session, resume_id, user.user_id)
    if not rows:
        return {"resume_id": resume_id, "total_interviews": 0, "competencies": []}

    observations_by_competency, history_by_competency, contributing_interviews = (
        _observations_by_competency(rows)
    )

    aggregator = AbilityAggregator()
    competencies = [
        {
            "competency_code": code,
            "profile": aggregator.aggregate_observations(observations),
            "history": history_by_competency[code],
        }
        for code, observations in sorted(observations_by_competency.items())
    ]

    return {
        "resume_id": resume_id,
        # Only count reports that yielded at least one competency observation.
        "total_interviews": len(contributing_interviews),
        "competencies": competencies,
    }

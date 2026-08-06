"""Analytics endpoints — trends, distributions, ability summaries."""

from collections import defaultdict
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.persistence.database import get_session
from app.persistence.models import Interview, InterviewReport, User

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
async def get_analytics_summary(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Aggregated analytics — score distribution, top/weak abilities, verification rates."""

    total_r = await session.execute(
        select(func.count(Interview.interview_id)).where(
            Interview.user_id == user.user_id
        )
    )
    total_interviews = total_r.scalar() or 0

    # Pull reports (current user only)
    reports_r = await session.execute(
        select(InterviewReport.data)
        .join(Interview, Interview.interview_id == InterviewReport.interview_id)
        .where(Interview.user_id == user.user_id)
    )
    report_data = [r[0] for r in reports_r.all() if isinstance(r[0], dict)]

    scores = []
    ability_totals: dict[str, list[float]] = defaultdict(list)
    claim_status_counts: dict[str, int] = defaultdict(int)

    for rd in report_data:
        s = rd.get("overall_score") or rd.get("score")
        if isinstance(s, (int, float)):
            scores.append(float(s))

        abilities = rd.get("abilities") or rd.get("ability_scores") or {}
        if isinstance(abilities, dict):
            for name, score in abilities.items():
                if isinstance(score, (int, float)):
                    ability_totals[name].append(float(score))

        claims = rd.get("claim_statuses") or rd.get("claims") or {}
        if isinstance(claims, dict):
            for _cid, cs in claims.items():
                status = cs if isinstance(cs, str) else cs.get("status", "UNKNOWN") if isinstance(cs, dict) else "UNKNOWN"
                claim_status_counts[status] += 1
        elif isinstance(claims, list):
            for c in claims:
                status = c if isinstance(c, str) else c.get("status", "UNKNOWN") if isinstance(c, dict) else "UNKNOWN"
                claim_status_counts[status] += 1

    avg_score = round(sum(scores) / len(scores), 1) if scores else None

    # Score distribution buckets
    buckets = {"0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0}
    for s in scores:
        if s <= 20:
            buckets["0-20"] += 1
        elif s <= 40:
            buckets["21-40"] += 1
        elif s <= 60:
            buckets["41-60"] += 1
        elif s <= 80:
            buckets["61-80"] += 1
        else:
            buckets["81-100"] += 1

    # Top and weak abilities
    ability_averages = {k: round(sum(v) / len(v), 1) for k, v in ability_totals.items() if v}
    sorted_abilities = sorted(ability_averages.items(), key=lambda x: x[1], reverse=True)
    top_abilities = [{"name": k, "score": v} for k, v in sorted_abilities[:3]]
    weak_abilities = [{"name": k, "score": v} for k, v in sorted_abilities[-3:]]

    total_claims = sum(claim_status_counts.values())
    verified = claim_status_counts.get("VERIFIED", 0)
    verification_rate = round(verified / total_claims * 100, 1) if total_claims > 0 else None

    return {
        "total_interviews": total_interviews,
        "average_score": avg_score,
        "score_distribution": buckets,
        "top_abilities": top_abilities,
        "weak_abilities": weak_abilities,
        "claim_verification_rate": verification_rate,
        "claim_status_counts": dict(claim_status_counts),
    }


@router.get("/trends")
async def get_analytics_trends(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Time-series trends for interviews and abilities."""

    interviews_r = await session.execute(
        select(
            Interview.created_at,
            Interview.status,
            Interview.interview_id,
        )
        .where(Interview.user_id == user.user_id)
        .order_by(Interview.created_at.asc())
    )
    interviews = interviews_r.all()

    reports_r = await session.execute(
        select(InterviewReport.interview_id, InterviewReport.data, InterviewReport.created_at)
        .join(Interview, Interview.interview_id == InterviewReport.interview_id)
        .where(Interview.user_id == user.user_id)
    )
    reports = {(r[0], r[2]): r[1] for r in reports_r.all() if isinstance(r[1], dict)}

    # Interviews over time (by week)
    weekly_counts: dict[str, int] = defaultdict(int)
    for created_at, _status, _iid in interviews:
        if created_at:
            week_key = created_at.strftime("%Y-W%W")
            weekly_counts[week_key] += 1

    # Score trend
    score_trend: list[dict] = []
    for created_at, status, iid in interviews:
        if status == "finished" and created_at:
            for (rid, rdate), rdata in reports.items():
                if rid == iid:
                    s = rdata.get("overall_score") or rdata.get("score")
                    if isinstance(s, (int, float)):
                        score_trend.append({
                            "date": created_at.strftime("%Y-%m-%d"),
                            "score": float(s),
                        })
                    break

    return {
        "interviews_over_time": [
            {"week": k, "count": v} for k, v in sorted(weekly_counts.items())
        ],
        "score_trend": score_trend,
    }

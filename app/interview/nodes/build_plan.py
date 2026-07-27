"""Build interview plan from resume profile and claims."""

from app.core.ids import new_id
from app.interview.state import InterviewState
from app.observability.logging import logger
from app.resume.schemas import InterviewPlan, TopicPlan


async def build_plan_node(state: InterviewState) -> dict:
    """Build interview plan."""
    profile = state.get("resume_profile", {})
    claims = state.get("resume_claims", [])
    target_role = state.get("target_role", "")
    max_turns = state.get("max_turns", 15)

    # Topic boundaries are a product rule, not a generative decision: one topic
    # always maps to one resume project/work entry.
    plan = _project_plan(profile, claims, target_role, max_turns)
    logger.info("plan_built", topics=len(plan.topics), target=target_role)

    return {"interview_plan": plan.model_dump(mode="json")}


def _project_plan(
    profile: dict,
    claims: list[dict],
    target_role: str,
    max_turns: int,
    warnings: list[str] | None = None,
) -> InterviewPlan:
    """Build one interview topic per project/work entry."""
    plan = InterviewPlan(target_role=target_role, max_turns=max_turns)
    plan.warnings.extend(warnings or [])
    claims_by_entry: dict[str, list[dict]] = {}
    for claim in claims:
        claims_by_entry.setdefault(claim.get("entry_id", ""), []).append(claim)

    entries = [
        entry
        for section in ("experiences", "projects", "research")
        for entry in profile.get(section, [])
        if claims_by_entry.get(entry.get("entry_id", ""))
    ]
    entries.sort(
        key=lambda entry: max(
            claim.get("priority", 0)
            for claim in claims_by_entry[entry.get("entry_id", "")]
        ),
        reverse=True,
    )

    selected = entries[: max(1, min(len(entries), max_turns))]
    questions_per_topic = max(1, max_turns // max(len(selected), 1))
    for entry in selected:
        related = sorted(
            claims_by_entry[entry.get("entry_id", "")],
            key=lambda claim: claim.get("priority", 0),
            reverse=True,
        )
        priority = max(claim.get("priority", 50) for claim in related)
        plan.topics.append(
            TopicPlan(
                topic_id=new_id("topic"),
                name=entry.get("title") or entry.get("organization") or "项目经历",
                related_claim_ids=[
                    claim.get("claim_id", "") for claim in related if claim.get("claim_id")
                ],
                weight=max(10, priority),
                target_depth=5 if priority >= 70 else 3,
                min_questions=1,
                max_questions=questions_per_topic,
                required_dimensions=[
                    "project_overview",
                    "personal_contribution",
                    "architecture",
                    "production",
                    "tradeoff",
                ],
                reason="Project-centered topic containing all related technical claims",
            )
        )

    if plan.topics:
        total_w = sum(t.weight for t in plan.topics)
        scale = 100 / total_w if total_w else 1
        for t in plan.topics:
            t.weight = int(t.weight * scale)
        plan.topics[0].weight += 100 - sum(t.weight for t in plan.topics)

    return plan

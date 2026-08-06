"""Extract ResumeClaims from a ResumeProfile using LLM."""

from pydantic import BaseModel

from app.core.ids import new_claim_id
from app.llm.agnes_api import AgnesGateway
from app.llm.model_router import get_tier
from app.observability.logging import logger
from app.resume.schemas import ResumeClaim, ResumeProfile

CLAIM_EXTRACTOR_PROMPT = """You are a resume analyzer. Your job is to extract specific, verifiable claims from a candidate's resume profile.

For each significant experience, project, or research entry, extract only its most interview-worthy core claims.
- Architecture decision or design
- Implementation detail
- Algorithm or data structure
- Performance optimization
- Research finding
- Leadership or ownership
- Quantified result

Rules:
1. Produce 1-3 claims per entry and no more than 15 claims in total. Order them by importance.
2. Combine closely related implementation details from the same subsystem into one coherent claim. Do not create one claim per bullet, library, algorithm, or technology.
3. Prefer claims showing architecture ownership, a substantial end-to-end implementation, a difficult technical decision, or a quantified outcome.
4. Do not extract claims from education, skills, awards, or generic self-evaluation.
5. Each claim must reference the source entry by copying its exact "id=" value from the entries list. Only reference entries from [experience], [project], or [research] sections.
6. For vague improvements without baselines, add "UNVERIFIED_IMPROVEMENT" risk flag.
7. For missing metrics, add "MISSING_METRICS" risk flag.
8. For unclear role boundaries, add "UNCLEAR_OWNERSHIP" risk flag.
9. Each claim must have implementation, tradeoff, and debugging verification points.
10. Return ONLY valid JSON matching the output schema."""


class ClaimExtractor:
    def __init__(self, llm_gateway: AgnesGateway | None = None):
        self.llm = llm_gateway or AgnesGateway()

    async def extract(self, profile: ResumeProfile) -> list[ResumeClaim]:
        """Extract claims from a ResumeProfile."""
        if not profile.experiences and not profile.projects:
            logger.warning("no_entries_for_claims", resume_id=profile.resume_id)
            return []

        entries_text = self._format_entries(profile)

        try:
            # Use generate_text with JSON parsing for flexibility
            result = await self.llm.generate_structured(
                task_name="claim_extractor",
                system_prompt=CLAIM_EXTRACTOR_PROMPT,
                user_payload={
                    "entries": entries_text,
                    "skills": profile.skills,
                },
                output_model=ClaimExtractorOutput,
                model_tier=get_tier("claim_extractor"),
            )

            claims = self._limit_claims(result.claims, profile)
            # Model-provided IDs are not globally safe. Always issue our IDs.
            for claim in claims:
                claim.claim_id = new_claim_id()
                for vp in claim.verification_points:
                    vp.point_id = new_claim_id()

            logger.info("claims_extracted", count=len(claims), resume_id=profile.resume_id)
            return claims

        except Exception as e:
            logger.error("claim_extraction_failed", error=str(e))
            return []

    def _format_entries(self, profile: ResumeProfile) -> str:
        parts = []
        for section_name in ("experiences", "projects", "research"):
            entries = getattr(profile, section_name, [])
            for entry in entries:
                parts.append(
                    f"[{section_name}] id={entry.entry_id} | {entry.title}"
                    + (f" @ {entry.organization}" if entry.organization else "")
                    + "\n"
                    + "\n".join(f"  • {b}" for b in entry.bullets)
                    + (f"\n  Technologies: {', '.join(entry.technologies)}" if entry.technologies else "")
                )
        return "\n\n".join(parts)

    def _limit_claims(
        self,
        claims: list[ResumeClaim],
        profile: ResumeProfile,
    ) -> list[ResumeClaim]:
        """Enforce stable per-entry and global claim budgets."""
        valid_entry_ids = {
            entry.entry_id
            for section in (profile.experiences, profile.projects, profile.research)
            for entry in section
        }
        counts: dict[str, int] = {}
        seen: set[tuple[str, str]] = set()
        limited: list[ResumeClaim] = []
        dropped = 0

        for claim in claims:
            if claim.entry_id not in valid_entry_ids:
                dropped += 1
                continue
            normalized = " ".join(claim.claim_text.lower().split())
            key = (claim.entry_id, normalized)
            if key in seen or counts.get(claim.entry_id, 0) >= 3:
                continue
            seen.add(key)
            counts[claim.entry_id] = counts.get(claim.entry_id, 0) + 1
            limited.append(claim)
            if len(limited) >= 15:
                break

        if dropped:
            logger.warning(
                "claims_dropped_bad_entry_id",
                dropped=dropped,
                kept=len(limited),
                resume_id=profile.resume_id,
            )

        return limited


class ClaimExtractorOutput(BaseModel):
    claims: list[ResumeClaim]

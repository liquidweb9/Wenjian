"""Build ResumeProfile from ResumeDocument using LLM."""

from app.core.ids import new_id
from app.llm.agnes_api import AgnesGateway
from app.llm.model_router import get_tier
from app.observability.logging import logger
from app.parsers.schemas import ResumeDocument
from app.resume.schemas import ResumeEntry, ResumeProfile
from app.resume.section_classifier import SectionClassifier

PROFILE_BUILDER_PROMPT = """You are a high-precision resume parser. Convert the supplied ordered blocks into one coherent structured profile.

Rules:
1. Preserve document order. Use the supplied section label as context, but correct it when the text contains clear contrary evidence.
2. An entry header (project name, school/degree, or company/role/date line) starts ONE entry. All following summary and bullet blocks belong to that nearest entry until the next entry header or section heading.
3. NEVER turn individual responsibilities, achievements, technologies, or bullets into separate project/experience entries. Put them in the parent entry's bullets.
4. For work experience, organization is the employer and role is the job title. For education, organization is the school and title/role contains the degree or major. For projects, title is the project name.
5. A company line and its following role/date line may describe the same experience; merge them rather than creating duplicate entries.
6. Extract education and experience even when their headings are missing if school/degree or company/role/date evidence is explicit.
7. Every entry must include all contributing source_block_ids exactly as supplied. Never invent block IDs.
8. Technologies and skills must only contain explicitly mentioned items. Do not fabricate metrics, dates, employers, roles, or results.
9. If dates are ambiguous, preserve the original text in date_range.raw.
10. Do not use a bullet sentence as an entry title unless there is truly no project/company/school header.
11. Return ONLY valid JSON matching the output schema."""


class ProfileBuilder:
    def __init__(self, llm_gateway: AgnesGateway | None = None):
        self.llm = llm_gateway or AgnesGateway()
        self.classifier = SectionClassifier()

    async def build(self, doc: ResumeDocument) -> ResumeProfile:
        """Build a ResumeProfile from a ResumeDocument."""
        # 1. Classify sections
        section_map = self.classifier.classify(doc.blocks)

        # 2. Build structured profile via LLM
        blocks_text = "\n".join(
            (
                f'<block id="{b.block_id}" section="{section_map.get(i, "unknown")}" '
                f'type="{b.block_type}">\n{b.text}\n</block>'
            )
            for i, b in enumerate(doc.blocks)
        )

        try:
            profile_data = await self.llm.generate_structured(
                task_name="profile_builder",
                system_prompt=PROFILE_BUILDER_PROMPT,
                user_payload={
                    "blocks": blocks_text,
                    "raw_text": doc.normalized_text[:12000],
                },
                output_model=ResumeProfile,
                model_tier=get_tier("profile_builder"),
            )

            # Override with correct IDs
            profile_data.resume_id = doc.resume_id
            profile_data.revision_id = doc.revision_id

            logger.info("profile_built", resume_id=doc.resume_id, entries=len(profile_data.experiences))
            return profile_data

        except Exception as e:
            logger.error("profile_build_failed", error=str(e))
            return self._build_fallback(doc)

    def _build_fallback(self, doc: ResumeDocument) -> ResumeProfile:
        """Build a useful section-aware profile when the LLM is unavailable."""
        section_map = self.classifier.classify(doc.blocks)
        entries: dict[str, list[ResumeEntry]] = {
            "education": [],
            "experience": [],
            "project": [],
            "research": [],
            "competition": [],
        }
        active: dict[str, ResumeEntry] = {}
        skills: list[str] = []
        unknown_lines: list[str] = []

        for index, block in enumerate(doc.blocks):
            section = section_map.get(index, "unknown")
            text = block.text.strip()
            if not text or block.block_type == "heading":
                continue

            if section == "skills":
                skills.extend(
                    item.strip()
                    for item in text.replace("，", ",").replace("\n", ",").split(",")
                    if item.strip()
                )
                continue

            if section == "unknown":
                unknown_lines.extend(line.strip() for line in text.splitlines() if line.strip())
                continue

            if section not in entries:
                continue

            current = active.get(section)
            starts_entry = block.block_type == "entry_header" or current is None
            if starts_entry:
                current = ResumeEntry(
                    entry_id=new_id("entry"),
                    section=section,
                    title=text.splitlines()[0],
                    source_block_ids=[block.block_id],
                    confidence=0.45,
                )
                entries[section].append(current)
                active[section] = current
            elif block.block_type == "bullet":
                current.bullets.extend(
                    line.strip().lstrip("•·●▪◦‣⁃–—*- ").strip()
                    for line in text.splitlines()
                    if line.strip()
                )
                current.source_block_ids.append(block.block_id)
            else:
                current.summary = " ".join(
                    part for part in (current.summary, text) if part
                )
                current.source_block_ids.append(block.block_id)

        return ResumeProfile(
            resume_id=doc.resume_id,
            revision_id=doc.revision_id,
            candidate_name=unknown_lines[0] if unknown_lines else None,
            headline=unknown_lines[1] if len(unknown_lines) > 1 else None,
            education=entries["education"],
            experiences=entries["experience"],
            projects=entries["project"],
            research=entries["research"],
            competitions=entries["competition"],
            skills=list(dict.fromkeys(skills)),
            warnings=["Profile builder LLM call failed; used deterministic section parser"],
            extraction_confidence=0.45,
        )

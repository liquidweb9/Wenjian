"""Resume orchestration service."""

from app.parsers.schemas import ParseInput, ResumeDocument
from app.parsers.registry import ParserRegistry
from app.parsers.ingress import FileIngressValidator
from app.parsers.normalizer import Normalizer
from app.resume.profile_builder import ProfileBuilder
from app.resume.claim_extractor import ClaimExtractor
from app.resume.claim_ranker import ClaimRanker
from app.resume.schemas import ResumeProfile, ResumeClaim
from app.llm.agnes_api import AgnesGateway
from app.core.ids import new_resume_id, new_revision_id
from app.observability.logging import logger


class ResumeService:
    def __init__(self):
        self.parser_registry = ParserRegistry()
        self.validator = FileIngressValidator()
        self.normalizer = Normalizer()
        self.llm = AgnesGateway()
        self.profile_builder = ProfileBuilder(self.llm)
        self.claim_extractor = ClaimExtractor(self.llm)
        self.claim_ranker = ClaimRanker()

    async def parse_resume(self, content: bytes, filename: str, mime: str | None = None) -> ResumeDocument:
        """Parse a resume file end-to-end."""
        # Validate
        sha256 = await self.validator.validate(content, filename, mime)

        # Resolve parser
        ext = self._get_ext(filename)
        head = content[:256]
        parser = self.parser_registry.resolve(ext, mime, head)

        # Parse
        resume_id = new_resume_id()
        revision_id = new_revision_id()
        parse_input = ParseInput(
            source_id=resume_id,
            file_name=filename,
            declared_mime_type=mime,
            content=content,
        )
        doc = await parser.parse(parse_input)
        doc.resume_id = resume_id
        doc.revision_id = revision_id

        # Preserve parser/extraction warnings before normalization adds its own
        parser_warnings = list(doc.extraction_warnings or [])

        # Normalize
        doc = self.normalizer.normalize(doc)

        # Merge warnings: parser warnings + normalizer warnings, deduplicated
        seen = set()
        merged_dedup = []
        for w in parser_warnings + (doc.extraction_warnings or []):
            if w not in seen:
                seen.add(w)
                merged_dedup.append(w)
        doc.extraction_warnings = merged_dedup

        logger.info("resume_parsed", resume_id=resume_id, quality=doc.extraction_quality, parser=parser.name)
        return doc

    async def build_profile(self, doc: ResumeDocument) -> ResumeProfile:
        """Build profile from parsed document."""
        return await self.profile_builder.build(doc)

    async def extract_claims(self, profile: ResumeProfile, target_role: str = "") -> list[ResumeClaim]:
        """Extract and rank claims from profile."""
        claims = await self.claim_extractor.extract(profile)
        ranker = ClaimRanker(target_role=target_role, llm_gateway=self.llm)
        claims = await ranker.rank(claims)
        return claims

    def _get_ext(self, filename: str) -> str:
        idx = filename.rfind(".")
        return filename[idx:].lower() if idx != -1 else ""

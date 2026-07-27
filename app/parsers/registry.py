import logging

from app.parsers.base import ResumeParser
from app.parsers.detector import detect_source_type, strict_detect
from app.parsers.text_parser import TextParser
from app.parsers.pdf_parser import PdfParser
from app.parsers.latex_parser import LatexParser
from app.core.exceptions import AppError, RESUME_TYPE_MISMATCH

logger = logging.getLogger(__name__)

PARSER_MAP = {
    "pdf": PdfParser,
    "text": TextParser,
    "latex": LatexParser,
}


class ParserRegistry:
    def __init__(self, parsers: list[ResumeParser] | None = None):
        self._parsers: dict[str, ResumeParser] = {}
        if parsers:
            for p in parsers:
                self._parsers[type(p).__name__] = p

    def register(self, name: str, parser: ResumeParser):
        self._parsers[name] = parser

    def resolve(self, extension: str, mime_type: str | None, head_bytes: bytes) -> ResumeParser:
        try:
            source_type = strict_detect(head_bytes, mime_type, extension)
        except AppError as e:
            if e.code != RESUME_TYPE_MISMATCH:
                raise
            logger.warning(
                "Strict detection failed, falling back to loose detection: %s",
                e.message,
            )
            source_type = detect_source_type(head_bytes, mime_type, extension)
        parser_cls = PARSER_MAP[source_type]
        name = parser_cls.__name__
        if name not in self._parsers:
            self._parsers[name] = parser_cls()
        return self._parsers[name]

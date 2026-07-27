"""Text parser for .txt files and plain text input."""

import re

import chardet

from app.core.ids import new_id
from app.parsers.base import ResumeParser
from app.parsers.quality import assess_quality
from app.parsers.schemas import ParseInput, ResumeBlock, ResumeDocument, SourceLocation

SECTION_HEADINGS = {
    "教育", "教育背景", "教育经历", "学历背景", "学历经历",
    "工作经历", "工作经验", "职业经历", "实习经历", "任职经历",
    "项目", "项目经历", "项目经验", "个人项目", "代表项目",
    "科研经历", "研究经历", "论文", "论文发表",
    "专业技能", "技能", "技能清单", "技术栈", "核心能力",
    "获奖经历", "荣誉", "荣誉奖项", "竞赛经历",
    "education", "academic background", "educational background",
    "experience", "work experience", "work history", "professional experience",
    "employment history", "internship", "internships",
    "project", "projects", "project experience", "selected projects",
    "research", "research experience", "publication", "publications",
    "skill", "skills", "technical skills", "core competencies", "tech stack",
    "award", "awards", "honor", "honors", "competitions",
}
BULLET_RE = re.compile(r"^(?:[•·●▪◦‣⁃–—*-]|\d+[.)、])\s+")
ENTRY_HEADER_RE = re.compile(
    r"(?:\s[|｜]\s|\t)|"
    r"(?:19|20)\d{2}[./年-]\d{1,2}.*"
    r"(?:至今|现在|present|current|now|(?:19|20)\d{2})",
    re.IGNORECASE,
)


def _is_section_heading(text: str) -> bool:
    normalized = text.strip().strip("═━─—-=_*# ").rstrip(":：").strip().lower()
    return normalized in SECTION_HEADINGS


class TextParser(ResumeParser):
    name = "text_parser"
    version = "0.2.0"

    async def parse(self, parse_input: ParseInput) -> ResumeDocument:
        raw_text = self._decode(parse_input.content)
        normalized_text = self._normalize(raw_text)
        blocks = self._split_blocks(normalized_text)

        quality_result = assess_quality(blocks)
        warnings = list(quality_result.get("warnings", []))

        return ResumeDocument(
            resume_id="",
            source_id=parse_input.source_id,
            file_name=parse_input.file_name,
            source_type="text",
            raw_text=raw_text,
            normalized_text=normalized_text,
            blocks=blocks,
            extraction_method="plain_text",
            extraction_quality=quality_result["score"],
            extraction_warnings=warnings,
            parser_name=self.name,
            parser_version=self.version,
        )

    def _decode(self, content: bytes) -> str:
        result = chardet.detect(content)
        encoding = result.get("encoding") or "utf-8"
        try:
            return content.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            return content.decode("utf-8", errors="replace")

    def _normalize(self, text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        return "".join(
            ch
            for ch in text
            if ch in ("\n", "\t") or ord(ch) >= 32
        )

    def _split_blocks(self, text: str) -> list[ResumeBlock]:
        """Split on resume semantics instead of relying only on blank lines."""
        blocks: list[ResumeBlock] = []
        lines = text.split("\n")
        current_para: list[str] = []
        para_start = 0
        offset = 0

        def flush_para(line_number: int) -> None:
            nonlocal current_para
            if current_para:
                blocks.append(
                    self._make_block(
                        "\n".join(current_para), para_start, line_number
                    )
                )
                current_para = []

        for i, line in enumerate(lines):
            stripped = line.strip()

            if not stripped:
                flush_para(i)
                offset += len(line) + 1
                continue

            if _is_section_heading(stripped):
                flush_para(i)
                blocks.append(self._make_block(stripped, offset, i, "heading"))
            elif BULLET_RE.match(stripped):
                flush_para(i)
                blocks.append(self._make_block(stripped, offset, i, "bullet"))
            elif ENTRY_HEADER_RE.search(stripped):
                flush_para(i)
                blocks.append(
                    self._make_block(stripped, offset, i, "entry_header")
                )
            else:
                if not current_para:
                    para_start = offset
                current_para.append(stripped)

            offset += len(line) + 1

        flush_para(len(lines))
        return blocks

    def _make_block(
        self,
        text: str,
        char_start: int,
        line: int,
        block_type: str = "paragraph",
    ) -> ResumeBlock:
        return ResumeBlock(
            block_id=new_id("blk"),
            text=text,
            raw_text=text,
            block_type=block_type,  # type: ignore[arg-type]
            source_location=SourceLocation(char_start=char_start),
            style_hints={"line": line},
        )

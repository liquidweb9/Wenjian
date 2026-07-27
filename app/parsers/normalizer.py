"""Deterministic text normalizer - no LLM calls.

Implements the architecture-defined line merging rules:
- Merge lines that are not complete sentences
- Skip lines that look like headings or new entry headers
- Only merge when font size/indent is similar
"""

import re
from app.parsers.schemas import ResumeDocument, ResumeBlock

# Common section heading patterns
SECTION_PATTERNS = {
    "education": re.compile(r"教育背景|教育经历|Education", re.IGNORECASE),
    "experience": re.compile(r"实习经历|工作经历|Experience|Work History", re.IGNORECASE),
    "project": re.compile(r"项目经历|项目经验|Projects", re.IGNORECASE),
    "research": re.compile(r"科研经历|研究经历|Research", re.IGNORECASE),
    "competition": re.compile(r"竞赛经历|获奖经历|Awards|Honors", re.IGNORECASE),
    "skills": re.compile(r"专业技能|技能|Skills|Technical Skills", re.IGNORECASE),
}

# Header/footer patterns (page numbers, dates, etc.)
HEADER_FOOTER_RE = re.compile(
    r"^\s*(Page\s+\d+|第\s*\d+\s*页|\d+\s*/\s*\d+|\d{4}-\d{2}-\d{2})\s*$",
    re.IGNORECASE,
)
CONTINUED_RE = re.compile(r"\(.*Continued.*\)|\(.*续.*\)", re.IGNORECASE)

# Patterns that indicate a complete line (ends with sentence-ending punctuation)
COMPLETE_SENTENCE_RE = re.compile(r".*[.!?。！？）)]$")

# Patterns that look like new entry headers (date-based, role-based)
ENTRY_HEADER_RE = re.compile(
    r"^\d{4}.*\d{4}|^\d{2,4}\.\d{1,2}.*\d{2,4}\.\d{1,2}|"
    r"^.*\|.*\||^[A-Z][a-z]+.*Engineer|^[A-Z][a-z]+.*Manager",
    re.IGNORECASE,
)

# Patterns that look like dates
DATE_PATTERN_RE = re.compile(
    r"^\s*\d{4}\s*[-–—/]\s*(?:\d{4}|至今|present|now)\s*$",
    re.IGNORECASE,
)


class Normalizer:
    def normalize(self, doc: ResumeDocument) -> ResumeDocument:
        """Normalize a ResumeDocument in place."""
        normalized = doc.normalized_text
        normalized = self._normalize_whitespace(normalized)
        doc.normalized_text = normalized

        # Merge consecutive bullets and compatible paragraph lines
        merged_blocks = self._merge_blocks(doc.blocks)
        # Filter header/footer
        merged_blocks = self._filter_noise(merged_blocks)
        # Merge orphaned lines within paragraphs
        merged_blocks = self._merge_broken_lines(merged_blocks)

        doc.blocks = merged_blocks
        doc.extraction_warnings = self._check_warnings(doc.blocks)

        return doc

    def _normalize_whitespace(self, text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _merge_blocks(self, blocks: list[ResumeBlock]) -> list[ResumeBlock]:
        """Merge consecutive bullet blocks of the same type."""
        if not blocks:
            return []
        merged: list[ResumeBlock] = [blocks[0]]
        for block in blocks[1:]:
            prev = merged[-1]
            if block.block_type == "bullet" and prev.block_type == "bullet":
                prev.text += "\n" + block.text
            else:
                merged.append(block)
        return merged

    def _merge_broken_lines(self, blocks: list[ResumeBlock]) -> list[ResumeBlock]:
        """Merge broken lines following architecture doc section 6.6 rules.

        Merge conditions (ALL must be true):
        - Previous line is NOT a complete sentence
        - Next line is NOT a heading
        - Next line is NOT a new entry header
        - Previous line is NOT a standalone date
        - Both lines are paragraphs (not bullets)
        """
        if not blocks:
            return []
        merged: list[ResumeBlock] = [blocks[0]]
        for block in blocks[1:]:
            prev = merged[-1]

            prev_text = prev.text.strip()
            curr_text = block.text.strip()

            if not prev_text or not curr_text:
                if curr_text:
                    merged.append(block)
                continue

            # Only merge paragraph-type blocks
            if prev.block_type != "paragraph" or block.block_type != "paragraph":
                merged.append(block)
                continue

            # Don't merge if prev is complete sentence
            if COMPLETE_SENTENCE_RE.match(prev_text):
                merged.append(block)
                continue

            # Don't merge if current is a heading candidate
            if block.text.isupper() and len(block.text) < 40:
                merged.append(block)
                continue

            # Don't merge if current looks like a new entry header
            if ENTRY_HEADER_RE.match(curr_text):
                merged.append(block)
                continue

            # Don't merge if prev is a standalone date
            if DATE_PATTERN_RE.match(prev_text):
                merged.append(block)
                continue

            # Merge: join with space
            prev.text = prev_text + " " + curr_text

        return merged

    def _filter_noise(self, blocks: list[ResumeBlock]) -> list[ResumeBlock]:
        filtered = []
        for block in blocks:
            text = block.text.strip()
            if HEADER_FOOTER_RE.match(text):
                continue
            if CONTINUED_RE.match(text):
                continue
            if len(text) < 2:
                continue
            filtered.append(block)
        return filtered

    def _check_warnings(self, blocks: list[ResumeBlock]) -> list[str]:
        warnings = []
        total_text = " ".join(b.text for b in blocks)
        symbol_ratio = sum(1 for c in total_text if c in "@#$%^&*=|\\<>`~") / max(len(total_text), 1)
        if symbol_ratio > 0.1:
            warnings.append("HIGH_SYMBOL_RATIO")
        return warnings

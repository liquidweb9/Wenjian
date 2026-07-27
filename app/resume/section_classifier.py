"""Deterministic resume section classification."""

import re

from app.parsers.schemas import ResumeBlock

SECTION_ALIASES: dict[str, set[str]] = {
    "education": {
        "教育", "教育背景", "教育经历", "学历背景", "学历经历",
        "Education", "Academic Background", "Educational Background",
    },
    "experience": {
        "工作经历", "工作经验", "职业经历", "实习经历", "任职经历",
        "Experience", "Work Experience", "Work History",
        "Professional Experience", "Employment History", "Internship", "Internships",
    },
    "project": {
        "项目", "项目经历", "项目经验", "个人项目", "代表项目",
        "Project", "Projects", "Project Experience", "Selected Projects",
    },
    "research": {
        "科研经历", "研究经历", "论文", "论文发表",
        "Research", "Research Experience", "Publication", "Publications",
    },
    "competition": {
        "竞赛经历", "获奖经历", "荣誉", "荣誉奖项",
        "Award", "Awards", "Honor", "Honors", "Competitions",
    },
    "skills": {
        "专业技能", "技能", "技能清单", "技术栈", "核心能力",
        "Skill", "Skills", "Technical Skills", "Core Competencies", "Tech Stack",
    },
}


class SectionClassifier:
    """Assign every block to the closest preceding resume section."""

    def classify(self, blocks: list[ResumeBlock]) -> dict[int, str]:
        result: dict[int, str] = {}
        current_section = "unknown"

        for i, block in enumerate(blocks):
            detected = self._detect_section(block.text)
            if detected:
                current_section = detected
            result[i] = current_section

        return result

    def _detect_section(self, text: str) -> str | None:
        normalized = text.strip().strip("═━─—-=_*# ").rstrip(":：").strip()

        detected = self._match_heading(normalized)
        if detected:
            return detected

        # A PDF block can contain the heading plus the first entry. Only accept
        # its first non-empty line as a heading; do not substring-match prose.
        first_line = next(
            (line.strip() for line in text.splitlines() if line.strip()),
            "",
        )
        first_line = first_line.strip("═━─—-=_*# ").rstrip(":：").strip()
        if first_line and first_line != normalized:
            return self._match_heading(first_line)

        return None

    def _match_heading(self, text: str) -> str | None:
        for section, aliases in SECTION_ALIASES.items():
            if any(
                re.fullmatch(re.escape(alias), text, re.IGNORECASE)
                for alias in aliases
            ):
                return section
        return None

"""Tests for deterministic resume section classification."""

from app.parsers.schemas import ResumeBlock, ResumeDocument, SourceLocation
from app.resume.profile_builder import ProfileBuilder
from app.resume.section_classifier import SectionClassifier


def block(text: str, block_type: str = "paragraph") -> ResumeBlock:
    return ResumeBlock(
        block_id=f"block-{text}",
        text=text,
        block_type=block_type,  # type: ignore[arg-type]
        source_location=SourceLocation(),
    )


def test_chinese_sections_keep_following_entries_in_context():
    blocks = [
        block("张三"),
        block("教育经历", "heading"),
        block("北京大学 | 计算机科学"),
        block("工作经验", "heading"),
        block("示例科技 | 后端工程师"),
        block("项目经验", "heading"),
        block("智能检索平台"),
        block("技术栈", "heading"),
        block("Python, FastAPI"),
    ]

    sections = SectionClassifier().classify(blocks)

    assert sections[2] == "education"
    assert sections[4] == "experience"
    assert sections[6] == "project"
    assert sections[8] == "skills"


def test_decorated_and_english_headings_are_recognized():
    classifier = SectionClassifier()

    assert classifier._detect_section("—— 教育背景 ——") == "education"
    assert classifier._detect_section("EMPLOYMENT HISTORY") == "experience"
    assert classifier._detect_section("Selected Projects:") == "project"


def test_fallback_groups_bullets_under_one_project():
    blocks = [
        block("项目经历", "heading"),
        block("智能检索平台"),
        block("- 使用 FastAPI 构建服务", "bullet"),
        block("- 使用 PostgreSQL 存储数据", "bullet"),
        block("教育经历", "heading"),
        block("北京大学 | 计算机科学 | 2020-2024", "entry_header"),
    ]
    doc = ResumeDocument(
        resume_id="res-test",
        revision_id="rev-test",
        source_id="src-test",
        file_name="resume.txt",
        source_type="text",
        raw_text="",
        normalized_text="",
        blocks=blocks,
        extraction_method="plain_text",
        extraction_quality=1,
        parser_name="test",
        parser_version="1",
    )

    profile = ProfileBuilder()._build_fallback(doc)

    assert len(profile.projects) == 1
    assert profile.projects[0].title == "智能检索平台"
    assert len(profile.projects[0].bullets) == 2
    assert len(profile.education) == 1
    assert profile.education[0].title.startswith("北京大学")

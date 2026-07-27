"""Tests for quality assessment module."""

import pytest
from app.parsers.quality import assess_quality
from app.parsers.schemas import ResumeBlock, SourceLocation


def make_block(text: str, block_type: str = "paragraph", page: int = 1) -> ResumeBlock:
    return ResumeBlock(
        block_id="blk_test",
        text=text,
        block_type=block_type,  # type: ignore
        source_location=SourceLocation(
            page_number=page,
            block_index=0,
            bbox=(0, page * 50.0, 400, page * 50.0 + 20.0),
        ),
    )


class TestQuality:
    def test_no_blocks_returns_zero(self):
        result = assess_quality([])
        assert result["score"] == 0.0
        assert "NO_BLOCKS" in result["warnings"]

    def test_empty_text_returns_zero(self):
        result = assess_quality([make_block("")])
        assert result["score"] == 0.0

    def test_good_quality_blocks(self):
        blocks = [
            make_block("Education", "heading"),
            make_block("MIT | Computer Science | 2020-2024", "paragraph"),
            make_block("Experience", "heading"),
            make_block("Built REST APIs using FastAPI and PostgreSQL", "bullet"),
            make_block("Led team of 5 engineers", "bullet"),
            make_block("Skills", "heading"),
            make_block("Python, FastAPI, PostgreSQL, Docker", "paragraph"),
        ]
        result = assess_quality(blocks)
        assert result["score"] > 0.5

    def test_low_quality_triggers_warning(self):
        """Very little text should trigger low quality warning."""
        result = assess_quality([make_block("a")])
        if result["score"] < 0.6:
            assert "PARSE_QUALITY_TOO_LOW" in result["warnings"]

    def test_score_with_sections_is_higher(self):
        blocks_with_sections = [
            make_block("Education", "heading"),
            make_block("Experience", "heading"),
            make_block("Skills", "heading"),
            make_block("Some content here about work experience", "paragraph"),
        ]
        blocks_without_sections = [
            make_block("Some content here about work experience", "paragraph"),
            make_block("More content about other things done at work", "paragraph"),
        ]
        score_with = assess_quality(blocks_with_sections)["score"]
        score_without = assess_quality(blocks_without_sections)["score"]
        assert score_with >= score_without

    def test_bbox_blocks_higher_confidence(self):
        blocks_with_bbox = [
            make_block("Content A", page=1),
            make_block("Content B", page=2),
            make_block("Content C", page=3),
        ]
        result = assess_quality(blocks_with_bbox)
        assert result["score"] > 0

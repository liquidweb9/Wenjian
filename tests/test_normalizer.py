"""Tests for normalizer module."""

import pytest
from app.parsers.normalizer import Normalizer
from app.parsers.schemas import ResumeDocument, ResumeBlock, SourceLocation


def make_block(text: str, block_type: str = "paragraph") -> ResumeBlock:
    return ResumeBlock(
        block_id=f"blk_{hash(text) & 0xFFFF:04x}",
        text=text,
        raw_text=text,
        block_type=block_type,  # type: ignore
        source_location=SourceLocation(),
    )


def make_doc(blocks: list[ResumeBlock]) -> ResumeDocument:
    return ResumeDocument(
        resume_id="test",
        source_id="test_src",
        file_name="test.txt",
        source_type="text",  # type: ignore
        raw_text="\n".join(b.text for b in blocks),
        normalized_text="\n".join(b.text for b in blocks),
        blocks=blocks,
        extraction_method="plain_text",  # type: ignore
        extraction_quality=0.8,
        parser_name="test",
        parser_version="0.1",
    )


class TestNormalizer:
    def test_merge_bullets(self):
        normalizer = Normalizer()
        doc = make_doc([
            make_block("• Item 1", "bullet"),
            make_block("• Item 2", "bullet"),
        ])
        result = normalizer.normalize(doc)
        assert len(result.blocks) == 1
        assert "Item 1" in result.blocks[0].text
        assert "Item 2" in result.blocks[0].text

    def test_filter_page_numbers(self):
        normalizer = Normalizer()
        doc = make_doc([
            make_block("Page 1"),
            make_block("Real content here"),
        ])
        result = normalizer.normalize(doc)
        assert len(result.blocks) == 1
        assert "Real content" in result.blocks[0].text

    def test_filter_continued_markers(self):
        normalizer = Normalizer()
        doc = make_doc([
            make_block("(Continued)"),
            make_block("Real content"),
        ])
        result = normalizer.normalize(doc)
        assert len(result.blocks) == 1

    def test_filter_short_lines(self):
        normalizer = Normalizer()
        doc = make_doc([
            make_block("x"),
            make_block("Real content with enough text"),
        ])
        result = normalizer.normalize(doc)
        assert len(result.blocks) == 1

    def test_merge_broken_lines(self):
        """Architecture doc section 6.6: merge lines that are not complete sentences."""
        normalizer = Normalizer()
        doc = make_doc([
            make_block("Design and implement a", "paragraph"),
            make_block("microservices architecture", "paragraph"),
        ])
        result = normalizer.normalize(doc)
        merged_text = " ".join(b.text for b in result.blocks)
        assert "Design and implement a microservices architecture" in merged_text

    def test_no_merge_complete_sentence(self):
        """Don't merge if the previous line is a complete sentence."""
        normalizer = Normalizer()
        doc = make_doc([
            make_block("The system was built using FastAPI.", "paragraph"),
            make_block("It handled 10K requests per second.", "paragraph"),
        ])
        result = normalizer.normalize(doc)
        assert len(result.blocks) >= 2

    def test_no_merge_heading(self):
        """Don't merge if the next line is an all-caps heading."""
        normalizer = Normalizer()
        doc = make_doc([
            make_block("Some text about", "paragraph"),
            make_block("EXPERIENCE", "paragraph"),
        ])
        result = normalizer.normalize(doc)
        assert len(result.blocks) >= 2

    def test_no_merge_entry_header(self):
        """Don't merge if next line looks like a new entry header with date."""
        normalizer = Normalizer()
        doc = make_doc([
            make_block("Description of role", "paragraph"),
            make_block("2024-present | TechCorp | Senior Engineer", "paragraph"),
        ])
        result = normalizer.normalize(doc)
        assert len(result.blocks) >= 2

    def test_symbol_ratio_warning(self):
        normalizer = Normalizer()
        doc = make_doc([
            make_block("@#$%^&*===__+++{}"),
            make_block("||||\\\\\\\\~~~~"),
        ])
        result = normalizer.normalize(doc)
        assert any("HIGH_SYMBOL_RATIO" in w for w in result.extraction_warnings)

    def test_empty_blocks(self):
        normalizer = Normalizer()
        doc = make_doc([])
        result = normalizer.normalize(doc)
        assert result.blocks == []

"""Tests for parser modules: TextParser, FileIngress, and fixture-based parsing."""

from pathlib import Path

import pytest

from app.core.exceptions import AppError
from app.core.ids import new_id
from app.parsers.ingress import FileIngressValidator
from app.parsers.schemas import ParseInput
from app.parsers.text_parser import TextParser

FIXTURES = Path(__file__).parent / "fixtures" / "resumes"


def read_fixture(path: str) -> bytes:
    return (FIXTURES / path).read_bytes()


@pytest.mark.asyncio
class TestTextParser:
    async def test_simple_text(self):
        parser = TextParser()
        content = b"John Doe\nSoftware Engineer\n- Built APIs\n- Designed systems"
        result = await parser.parse(ParseInput(
            source_id=new_id(),
            file_name="test.txt",
            content=content,
        ))
        assert result.source_type == "text"
        assert result.blocks
        assert result.normalized_text

    async def test_chinese_text(self):
        parser = TextParser()
        content = "张三\n软件工程师\n• 项目经验\n• 技术栈".encode("utf-8")
        result = await parser.parse(ParseInput(
            source_id=new_id(),
            file_name="test.txt",
            content=content,
        ))
        assert result.extraction_quality > 0

    async def test_empty_text(self):
        parser = TextParser()
        result = await parser.parse(ParseInput(
            source_id=new_id(),
            file_name="empty.txt",
            content=b"",
        ))
        assert result.extraction_quality == 0

    async def test_bullet_detection(self):
        parser = TextParser()
        content = b"Skills:\n- Python\n- Rust\n- TypeScript"
        result = await parser.parse(ParseInput(
            source_id=new_id(),
            file_name="test.txt",
            content=content,
        ))
        bullets = [b for b in result.blocks if b.block_type == "bullet"]
        assert bullets

    async def test_chinese_fixture(self):
        parser = TextParser()
        content = read_fixture("text/chinese.txt")
        result = await parser.parse(ParseInput(
            source_id=new_id(),
            file_name="chinese.txt",
            content=content,
        ))
        assert result.extraction_quality > 0
        assert len(result.blocks) > 0

    async def test_english_fixture(self):
        parser = TextParser()
        content = read_fixture("text/english.txt")
        result = await parser.parse(ParseInput(
            source_id=new_id(),
            file_name="english.txt",
            content=content,
        ))
        assert result.extraction_quality > 0
        assert len(result.blocks) > 0

    async def test_malformed_fixture_quality(self):
        parser = TextParser()
        content = read_fixture("text/malformed.txt")
        result = await parser.parse(ParseInput(
            source_id=new_id(),
            file_name="malformed.txt",
            content=content,
        ))
        assert result.extraction_quality < 0.8  # Should be lower quality

    async def test_multiple_empty_lines(self):
        parser = TextParser()
        content = b"Section 1\n\n\n\nSection 2"
        result = await parser.parse(ParseInput(
            source_id=new_id(),
            file_name="test.txt",
            content=content,
        ))
        assert len(result.blocks) >= 2

    async def test_bullet_variants(self):
        parser = TextParser()
        content = b"Skills:\n- Python\n* Rust\n\xe2\x80\xa2 TypeScript\n\xc2\xb7 Go"
        result = await parser.parse(ParseInput(
            source_id=new_id(),
            file_name="test.txt",
            content=content,
        ))
        bullets = [b for b in result.blocks if b.block_type == "bullet"]
        assert len(bullets) >= 2

    async def test_semantic_resume_boundaries(self):
        parser = TextParser()
        content = """张三
后端工程师
教育经历
北京大学 | 计算机科学 | 2020-2024
工作经历
示例科技 | 后端工程师 | 2024-至今
- 负责 API 平台建设
项目经历
智能检索平台
- 使用 FastAPI 构建服务
- 使用 PostgreSQL 存储数据
""".encode()
        result = await parser.parse(ParseInput(
            source_id=new_id(),
            file_name="resume.txt",
            content=content,
        ))

        texts = [item.text for item in result.blocks]
        assert "教育经历" in texts
        assert "工作经历" in texts
        assert "项目经历" in texts
        assert next(
            item for item in result.blocks if item.text == "教育经历"
        ).block_type == "heading"
        assert next(
            item for item in result.blocks if "示例科技" in item.text
        ).block_type == "entry_header"
        assert len(
            [item for item in result.blocks if item.block_type == "bullet"]
        ) == 3


@pytest.mark.asyncio
class TestFileIngress:
    async def test_valid_pdf_header(self):
        validator = FileIngressValidator()
        content = b"%PDF-1.4\nsome content\n/Type /Page\n/Type /Page\n"
        sha = await validator.validate(content, "test.pdf", "application/pdf")
        assert sha

    async def test_empty_file(self):
        validator = FileIngressValidator()
        with pytest.raises(Exception):
            await validator.validate(b"", "empty.pdf", "application/pdf")

    async def test_encrypted_pdf(self):
        validator = FileIngressValidator()
        content = b"%PDF-1.4\n/Encrypt\nsome content\n/Type /Page"
        with pytest.raises(Exception) as exc:
            await validator.validate(content, "encrypted.pdf", "application/pdf")
        assert "encrypted" in str(exc.value).lower()

    async def test_size_limit(self):
        validator = FileIngressValidator()
        content = b"x" * (6 * 1024 * 1024)  # 6MB
        with pytest.raises(AppError) as exc:
            await validator.validate(content, "large.txt", "text/plain")
        assert exc.value.code == "RESUME_TOO_LARGE"

    async def test_unsupported_extension(self):
        validator = FileIngressValidator()
        with pytest.raises(AppError) as exc:
            await validator.validate(b"hello", "file.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        assert exc.value.code == "RESUME_UNSUPPORTED_TYPE"

    async def test_pdf_too_many_pages(self):
        validator = FileIngressValidator()
        pages = "/Type /Page\n" * 20
        content = f"%PDF-1.4\n{pages}".encode()
        with pytest.raises(AppError) as exc:
            await validator.validate(content, "large.pdf", "application/pdf")
        assert exc.value.code == "PDF_TOO_MANY_PAGES"

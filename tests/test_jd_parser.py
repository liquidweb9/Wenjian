"""Tests for JD parser."""

import pytest

from app.job_target.jd_parser import (
    JDParser,
    ParsedRequirement,
    JDParseResult,
    SourceSpan,
    MockLLMGateway,
)


class TestJDParserSchemas:
    """Test JD parser data schemas."""

    def test_parsed_requirement_valid(self):
        """Create valid parsed requirement."""
        req = ParsedRequirement(
            competency_code="backend.cache",
            title="Redis 缓存",
            description="使用 Redis 实现缓存",
            importance=0.85,
            expected_level=3,
            evidence_expectation=["能实现缓存模式", "能处理一致性"],
        )

        assert req.competency_code == "backend.cache"
        assert req.importance == 0.85
        assert req.expected_level == 3
        assert len(req.evidence_expectation) == 2

    def test_parsed_requirement_with_source_span(self):
        """Parsed requirement can include source span."""
        req = ParsedRequirement(
            competency_code="backend.cache",
            title="缓存",
            description="Redis 缓存",
            importance=0.8,
            expected_level=3,
            evidence_expectation=["证据1", "证据2"],
            source_span=SourceSpan(start=10, end=30, text="熟悉 Redis 缓存"),
        )

        assert req.source_span is not None
        assert req.source_span.start == 10
        assert req.source_span.end == 30

    def test_importance_out_of_range_rejected(self):
        """Reject importance outside 0.0-1.0."""
        with pytest.raises(Exception):  # Pydantic validation error
            ParsedRequirement(
                competency_code="backend.cache",
                title="缓存",
                description="Redis",
                importance=1.5,  # Invalid
                expected_level=3,
                evidence_expectation=["e1", "e2"],
            )

    def test_expected_level_out_of_range_rejected(self):
        """Reject expected level outside 1-5."""
        with pytest.raises(Exception):  # Pydantic validation error
            ParsedRequirement(
                competency_code="backend.cache",
                title="缓存",
                description="Redis",
                importance=0.8,
                expected_level=6,  # Invalid
                evidence_expectation=["e1", "e2"],
            )

    def test_evidence_expectation_minimum(self):
        """Evidence expectation requires at least 2 items."""
        with pytest.raises(Exception):  # Pydantic validation error
            ParsedRequirement(
                competency_code="backend.cache",
                title="缓存",
                description="Redis",
                importance=0.8,
                expected_level=3,
                evidence_expectation=["only_one"],  # Invalid
            )


class TestJDParseResult:
    """Test JD parse result schema."""

    def test_jd_parse_result_valid(self):
        """Create valid JD parse result."""
        result = JDParseResult(
            requirements=[
                ParsedRequirement(
                    competency_code="backend.cache",
                    title="缓存",
                    description="Redis",
                    importance=0.8,
                    expected_level=3,
                    evidence_expectation=["e1", "e2"],
                )
            ],
            inferred_level="mid",
            inferred_round="technical",
        )

        assert len(result.requirements) == 1
        assert result.inferred_level == "mid"
        assert result.inferred_round == "technical"


@pytest.mark.asyncio
class TestJDParser:
    """Test JD parser functionality."""

    async def test_parse_jd_with_mock_llm(self):
        """Parse JD using mock LLM."""
        parser = JDParser(llm=MockLLMGateway())

        jd_text = """
        后端工程师 - 中级

        职责：
        - 使用 Redis 实现缓存方案
        - 优化 MySQL 查询性能
        """

        result = await parser.parse_jd(jd_text)

        assert len(result.requirements) == 2
        assert result.inferred_level == "mid"
        assert result.inferred_round == "technical"

        # Check first requirement (Redis)
        redis_req = result.requirements[0]
        assert redis_req.competency_code == "backend.cache"
        assert "Redis" in redis_req.title
        assert len(redis_req.evidence_expectation) >= 2

    async def test_parse_empty_jd_raises_error(self):
        """Parsing empty JD raises ValueError."""
        parser = JDParser(llm=MockLLMGateway())

        with pytest.raises(ValueError, match="cannot be empty"):
            await parser.parse_jd("")

        with pytest.raises(ValueError, match="cannot be empty"):
            await parser.parse_jd("   ")

    def test_validate_requirement_valid(self):
        """Validate a valid requirement."""
        parser = JDParser(llm=MockLLMGateway())

        req = ParsedRequirement(
            competency_code="backend.cache",
            title="缓存",
            description="Redis 缓存实现",
            importance=0.85,
            expected_level=3,
            evidence_expectation=["能实现缓存模式", "能处理一致性问题"],
        )

        issues = parser.validate_requirement(req)
        assert len(issues) == 0

    def test_validate_requirement_invalid_code(self):
        """Validation catches invalid competency code."""
        parser = JDParser(llm=MockLLMGateway())

        req = ParsedRequirement(
            competency_code="invalid.code",
            title="测试",
            description="描述",
            importance=0.8,
            expected_level=3,
            evidence_expectation=["证据1", "证据2"],
        )

        issues = parser.validate_requirement(req)
        assert len(issues) > 0
        assert any("Unknown competency code" in issue for issue in issues)

    def test_validate_requirement_importance_out_of_range(self):
        """Validation catches importance out of range."""
        parser = JDParser(llm=MockLLMGateway())

        # Manually create invalid requirement (bypassing Pydantic)
        req = ParsedRequirement.model_construct(
            competency_code="backend.cache",
            title="测试",
            description="描述",
            importance=1.5,
            expected_level=3,
            evidence_expectation=["证据1", "证据2"],
        )

        issues = parser.validate_requirement(req)
        assert any("Importance must be 0.0-1.0" in issue for issue in issues)

    def test_validate_requirement_too_few_evidence(self):
        """Validation catches insufficient evidence expectations."""
        parser = JDParser(llm=MockLLMGateway())

        req = ParsedRequirement.model_construct(
            competency_code="backend.cache",
            title="测试",
            description="描述",
            importance=0.8,
            expected_level=3,
            evidence_expectation=["only_one"],
        )

        issues = parser.validate_requirement(req)
        assert any("at least 2 evidence" in issue for issue in issues)

    def test_validate_requirement_short_evidence(self):
        """Validation catches too-short evidence expectations."""
        parser = JDParser(llm=MockLLMGateway())

        req = ParsedRequirement(
            competency_code="backend.cache",
            title="测试",
            description="描述",
            importance=0.8,
            expected_level=3,
            evidence_expectation=["good evidence", "bad"],
        )

        issues = parser.validate_requirement(req)
        assert any("too short" in issue for issue in issues)


class TestPromptBuilding:
    """Test prompt construction."""

    def test_build_prompt_includes_competencies(self):
        """Prompt includes competency list."""
        parser = JDParser(llm=MockLLMGateway())

        prompt = parser._build_prompt("测试 JD 文本")

        assert "backend.cache" in prompt
        assert "agent.prompt_design" in prompt
        assert "测试 JD 文本" in prompt

    def test_build_prompt_includes_instructions(self):
        """Prompt includes extraction instructions."""
        parser = JDParser(llm=MockLLMGateway())

        prompt = parser._build_prompt("JD 文本")

        assert "Competency Code" in prompt
        assert "Importance" in prompt
        assert "Expected Level" in prompt
        assert "Evidence Expectation" in prompt

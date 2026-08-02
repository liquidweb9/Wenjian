"""Tests for Claim Mapper."""

import pytest

from app.planning.claim_mapper import (
    ClaimMapper,
    CompetencyMapping,
    RequirementMapping,
    ClaimMappingResult,
)


class TestCompetencyMapping:
    """Test competency mapping functionality."""

    def test_redis_claim_maps_to_cache(self):
        """Claim mentioning Redis maps to backend.cache."""
        mapper = ClaimMapper()

        claim_text = "我使用 Redis 实现了订单缓存，处理了缓存穿透和缓存雪崩问题"

        mappings = mapper.map_claim_to_competencies(
            claim_id="claim_1",
            claim_text=claim_text,
            min_strength=0.5,
        )

        # Should map to cache competency
        assert len(mappings) > 0
        cache_mapping = next((m for m in mappings if m.competency_code == "backend.cache"), None)
        assert cache_mapping is not None
        assert cache_mapping.mapping_strength >= 0.7  # Multiple keywords
        assert "Redis" in cache_mapping.mapping_reason or "redis" in cache_mapping.mapping_reason

    def test_java_api_claim_maps_to_multiple(self):
        """Claim about Java API development maps to multiple competencies."""
        mapper = ClaimMapper()

        claim_text = "负责开发 Java RESTful API，使用 MySQL 存储数据，Redis 缓存热点数据"

        mappings = mapper.map_claim_to_competencies(
            claim_id="claim_2",
            claim_text=claim_text,
            min_strength=0.5,
        )

        # Should map to multiple competencies
        assert len(mappings) >= 3

        comp_codes = {m.competency_code for m in mappings}
        assert "backend.language_runtime" in comp_codes  # Java
        assert "backend.api_protocol" in comp_codes      # RESTful
        assert "backend.cache" in comp_codes             # Redis
        assert "backend.database_modeling" in comp_codes # MySQL

    def test_weak_claim_filtered_by_min_strength(self):
        """Claims with weak keyword matches are filtered."""
        mapper = ClaimMapper()

        claim_text = "负责前端页面开发和UI设计"  # No backend keywords

        mappings = mapper.map_claim_to_competencies(
            claim_id="claim_3",
            claim_text=claim_text,
            min_strength=0.5,
        )

        # Should have no mappings (frontend not in our catalog)
        assert len(mappings) == 0

    def test_mapping_strength_increases_with_keywords(self):
        """More keyword matches result in higher strength."""
        mapper = ClaimMapper()

        # Single keyword
        single_kw = "使用 Redis 缓存"
        single_mappings = mapper.map_claim_to_competencies("c1", single_kw)
        single_strength = single_mappings[0].mapping_strength if single_mappings else 0.0

        # Multiple keywords
        multi_kw = "使用 Redis 缓存，处理缓存穿透、缓存击穿和缓存雪崩问题"
        multi_mappings = mapper.map_claim_to_competencies("c2", multi_kw)
        multi_strength = multi_mappings[0].mapping_strength if multi_mappings else 0.0

        assert multi_strength > single_strength

    def test_langgraph_claim_maps_to_agent_orchestration(self):
        """Claim about LangGraph maps to agent orchestration."""
        mapper = ClaimMapper()

        claim_text = "使用 LangGraph 构建 Agent 工作流，实现状态管理和 checkpoint 恢复"

        mappings = mapper.map_claim_to_competencies(
            claim_id="claim_4",
            claim_text=claim_text,
        )

        comp_codes = {m.competency_code for m in mappings}
        assert "agent.workflow_orchestration" in comp_codes  # LangGraph, workflow
        assert "agent.state_management" in comp_codes        # 状态管理, checkpoint

    def test_prompt_design_claim_maps_correctly(self):
        """Claim about prompt engineering maps to agent.prompt_design."""
        mapper = ClaimMapper()

        claim_text = "设计 few-shot prompt 和 chain-of-thought 提示词，优化 LLM 输出质量"

        mappings = mapper.map_claim_to_competencies(
            claim_id="claim_5",
            claim_text=claim_text,
        )

        # Should map to prompt_design
        assert any(m.competency_code == "agent.prompt_design" for m in mappings)

    def test_mappings_sorted_by_strength(self):
        """Competency mappings are sorted by strength descending."""
        mapper = ClaimMapper()

        claim_text = "Java 后端开发，RESTful API，MySQL 数据库设计，Redis 缓存，Kafka 消息队列"

        mappings = mapper.map_claim_to_competencies(
            claim_id="claim_6",
            claim_text=claim_text,
        )

        # Should be sorted descending
        strengths = [m.mapping_strength for m in mappings]
        assert strengths == sorted(strengths, reverse=True)


class TestRequirementMapping:
    """Test requirement mapping functionality."""

    def test_requirement_mapping_uses_competency_strength(self):
        """Requirement mapping derives relevance from competency mapping."""
        mapper = ClaimMapper()

        claim_text = "使用 Redis 实现缓存方案"

        # First get competency mappings
        comp_mappings = mapper.map_claim_to_competencies("claim_1", claim_text)

        # Define a requirement for Redis caching
        requirements = [
            {
                "requirement_id": "req_1",
                "competency_code": "backend.cache",
                "title": "Redis 缓存设计",
                "importance": 0.85,
                "expected_level": 3,
            }
        ]

        req_mappings = mapper.map_claim_to_requirements(
            claim_id="claim_1",
            claim_text=claim_text,
            requirements=requirements,
            competency_mappings=comp_mappings,
        )

        # Should map to the requirement
        assert len(req_mappings) == 1
        assert req_mappings[0].requirement_id == "req_1"
        assert req_mappings[0].competency_code == "backend.cache"
        assert req_mappings[0].relevance > 0.6

    def test_title_match_boosts_relevance(self):
        """Requirement title appearing in claim boosts relevance."""
        mapper = ClaimMapper()

        claim_text = "负责 Kafka 消息队列的架构设计和性能优化"

        comp_mappings = mapper.map_claim_to_competencies("claim_2", claim_text)

        # Requirement with matching title
        requirements = [
            {
                "requirement_id": "req_2",
                "competency_code": "backend.message_queue",
                "title": "Kafka",  # Appears in claim
                "importance": 0.8,
                "expected_level": 3,
            }
        ]

        req_mappings = mapper.map_claim_to_requirements(
            claim_id="claim_2",
            claim_text=claim_text,
            requirements=requirements,
            competency_mappings=comp_mappings,
        )

        assert len(req_mappings) == 1
        # Relevance should be boosted
        assert req_mappings[0].relevance >= 0.8
        assert "title keyword" in req_mappings[0].mapping_reason.lower()

    def test_no_mapping_for_unrelated_requirement(self):
        """Requirements with no competency match are not mapped."""
        mapper = ClaimMapper()

        claim_text = "使用 Redis 缓存"

        comp_mappings = mapper.map_claim_to_competencies("claim_3", claim_text)

        # Requirement for a different competency
        requirements = [
            {
                "requirement_id": "req_3",
                "competency_code": "agent.prompt_design",  # Unrelated
                "title": "Prompt 设计",
                "importance": 0.9,
                "expected_level": 3,
            }
        ]

        req_mappings = mapper.map_claim_to_requirements(
            claim_id="claim_3",
            claim_text=claim_text,
            requirements=requirements,
            competency_mappings=comp_mappings,
        )

        # No mapping expected
        assert len(req_mappings) == 0

    def test_multiple_requirements_mapped_correctly(self):
        """Claim maps to multiple requirements when relevant."""
        mapper = ClaimMapper()

        claim_text = "Java 后端开发，RESTful API 设计，MySQL 数据库优化"

        comp_mappings = mapper.map_claim_to_competencies("claim_4", claim_text)

        requirements = [
            {
                "requirement_id": "req_4a",
                "competency_code": "backend.language_runtime",
                "title": "Java/JVM",
                "importance": 0.9,
                "expected_level": 3,
            },
            {
                "requirement_id": "req_4b",
                "competency_code": "backend.api_protocol",
                "title": "RESTful API",
                "importance": 0.85,
                "expected_level": 3,
            },
            {
                "requirement_id": "req_4c",
                "competency_code": "backend.database_modeling",
                "title": "MySQL 优化",
                "importance": 0.8,
                "expected_level": 3,
            },
        ]

        req_mappings = mapper.map_claim_to_requirements(
            claim_id="claim_4",
            claim_text=claim_text,
            requirements=requirements,
            competency_mappings=comp_mappings,
        )

        # Should map to all three
        assert len(req_mappings) == 3
        req_ids = {m.requirement_id for m in req_mappings}
        assert req_ids == {"req_4a", "req_4b", "req_4c"}

    def test_coverage_level_estimated(self):
        """Coverage level is estimated based on relevance."""
        mapper = ClaimMapper()

        claim_text = "深度使用 Redis，实现缓存模式、一致性处理、分布式锁"

        comp_mappings = mapper.map_claim_to_competencies("claim_5", claim_text)

        requirements = [
            {
                "requirement_id": "req_5",
                "competency_code": "backend.cache",
                "title": "Redis 缓存",
                "importance": 0.9,
                "expected_level": 3,
            }
        ]

        req_mappings = mapper.map_claim_to_requirements(
            claim_id="claim_5",
            claim_text=claim_text,
            requirements=requirements,
            competency_mappings=comp_mappings,
        )

        assert len(req_mappings) == 1
        # High relevance should give higher coverage level
        assert req_mappings[0].coverage_level >= 1

    def test_min_relevance_filter(self):
        """Requirements below min_relevance are filtered."""
        mapper = ClaimMapper()

        claim_text = "提到了一点 Redis"  # Weak mention

        comp_mappings = mapper.map_claim_to_competencies("claim_6", claim_text, min_strength=0.4)

        requirements = [
            {
                "requirement_id": "req_6",
                "competency_code": "backend.cache",
                "title": "Redis 专家级应用",
                "importance": 1.0,
                "expected_level": 5,
            }
        ]

        # Use higher min_relevance
        req_mappings = mapper.map_claim_to_requirements(
            claim_id="claim_6",
            claim_text=claim_text,
            requirements=requirements,
            competency_mappings=comp_mappings,
            min_relevance=0.8,  # High threshold
        )

        # Weak claim should be filtered
        assert len(req_mappings) == 0


class TestMapClaim:
    """Test integrated map_claim function."""

    def test_map_claim_without_requirements(self):
        """map_claim works with only competency mapping."""
        mapper = ClaimMapper()

        result = mapper.map_claim(
            claim_id="claim_1",
            claim_text="使用 Redis 缓存和 Kafka 消息队列",
            requirements=None,
        )

        assert result.claim_id == "claim_1"
        assert len(result.competency_mappings) >= 2
        assert len(result.requirement_mappings) == 0  # No requirements provided

    def test_map_claim_with_requirements(self):
        """map_claim includes requirement mappings when provided."""
        mapper = ClaimMapper()

        requirements = [
            {
                "requirement_id": "req_1",
                "competency_code": "backend.cache",
                "title": "Redis",
                "importance": 0.85,
                "expected_level": 3,
            }
        ]

        result = mapper.map_claim(
            claim_id="claim_2",
            claim_text="使用 Redis 实现分布式缓存",
            requirements=requirements,
        )

        assert result.claim_id == "claim_2"
        assert len(result.competency_mappings) > 0
        assert len(result.requirement_mappings) > 0

    def test_map_claim_preserves_claim_text(self):
        """Result includes original claim text."""
        mapper = ClaimMapper()

        claim_text = "测试文本 - Redis 缓存"

        result = mapper.map_claim(
            claim_id="claim_3",
            claim_text=claim_text,
        )

        assert result.claim_text == claim_text

    def test_map_claim_respects_thresholds(self):
        """Custom min thresholds are respected."""
        mapper = ClaimMapper()

        claim_text = "略微提到 Redis"  # Weak

        # Strict thresholds
        result = mapper.map_claim(
            claim_id="claim_4",
            claim_text=claim_text,
            min_competency_strength=0.9,
        )

        # Should have no mappings due to high threshold
        assert len(result.competency_mappings) == 0


class TestKeywordMatchScoring:
    """Test keyword matching algorithm."""

    def test_no_match_returns_zero(self):
        """No keyword match returns 0.0."""
        mapper = ClaimMapper()

        score = mapper._calculate_keyword_match_score(
            text="前端开发 React 组件",
            keywords=["redis", "cache", "缓存"],
        )

        assert score == 0.0

    def test_single_match_returns_0_6(self):
        """Single keyword match returns 0.6."""
        mapper = ClaimMapper()

        score = mapper._calculate_keyword_match_score(
            text="使用 Redis 缓存",
            keywords=["redis", "cache", "memcached"],
        )

        assert score == 0.6

    def test_two_matches_returns_0_75(self):
        """Two keyword matches return 0.75."""
        mapper = ClaimMapper()

        score = mapper._calculate_keyword_match_score(
            text="使用 Redis 实现 cache 方案",
            keywords=["redis", "cache", "memcached"],
        )

        assert score == 0.75

    def test_three_plus_matches_returns_0_9(self):
        """Three or more keyword matches return 0.9."""
        mapper = ClaimMapper()

        score = mapper._calculate_keyword_match_score(
            text="Redis cache 缓存穿透 缓存雪崩",
            keywords=["redis", "cache", "缓存", "memcached"],
        )

        assert score == 0.9

    def test_case_insensitive_matching(self):
        """Keyword matching is case-insensitive."""
        mapper = ClaimMapper()

        score = mapper._calculate_keyword_match_score(
            text="REDIS Cache Implementation",
            keywords=["redis", "cache"],
        )

        assert score == 0.75  # Two matches

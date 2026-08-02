"""Tests for competency catalog."""

import pytest

from app.competencies import (
    ALL_COMPETENCIES,
    BACKEND_COMPETENCIES,
    AGENT_COMPETENCIES,
    get_competency_by_code,
    get_competencies_by_domain,
    get_all_competency_codes,
)


class TestCompetencyCatalog:
    """Test competency catalog structure and access."""

    def test_all_competencies_count(self):
        """Total competency count matches backend + agent."""
        assert len(ALL_COMPETENCIES) == len(BACKEND_COMPETENCIES) + len(AGENT_COMPETENCIES)
        assert len(ALL_COMPETENCIES) >= 20  # Phase 2 target: 20-25 competencies

    def test_backend_competencies_count(self):
        """Backend competencies are defined."""
        assert len(BACKEND_COMPETENCIES) == 13

        # Check all expected backend competencies exist
        backend_codes = {comp.code for comp in BACKEND_COMPETENCIES}
        expected = {
            "backend.language_runtime",
            "backend.api_protocol",
            "backend.database_modeling",
            "backend.transaction_consistency",
            "backend.cache",
            "backend.message_queue",
            "backend.concurrency",
            "backend.observability",
            "backend.failure_recovery",
            "backend.security",
            "backend.system_design",
            "backend.testing",
            "backend.delivery",
        }
        assert backend_codes == expected

    def test_agent_competencies_count(self):
        """Agent competencies are defined."""
        assert len(AGENT_COMPETENCIES) == 10

        # Check all expected agent competencies exist
        agent_codes = {comp.code for comp in AGENT_COMPETENCIES}
        expected = {
            "agent.prompt_design",
            "agent.structured_output",
            "agent.workflow_orchestration",
            "agent.state_management",
            "agent.tool_calling",
            "agent.rag_fundamentals",
            "agent.eval",
            "agent.guardrail",
            "agent.cost_latency",
            "agent.production_reliability",
        }
        assert agent_codes == expected

    def test_competency_codes_unique(self):
        """All competency codes are unique."""
        codes = [comp.code for comp in ALL_COMPETENCIES]
        assert len(codes) == len(set(codes))

    def test_competency_structure(self):
        """Each competency has required fields."""
        for comp in ALL_COMPETENCIES:
            assert comp.code
            assert comp.domain in ["backend", "agent"]
            assert comp.title
            assert comp.description
            assert len(comp.levels) == 5  # L1-L5

    def test_level_descriptors(self):
        """Level descriptors are properly structured."""
        for comp in ALL_COMPETENCIES:
            assert len(comp.levels) == 5

            for i, level in enumerate(comp.levels, start=1):
                assert level.level == i
                assert level.title
                assert level.behavior
                assert len(level.behavior) > 20  # Meaningful behavioral description


class TestCompetencyAccess:
    """Test competency catalog access functions."""

    def test_get_competency_by_code(self):
        """Get competency by code."""
        comp = get_competency_by_code("backend.cache")

        assert comp is not None
        assert comp.code == "backend.cache"
        assert comp.domain == "backend"
        assert comp.title == "Caching"
        assert "cache-aside" in comp.levels[1].behavior.lower()

    def test_get_competency_by_code_not_found(self):
        """Return None for non-existent code."""
        comp = get_competency_by_code("backend.nonexistent")
        assert comp is None

    def test_get_competencies_by_domain_backend(self):
        """Get all backend competencies."""
        backend = get_competencies_by_domain("backend")

        assert len(backend) == 13
        assert all(comp.domain == "backend" for comp in backend)

    def test_get_competencies_by_domain_agent(self):
        """Get all agent competencies."""
        agent = get_competencies_by_domain("agent")

        assert len(agent) == 10
        assert all(comp.domain == "agent" for comp in agent)

    def test_get_all_competency_codes(self):
        """Get list of all codes."""
        codes = get_all_competency_codes()

        assert len(codes) == 23
        assert "backend.cache" in codes
        assert "agent.prompt_design" in codes


class TestSpecificCompetencies:
    """Test specific competency definitions."""

    def test_backend_cache_competency(self):
        """Backend cache competency is well-defined."""
        comp = get_competency_by_code("backend.cache")

        assert comp.title == "Caching"
        assert "cache" in comp.description.lower()

        # Check level progression
        assert "memory" in comp.levels[0].behavior.lower()  # In-memory cache
        assert "cache-aside" in comp.levels[1].behavior.lower()
        assert "invalidation" in comp.levels[2].behavior.lower()
        assert "redis" in comp.levels[3].behavior.lower()
        assert "multi-layer" in comp.levels[4].behavior.lower()

    def test_agent_prompt_design_competency(self):
        """Agent prompt design competency is well-defined."""
        comp = get_competency_by_code("agent.prompt_design")

        assert comp.title == "Prompt Engineering"
        assert "prompt" in comp.description.lower()

        # Check level progression
        assert "basic prompts" in comp.levels[0].title.lower()
        assert "few-shot" in comp.levels[1].behavior.lower()
        assert "chain-of-thought" in comp.levels[2].behavior.lower()
        assert "eval" in comp.levels[3].behavior.lower()
        assert "registries" in comp.levels[4].behavior.lower()  # "registries" not "registry"

    def test_backend_database_modeling(self):
        """Database modeling has clear level progression."""
        comp = get_competency_by_code("backend.database_modeling")

        levels_text = " ".join(level.behavior.lower() for level in comp.levels)

        # L1: Basic SQL
        assert "select" in levels_text

        # L2: Schema design
        assert "schema" in levels_text
        assert "normalized" in levels_text

        # L3: Query optimization
        assert "index" in levels_text
        assert "n+1" in levels_text

        # L4: Advanced
        assert "denormalization" in levels_text or "partition" in levels_text

        # L5: Architecture
        assert "sharding" in levels_text

    def test_agent_rag_fundamentals(self):
        """RAG competency has clear progression."""
        comp = get_competency_by_code("agent.rag_fundamentals")

        levels_text = " ".join(level.behavior.lower() for level in comp.levels)

        assert "retrieval" in levels_text
        assert "embedding" in levels_text
        assert "semantic search" in levels_text
        assert "reranking" in levels_text or "hybrid" in levels_text

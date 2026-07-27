"""End-to-end integration tests for the resume interview pipeline."""

import pytest
from app.resume.service import ResumeService
from app.interview.graph import interview_graph
from app.interview.state import InterviewState
from app.core.ids import new_interview_id, new_thread_id


def _make_initial_state(
    claims: list[dict] | None = None,
    max_turns: int = 15,
    target_role: str = "Software Engineer",
) -> InterviewState:
    """Build a minimal InterviewState for testing graph nodes."""
    return {
        "interview_id": "",
        "thread_id": "",
        "resume_id": "res_test",
        "resume_revision_id": "rev_test",
        "target_role": target_role,
        "job_description": None,
        "interview_mode": "simulation",
        "resume_profile": {
            "candidate_name": "John Doe",
            "skills": ["Python", "FastAPI", "PostgreSQL"],
        },
        "resume_claims": claims or [
            {
                "claim_id": "clm_1",
                "entry_id": "entry_1",
                "claim_text": "Designed microservices architecture",
                "claim_type": "architecture",
                "technologies": ["FastAPI"],
                "expected_level": "design",
                "verification_points": [
                    {"point_id": "vp_1", "description": "Architecture design decisions", "category": "implementation", "target_depth": 5, "importance": 8},
                    {"point_id": "vp_2", "description": "Why microservices over monolith", "category": "tradeoff", "target_depth": 6, "importance": 7},
                ],
                "risk_flags": [],
                "priority": 80,
                "confidence": 0.8,
                "source_block_ids": ["blk_1"],
            }
        ],
        "interview_plan": {},
        "current_topic_id": None,
        "current_claim_id": None,
        "current_verification_point_id": None,
        "current_depth": 1,
        "current_question": None,
        "questions": [],
        "answers": [],
        "analyses": [],
        "evaluations": [],
        "claim_statuses": {},
        "contradictions": [],
        "evidence_items": [],
        "coverage": {},
        "ability_profile": {},
        "turn_count": 0,
        "max_turns": max_turns,
        "next_action": None,
        "stop_reason": None,
        "finished": False,
        "latest_coaching": None,
        "final_report": None,
    }


@pytest.mark.asyncio
class TestPipeline:
    async def test_parse_and_build_profile(self):
        """Test parsing text resume and building profile."""
        service = ResumeService()
        content = b"""John Doe
Software Engineer

Experience
TechCorp | Senior Engineer | 2020-present
- Designed and implemented microservices architecture
- Built REST APIs using FastAPI and PostgreSQL
- Led team of 5 engineers

Skills: Python, FastAPI, PostgreSQL, Docker"""
        doc = await service.parse_resume(content, "resume.txt", "text/plain")
        assert doc.source_type == "text"
        assert doc.extraction_quality > 0
        assert len(doc.blocks) > 0
        assert "John Doe" in doc.raw_text

    async def test_graph_initialization(self):
        """Test interview graph builds and initializes correctly."""
        state = _make_initial_state()
        config = {"configurable": {"thread_id": "test_thread_init"}}
        result = await interview_graph.ainvoke(state, config)
        assert result is not None
        assert result.get("interview_id", "")
        assert result.get("thread_id", "")
        assert result.get("turn_count") == 0

    async def test_preserves_pre_set_ids(self):
        """Test that pre-set interview_id and thread_id are preserved by initialize_node."""
        interview_id = new_interview_id()
        thread_id = new_thread_id()
        state = _make_initial_state()
        state["interview_id"] = interview_id
        state["thread_id"] = thread_id
        config = {"configurable": {"thread_id": thread_id}}
        result = await interview_graph.ainvoke(state, config)
        assert result.get("interview_id") == interview_id
        assert result.get("thread_id") == thread_id

    async def test_graph_with_multiple_claims(self):
        """Test graph with multiple resume claims."""
        claims = [
            {
                "claim_id": "clm_1",
                "claim_text": "Built microservices architecture",
                "claim_type": "architecture",
                "technologies": ["FastAPI", "Docker"],
                "expected_level": "design",
                "verification_points": [
                    {"point_id": "vp_1a", "description": "Architecture pattern", "category": "implementation", "target_depth": 5, "importance": 8},
                ],
                "risk_flags": [],
                "priority": 80,
                "confidence": 0.8,
                "source_block_ids": ["blk_1"],
            },
            {
                "claim_id": "clm_2",
                "claim_text": "Optimized database queries for 40% improvement",
                "claim_type": "performance",
                "technologies": ["PostgreSQL"],
                "expected_level": "implement",
                "verification_points": [
                    {"point_id": "vp_2a", "description": "Query optimization technique", "category": "implementation", "target_depth": 4, "importance": 6},
                ],
                "risk_flags": ["UNVERIFIED_IMPROVEMENT"],
                "priority": 60,
                "confidence": 0.6,
                "source_block_ids": ["blk_2"],
            },
        ]
        state = _make_initial_state(claims=claims)
        config = {"configurable": {"thread_id": "test_thread_multi"}}
        result = await interview_graph.ainvoke(state, config)
        assert result is not None
        # Should have initialized claim_statuses for both claims
        assert "clm_1" in result.get("claim_statuses", {})
        assert "clm_2" in result.get("claim_statuses", {})

    async def test_graph_with_high_risk_claims(self):
        """Test graph handles claims with risk flags."""
        claims = [{
            "claim_id": "clm_risk",
            "claim_text": "Led team to improve system performance by 200%",
            "claim_type": "result",
            "technologies": ["Kubernetes"],
            "expected_level": "use",
            "verification_points": [
                {"point_id": "vp_r1", "description": "How was performance measured", "category": "result", "target_depth": 3, "importance": 5},
            ],
            "risk_flags": ["MISSING_METRICS", "UNCLEAR_OWNERSHIP"],
            "priority": 30,
            "confidence": 0.4,
            "source_block_ids": ["blk_r"],
        }]
        state = _make_initial_state(claims=claims, target_role="DevOps Engineer")
        config = {"configurable": {"thread_id": "test_thread_risk"}}
        result = await interview_graph.ainvoke(state, config)
        assert result is not None

    async def test_graph_max_turns_enforced(self):
        """Test max_turns is stored in state."""
        state = _make_initial_state(max_turns=3)
        config = {"configurable": {"thread_id": "test_thread_max"}}
        result = await interview_graph.ainvoke(state, config)
        assert result.get("max_turns") == 3

    async def test_profile_builder_fallback(self):
        """Test profile builder produces valid output even with minimal data."""
        from app.parsers.schemas import ResumeDocument, ResumeBlock, SourceLocation
        from app.resume.profile_builder import ProfileBuilder

        doc = ResumeDocument(
            resume_id="res_test",
            source_id="src_test",
            file_name="test.txt",
            source_type="text",  # type: ignore
            raw_text="Minimal",
            normalized_text="Minimal",
            blocks=[ResumeBlock(
                block_id="blk_1",
                text="John Doe\nSoftware Engineer",
                block_type="paragraph",  # type: ignore
                source_location=SourceLocation(),
            )],
            extraction_method="plain_text",  # type: ignore
            extraction_quality=0.5,
            parser_name="test",
            parser_version="0.1",
        )
        builder = ProfileBuilder()
        profile = await builder.build(doc)
        assert profile.resume_id == "res_test"
        assert profile.extraction_confidence >= 0

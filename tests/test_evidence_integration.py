"""Tests for Evidence Engine 2.0 integration with interview graph.

Tests the integration of state machine, span extractor, and contradiction detector
into the update_evidence node.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.interview.nodes.update_evidence import update_evidence_node
from app.interview.state import InterviewState
from app.evidence import (
    EvidenceState,
    EvidenceSpan,
    ExtractionResult,
    Contradiction,
    DetectionResult,
)


@pytest.fixture
def mock_session():
    """Mock database session."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def mock_evidence_repo():
    """Mock evidence repository."""
    repo = MagicMock()
    repo.get_verification_point = AsyncMock(return_value=None)
    repo.add_verification_point = AsyncMock()
    repo.add_evidence = AsyncMock()
    repo.add_transition = AsyncMock()
    repo.add_contradiction = AsyncMock()
    repo.update_verification_point_state = AsyncMock()
    return repo


@pytest.fixture
def base_interview_state() -> InterviewState:
    """Base interview state for testing."""
    return {
        "interview_id": "int_001",
        "thread_id": "thread_001",
        "resume_id": "res_001",
        "resume_revision_id": "rev_001",
        "target_role": "Backend Engineer",
        "job_description": None,
        "interview_mode": "standard",
        "resume_profile": {},
        "resume_claims": [
            {
                "claim_id": "claim_001",
                "verification_points": [
                    {
                        "verification_point_id": "vp_001",
                        "competency_code": "backend.cache",
                        "requirement_id": None,
                        "aspect": "Redis implementation",
                        "expected_evidence": {"technical_details": True},
                    }
                ],
            }
        ],
        "interview_plan": {"topics": []},
        "current_topic_id": "topic_001",
        "current_claim_id": "claim_001",
        "current_verification_point_id": "vp_001",
        "current_depth": 1,
        "current_question": {
            "question_id": "q_001",
            "question_text": "Tell me about your Redis implementation",
            "verification_point_id": "vp_001",
        },
        "questions": [
            {
                "question_id": "q_001",
                "question_text": "Tell me about your Redis implementation",
                "verification_point_id": "vp_001",
            }
        ],
        "answers": [
            {
                "answer_id": "ans_001",
                "question_id": "q_001",
                "answer_text": "I implemented Redis caching for user sessions with 1000 QPS throughput.",
            }
        ],
        "analyses": [
            {
                "addressed_expected_points": ["technical_details"],
                "missing_expected_points": [],
                "possible_contradictions": [],
            }
        ],
        "evaluations": [
            {
                "evaluation_id": "eval_001",
                "evaluation_confidence": 0.85,
            }
        ],
        "claim_statuses": {
            "claim_001": {
                "status": "IN_PROGRESS",
                "verified_points": [],
                "partial_points": [],
                "missing_points": [],
                "confidence": 0.0,
            }
        },
        "contradictions": [],
        "evidence_items": [],
        "coverage": {},
        "ability_profile": {},
        "turn_count": 1,
        "max_turns": 20,
        "next_action": None,
        "stop_reason": None,
        "finished": False,
        "latest_coaching": None,
        "final_report": None,
    }


class TestEvidenceIntegration:
    """Test Evidence Engine 2.0 integration."""

    @pytest.mark.asyncio
    async def test_creates_verification_point_if_not_exists(
        self, base_interview_state, mock_session, mock_evidence_repo
    ):
        """Test that verification point is created if it doesn't exist."""
        with patch("app.interview.nodes.update_evidence.async_session_factory") as mock_factory, \
             patch("app.interview.nodes.update_evidence.EvidenceRepository") as mock_repo_class, \
             patch("app.interview.nodes.update_evidence.EvidenceSpanExtractor") as mock_span_class, \
             patch("app.interview.nodes.update_evidence.ContradictionDetector") as mock_contradiction_class, \
             patch("app.interview.nodes.update_evidence.AgnesGateway"):

            # Setup mocks
            mock_factory.return_value.__aenter__.return_value = mock_session
            mock_factory.return_value.__aexit__.return_value = AsyncMock()
            mock_repo_class.return_value = mock_evidence_repo

            # Mock span extractor
            mock_span_extractor = mock_span_class.return_value
            mock_span_extractor.extract_spans = AsyncMock(
                return_value=ExtractionResult(
                    spans=[
                        EvidenceSpan(
                            answer_id="ans_001",
                            start=0,
                            end=50,
                            text="I implemented Redis caching for user sessions",
                            quote_hash="sha256:abc123",
                            evidence_type="DIRECT",
                        )
                    ],
                    summary="Redis implementation described",
                    confidence=0.85,
                    extracted_by="MODEL",
                )
            )

            # Mock contradiction detector
            mock_contradiction_detector = mock_contradiction_class.return_value
            mock_contradiction_detector.detect_contradictions = AsyncMock(
                return_value=DetectionResult(
                    contradictions=[],
                    overall_consistency="CONSISTENT",
                    confidence=0.9,
                )
            )

            # Execute
            result = await update_evidence_node(base_interview_state)

            # Verify verification point was created
            assert mock_evidence_repo.add_verification_point.called
            vp_call = mock_evidence_repo.add_verification_point.call_args[0][0]
            assert vp_call.verification_point_id == "vp_001"
            assert vp_call.claim_id == "claim_001"
            assert vp_call.aspect == "Redis implementation"
            assert vp_call.current_state == EvidenceState.UNSEEN.value

    @pytest.mark.asyncio
    async def test_extracts_evidence_spans_from_answer(
        self, base_interview_state, mock_session, mock_evidence_repo
    ):
        """Test that evidence spans are extracted from the answer."""
        with patch("app.interview.nodes.update_evidence.async_session_factory") as mock_factory, \
             patch("app.interview.nodes.update_evidence.EvidenceRepository") as mock_repo_class, \
             patch("app.interview.nodes.update_evidence.EvidenceSpanExtractor") as mock_span_class, \
             patch("app.interview.nodes.update_evidence.ContradictionDetector") as mock_contradiction_class, \
             patch("app.interview.nodes.update_evidence.AgnesGateway"):

            mock_factory.return_value.__aenter__.return_value = mock_session
            mock_factory.return_value.__aexit__.return_value = AsyncMock()
            mock_repo_class.return_value = mock_evidence_repo

            mock_span_extractor = mock_span_class.return_value
            mock_span_extractor.extract_spans = AsyncMock(
                return_value=ExtractionResult(
                    spans=[
                        EvidenceSpan(
                            answer_id="ans_001",
                            start=0,
                            end=50,
                            text="I implemented Redis caching",
                            quote_hash="sha256:abc123",
                            evidence_type="DIRECT",
                        )
                    ],
                    summary="Redis details",
                    confidence=0.85,
                    extracted_by="MODEL",
                )
            )

            mock_contradiction_detector = mock_contradiction_class.return_value
            mock_contradiction_detector.detect_contradictions = AsyncMock(
                return_value=DetectionResult(
                    contradictions=[],
                    overall_consistency="CONSISTENT",
                    confidence=0.9,
                )
            )

            await update_evidence_node(base_interview_state)

            # Verify span extractor was called
            assert mock_span_extractor.extract_spans.called
            call_args = mock_span_extractor.extract_spans.call_args
            assert call_args[1]["answer_text"] == "I implemented Redis caching for user sessions with 1000 QPS throughput."
            assert call_args[1]["answer_id"] == "ans_001"

            # Verify evidence was added
            assert mock_evidence_repo.add_evidence.called

    @pytest.mark.asyncio
    async def test_detects_contradictions(
        self, base_interview_state, mock_session, mock_evidence_repo
    ):
        """Test that contradictions are detected between answers."""
        # Add a second answer with contradiction
        base_interview_state["answers"].append({
            "answer_id": "ans_002",
            "question_id": "q_002",
            "answer_text": "We actually used Memcached, not Redis.",
        })
        base_interview_state["questions"].append({
            "question_id": "q_002",
            "question_text": "What caching solution did you use?",
            "verification_point_id": "vp_001",
        })
        base_interview_state["analyses"].append({
            "addressed_expected_points": ["technical_details"],
            "missing_expected_points": [],
            "possible_contradictions": ["cache_technology"],
        })
        base_interview_state["evaluations"].append({
            "evaluation_id": "eval_002",
            "evaluation_confidence": 0.75,
        })

        with patch("app.interview.nodes.update_evidence.async_session_factory") as mock_factory, \
             patch("app.interview.nodes.update_evidence.EvidenceRepository") as mock_repo_class, \
             patch("app.interview.nodes.update_evidence.EvidenceSpanExtractor") as mock_span_class, \
             patch("app.interview.nodes.update_evidence.ContradictionDetector") as mock_contradiction_class, \
             patch("app.interview.nodes.update_evidence.AgnesGateway"):

            mock_factory.return_value.__aenter__.return_value = mock_session
            mock_factory.return_value.__aexit__.return_value = AsyncMock()
            mock_repo_class.return_value = mock_evidence_repo

            mock_span_extractor = mock_span_class.return_value
            mock_span_extractor.extract_spans = AsyncMock(
                return_value=ExtractionResult(
                    spans=[],
                    summary="No evidence",
                    confidence=0.1,
                    extracted_by="MODEL",
                )
            )

            mock_contradiction_detector = mock_contradiction_class.return_value
            mock_contradiction_detector.detect_contradictions = AsyncMock(
                return_value=DetectionResult(
                    contradictions=[
                        Contradiction(
                            contradiction_id="ct_001",
                            verification_point_id="vp_001",
                            conflicting_answers=[
                                {"answer_id": "ans_001", "text": "Redis"},
                                {"answer_id": "ans_002", "text": "Memcached"},
                            ],
                            contradiction_type="FACTUAL",
                            severity="HIGH",
                            description="Cache technology contradicted",
                            clarification_question="Which caching solution did you actually use?",
                        )
                    ],
                    overall_consistency="CONTRADICTORY",
                    confidence=0.9,
                )
            )

            result = await update_evidence_node(base_interview_state)

            # Verify contradiction detector was called
            assert mock_contradiction_detector.detect_contradictions.called

            # Verify contradiction was added to database
            assert mock_evidence_repo.add_contradiction.called

            # Verify contradiction was added to state
            assert "contradictions" in result
            assert len(result["contradictions"]) > 0

    @pytest.mark.asyncio
    async def test_updates_verification_point_with_evidence(
        self, base_interview_state, mock_session, mock_evidence_repo
    ):
        """Test that verification point is updated with evidence data."""
        # Set up mock to return existing VP
        from app.persistence.models import VerificationPoint
        mock_vp = VerificationPoint(
            verification_point_id="vp_001",
            claim_id="claim_001",
            competency_code="backend.cache",
            requirement_id=None,
            aspect="Redis implementation",
            expected_evidence={"technical_details": True},
            current_state="ADDRESSED",
            strength=None,
            confidence=None,
            unresolved_reason_codes=None,
        )
        mock_evidence_repo.get_verification_point = AsyncMock(return_value=mock_vp)

        with patch("app.interview.nodes.update_evidence.async_session_factory") as mock_factory, \
             patch("app.interview.nodes.update_evidence.EvidenceRepository") as mock_repo_class, \
             patch("app.interview.nodes.update_evidence.EvidenceSpanExtractor") as mock_span_class, \
             patch("app.interview.nodes.update_evidence.ContradictionDetector") as mock_contradiction_class, \
             patch("app.interview.nodes.update_evidence.AgnesGateway"):

            mock_factory.return_value.__aenter__.return_value = mock_session
            mock_factory.return_value.__aexit__.return_value = AsyncMock()
            mock_repo_class.return_value = mock_evidence_repo

            mock_span_extractor = mock_span_class.return_value
            mock_span_extractor.extract_spans = AsyncMock(
                return_value=ExtractionResult(
                    spans=[
                        EvidenceSpan(
                            answer_id="ans_001",
                            start=0,
                            end=50,
                            text="I implemented Redis",
                            quote_hash="sha256:abc",
                            evidence_type="DIRECT",
                        )
                    ],
                    summary="Evidence found",
                    confidence=0.65,
                    extracted_by="MODEL",
                )
            )

            mock_contradiction_detector = mock_contradiction_class.return_value
            mock_contradiction_detector.detect_contradictions = AsyncMock(
                return_value=DetectionResult(
                    contradictions=[],
                    overall_consistency="CONSISTENT",
                    confidence=0.9,
                )
            )

            result = await update_evidence_node(base_interview_state)

            # Verify evidence was added to database
            assert mock_evidence_repo.add_evidence.called

            # Verify Phase 1 outputs still work
            assert "claim_statuses" in result
            assert "evidence_items" in result
            assert len(result["evidence_items"]) > 0

    @pytest.mark.asyncio
    async def test_phase1_compatibility_maintained(
        self, base_interview_state, mock_session, mock_evidence_repo
    ):
        """Test that Phase 1 claim status updates still work."""
        with patch("app.interview.nodes.update_evidence.async_session_factory") as mock_factory, \
             patch("app.interview.nodes.update_evidence.EvidenceRepository") as mock_repo_class, \
             patch("app.interview.nodes.update_evidence.EvidenceSpanExtractor") as mock_span_class, \
             patch("app.interview.nodes.update_evidence.ContradictionDetector") as mock_contradiction_class, \
             patch("app.interview.nodes.update_evidence.AgnesGateway"):

            mock_factory.return_value.__aenter__.return_value = mock_session
            mock_factory.return_value.__aexit__.return_value = AsyncMock()
            mock_repo_class.return_value = mock_evidence_repo

            mock_span_extractor = mock_span_class.return_value
            mock_span_extractor.extract_spans = AsyncMock(
                return_value=ExtractionResult(
                    spans=[],
                    summary="",
                    confidence=0.0,
                    extracted_by="MODEL",
                )
            )

            mock_contradiction_detector = mock_contradiction_class.return_value
            mock_contradiction_detector.detect_contradictions = AsyncMock(
                return_value=DetectionResult(
                    contradictions=[],
                    overall_consistency="CONSISTENT",
                    confidence=0.0,
                )
            )

            result = await update_evidence_node(base_interview_state)

            # Verify Phase 1 outputs are present
            assert "claim_statuses" in result
            assert "evidence_items" in result
            assert "coverage" in result

            # Verify claim status was updated (Phase 1 logic)
            assert result["claim_statuses"]["claim_001"]["verified_points"] == ["vp_001"]

    @pytest.mark.asyncio
    async def test_handles_missing_current_claim(self, base_interview_state):
        """Test that node returns empty dict if no current claim."""
        state_no_claim = base_interview_state.copy()
        state_no_claim["current_claim_id"] = None

        result = await update_evidence_node(state_no_claim)

        assert result == {}

    @pytest.mark.asyncio
    async def test_handles_no_evaluations(self, base_interview_state):
        """Test that node returns empty dict if no evaluations."""
        state_no_eval = base_interview_state.copy()
        state_no_eval["evaluations"] = []

        result = await update_evidence_node(state_no_eval)

        assert result == {}

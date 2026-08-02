"""Tests for Evidence Engine database models."""

import pytest
from datetime import datetime, timezone

from app.persistence.models import (
    VerificationPoint,
    Evidence,
    EvidenceTransition,
    Contradiction,
)


class TestVerificationPointModel:
    """Test VerificationPoint model structure."""

    def test_verification_point_creation(self):
        """Create a verification point."""
        vp = VerificationPoint(
            verification_point_id="vp_123",
            claim_id="claim_456",
            competency_code="backend.cache",
            requirement_id="req_789",
            aspect="Redis caching implementation",
            expected_evidence={"types": ["DIRECT", "INDIRECT"]},
            current_state="UNSEEN",
            strength=None,
            confidence=None,
        )

        assert vp.verification_point_id == "vp_123"
        assert vp.claim_id == "claim_456"
        assert vp.competency_code == "backend.cache"
        assert vp.current_state == "UNSEEN"
        assert vp.strength is None

    def test_verification_point_defaults(self):
        """Verification point has correct defaults."""
        vp = VerificationPoint(
            verification_point_id="vp_123",
            claim_id="claim_456",
            competency_code="backend.cache",
            aspect="Redis caching",
            expected_evidence={},
            current_state="UNSEEN",  # Must be explicit in Python object
        )

        assert vp.current_state == "UNSEEN"
        assert vp.requirement_id is None
        assert vp.strength is None
        assert vp.confidence is None

    def test_verification_point_state_update(self):
        """Verification point state can be updated."""
        vp = VerificationPoint(
            verification_point_id="vp_123",
            claim_id="claim_456",
            competency_code="backend.cache",
            aspect="Redis caching",
            expected_evidence={},
            current_state="UNSEEN",
        )

        # Simulate state transition
        vp.current_state = "ADDRESSED"
        assert vp.current_state == "ADDRESSED"

        vp.current_state = "VERIFIED"
        vp.strength = 0.85
        vp.confidence = "HIGH"
        assert vp.current_state == "VERIFIED"
        assert vp.strength == 0.85
        assert vp.confidence == "HIGH"


class TestEvidenceModel:
    """Test Evidence model structure."""

    def test_evidence_creation(self):
        """Create an evidence record."""
        evidence = Evidence(
            evidence_id="ev_123",
            verification_point_id="vp_456",
            interview_id="int_789",
            answer_id="ans_012",
            evidence_type="DIRECT",
            spans=[
                {
                    "start": 10,
                    "end": 50,
                    "text": "I implemented Redis caching for user sessions",
                    "quote_hash": "sha256:abc123",
                }
            ],
            summary="Candidate describes Redis implementation",
            extracted_by="MODEL",
            confidence=0.9,
        )

        assert evidence.evidence_id == "ev_123"
        assert evidence.verification_point_id == "vp_456"
        assert evidence.evidence_type == "DIRECT"
        assert len(evidence.spans) == 1
        assert evidence.spans[0]["start"] == 10
        assert evidence.confidence == 0.9

    def test_evidence_multiple_spans(self):
        """Evidence can have multiple spans."""
        evidence = Evidence(
            evidence_id="ev_123",
            verification_point_id="vp_456",
            interview_id="int_789",
            answer_id="ans_012",
            evidence_type="INDIRECT",
            spans=[
                {"start": 10, "end": 30, "text": "Redis cluster", "quote_hash": "h1"},
                {"start": 50, "end": 80, "text": "cache invalidation", "quote_hash": "h2"},
            ],
            summary="Multiple mentions of caching",
            extracted_by="MODEL",
            confidence=0.75,
        )

        assert len(evidence.spans) == 2
        assert evidence.spans[0]["text"] == "Redis cluster"
        assert evidence.spans[1]["text"] == "cache invalidation"


class TestEvidenceTransitionModel:
    """Test EvidenceTransition model structure."""

    def test_transition_creation(self):
        """Create an evidence transition."""
        transition = EvidenceTransition(
            transition_id="tr_123",
            verification_point_id="vp_456",
            interview_id="int_789",
            from_state="UNSEEN",
            to_state="ADDRESSED",
            reason_code="FIRST_INQUIRY",
            answer_id=None,
            policy_version="v1.0",
            prompt_version=None,
            model_name=None,
        )

        assert transition.transition_id == "tr_123"
        assert transition.from_state == "UNSEEN"
        assert transition.to_state == "ADDRESSED"
        assert transition.reason_code == "FIRST_INQUIRY"
        assert transition.policy_version == "v1.0"

    def test_transition_with_evidence_spans(self):
        """Transition can include evidence span snapshot."""
        transition = EvidenceTransition(
            transition_id="tr_123",
            verification_point_id="vp_456",
            interview_id="int_789",
            from_state="PARTIALLY_SUPPORTED",
            to_state="VERIFIED",
            reason_code="EVIDENCE_SPANS_FOUND",
            answer_id="ans_012",
            evidence_spans=[
                {"start": 10, "end": 50, "text": "Redis implementation"}
            ],
            policy_version="v1.0",
            prompt_version="v2.1",
            model_name="gpt-4o",
        )

        assert transition.to_state == "VERIFIED"
        assert transition.reason_code == "EVIDENCE_SPANS_FOUND"
        assert transition.evidence_spans is not None
        assert len(transition.evidence_spans) == 1
        assert transition.prompt_version == "v2.1"
        assert transition.model_name == "gpt-4o"


class TestContradictionModel:
    """Test Contradiction model structure."""

    def test_contradiction_creation(self):
        """Create a contradiction record."""
        contradiction = Contradiction(
            contradiction_id="con_123",
            verification_point_id="vp_456",
            interview_id="int_789",
            claim_id="claim_012",
            conflicting_answers=[
                {
                    "answer_id": "ans_001",
                    "quote": "I led a team of 5",
                    "position": 100,
                },
                {
                    "answer_id": "ans_002",
                    "quote": "I worked alone on this project",
                    "position": 250,
                },
            ],
            contradiction_type="ROLE",
            severity="MEDIUM",
            description="Conflicting information about team involvement",
            clarification_question="Can you clarify your role and team structure?",
            resolution_status="UNRESOLVED",
        )

        assert contradiction.contradiction_id == "con_123"
        assert contradiction.contradiction_type == "ROLE"
        assert contradiction.severity == "MEDIUM"
        assert len(contradiction.conflicting_answers) == 2
        assert contradiction.resolution_status == "UNRESOLVED"

    def test_contradiction_defaults(self):
        """Contradiction has correct defaults."""
        contradiction = Contradiction(
            contradiction_id="con_123",
            verification_point_id="vp_456",
            interview_id="int_789",
            claim_id="claim_012",
            conflicting_answers=[],
            contradiction_type="FACTUAL",
            severity="LOW",
            description="Minor inconsistency",
            resolution_status="UNRESOLVED",  # Must be explicit in Python object
        )

        assert contradiction.resolution_status == "UNRESOLVED"
        assert contradiction.clarification_question is None
        assert contradiction.resolution_answer_id is None
        assert contradiction.resolved_at is None

    def test_contradiction_resolution(self):
        """Contradiction can be resolved."""
        contradiction = Contradiction(
            contradiction_id="con_123",
            verification_point_id="vp_456",
            interview_id="int_789",
            claim_id="claim_012",
            conflicting_answers=[],
            contradiction_type="TIMELINE",
            severity="HIGH",
            description="Timeline inconsistency",
            resolution_status="UNRESOLVED",
        )

        # Simulate resolution
        contradiction.resolution_status = "CLARIFIED"
        contradiction.resolution_answer_id = "ans_999"
        contradiction.resolved_at = datetime.now(timezone.utc)

        assert contradiction.resolution_status == "CLARIFIED"
        assert contradiction.resolution_answer_id == "ans_999"
        assert contradiction.resolved_at is not None


class TestContradictionTypes:
    """Test contradiction type values."""

    def test_factual_contradiction(self):
        """FACTUAL contradiction type."""
        c = Contradiction(
            contradiction_id="c1",
            verification_point_id="vp1",
            interview_id="i1",
            claim_id="cl1",
            conflicting_answers=[],
            contradiction_type="FACTUAL",
            severity="HIGH",
            description="Factual mismatch",
        )
        assert c.contradiction_type == "FACTUAL"

    def test_timeline_contradiction(self):
        """TIMELINE contradiction type."""
        c = Contradiction(
            contradiction_id="c1",
            verification_point_id="vp1",
            interview_id="i1",
            claim_id="cl1",
            conflicting_answers=[],
            contradiction_type="TIMELINE",
            severity="MEDIUM",
            description="Timeline inconsistency",
        )
        assert c.contradiction_type == "TIMELINE"

    def test_role_contradiction(self):
        """ROLE contradiction type."""
        c = Contradiction(
            contradiction_id="c1",
            verification_point_id="vp1",
            interview_id="i1",
            claim_id="cl1",
            conflicting_answers=[],
            contradiction_type="ROLE",
            severity="MEDIUM",
            description="Role inconsistency",
        )
        assert c.contradiction_type == "ROLE"

    def test_scope_contradiction(self):
        """SCOPE contradiction type."""
        c = Contradiction(
            contradiction_id="c1",
            verification_point_id="vp1",
            interview_id="i1",
            claim_id="cl1",
            conflicting_answers=[],
            contradiction_type="SCOPE",
            severity="LOW",
            description="Scope mismatch",
        )
        assert c.contradiction_type == "SCOPE"

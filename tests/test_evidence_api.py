"""Tests for Evidence API endpoints."""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.persistence.models import (
    VerificationPoint,
    Evidence,
    EvidenceTransition,
    Contradiction,
)
from datetime import datetime


client = TestClient(app)


class TestVerificationPointsEndpoint:
    """Test GET /api/v1/evidence/verification-points/{claim_id}"""

    def test_get_verification_points_for_claim(self):
        """Test getting verification points for a claim."""
        # Mock verification point
        mock_vp = VerificationPoint(
            verification_point_id="vp_001",
            claim_id="claim_001",
            competency_code="backend.cache",
            requirement_id=None,
            aspect="Redis implementation",
            expected_evidence={"technical_details": True},
            current_state="PARTIALLY_SUPPORTED",
            strength=0.75,
            confidence="MEDIUM",
            unresolved_reason_codes=["HAS_ANSWER"],
        )
        mock_vp.created_at = datetime(2026, 7, 30, 10, 0, 0)
        mock_vp.updated_at = datetime(2026, 7, 30, 12, 0, 0)

        with patch("app.api.v1.evidence.EvidenceRepository") as mock_repo_class:
            mock_repo = mock_repo_class.return_value
            mock_repo.get_verification_points_for_claim = AsyncMock(return_value=[mock_vp])
            mock_repo.get_evidence_for_verification_point = AsyncMock(return_value=[1, 2])  # 2 evidence
            mock_repo.get_transitions_for_verification_point = AsyncMock(return_value=[1, 2])  # 2 transitions
            mock_repo.get_contradictions_for_verification_point = AsyncMock(return_value=[1])  # 1 contradiction

            response = client.get("/api/v1/evidence/verification-points/claim_001")

            assert response.status_code == 200
            data = response.json()

            assert "verification_points" in data
            assert len(data["verification_points"]) == 1

            vp = data["verification_points"][0]
            assert vp["verification_point_id"] == "vp_001"
            assert vp["claim_id"] == "claim_001"
            assert vp["aspect"] == "Redis implementation"
            assert vp["current_state"] == "PARTIALLY_SUPPORTED"
            assert vp["strength"] == 0.75
            assert vp["confidence"] == "MEDIUM"
            assert vp["evidence_count"] == 2
            assert vp["transition_count"] == 2
            assert vp["has_contradictions"] is True

    def test_get_verification_points_empty(self):
        """Test getting verification points for nonexistent claim."""
        with patch("app.api.v1.evidence.EvidenceRepository") as mock_repo_class:
            mock_repo = mock_repo_class.return_value
            mock_repo.get_verification_points_for_claim = AsyncMock(return_value=[])

            response = client.get("/api/v1/evidence/verification-points/nonexistent")

            assert response.status_code == 200
            data = response.json()
            assert data["verification_points"] == []


class TestTransitionsEndpoint:
    """Test GET /api/v1/evidence/transitions/{vp_id}"""

    def test_get_transitions_for_verification_point(self):
        """Test getting transitions for a verification point."""
        # Mock VP
        mock_vp = VerificationPoint(
            verification_point_id="vp_001",
            claim_id="claim_001",
            competency_code="backend.cache",
            requirement_id=None,
            aspect="Redis implementation",
            expected_evidence={},
            current_state="PARTIALLY_SUPPORTED",
            strength=None,
            confidence=None,
            unresolved_reason_codes=None,
        )

        # Mock transitions
        mock_tr1 = EvidenceTransition(
            transition_id="tr_001",
            verification_point_id="vp_001",
            interview_id="int_001",
            from_state="UNSEEN",
            to_state="ADDRESSED",
            reason_code="FIRST_INQUIRY",
            answer_id="ans_001",
            evaluation_id=None,
            evidence_spans=None,
            policy_version="1.0",
            prompt_version=None,
            model_name=None,
        )
        mock_tr1.created_at = datetime(2026, 7, 30, 10, 0, 0)

        mock_tr2 = EvidenceTransition(
            transition_id="tr_002",
            verification_point_id="vp_001",
            interview_id="int_001",
            from_state="ADDRESSED",
            to_state="PARTIALLY_SUPPORTED",
            reason_code="HAS_ANSWER",
            answer_id="ans_002",
            evaluation_id=None,
            evidence_spans=None,
            policy_version="1.0",
            prompt_version=None,
            model_name=None,
        )
        mock_tr2.created_at = datetime(2026, 7, 30, 11, 0, 0)

        with patch("app.api.v1.evidence.EvidenceRepository") as mock_repo_class:
            mock_repo = mock_repo_class.return_value
            mock_repo.get_verification_point = AsyncMock(return_value=mock_vp)
            mock_repo.get_transitions_for_verification_point = AsyncMock(
                return_value=[mock_tr1, mock_tr2]
            )

            response = client.get("/api/v1/evidence/transitions/vp_001")

            assert response.status_code == 200
            data = response.json()

            assert data["verification_point_id"] == "vp_001"
            assert data["current_state"] == "PARTIALLY_SUPPORTED"
            assert len(data["transitions"]) == 2

            # Check transitions
            assert data["transitions"][0]["from_state"] == "UNSEEN"
            assert data["transitions"][0]["to_state"] == "ADDRESSED"
            assert data["transitions"][1]["from_state"] == "ADDRESSED"
            assert data["transitions"][1]["to_state"] == "PARTIALLY_SUPPORTED"

    def test_get_transitions_not_found(self):
        """Test getting transitions for nonexistent VP."""
        with patch("app.api.v1.evidence.EvidenceRepository") as mock_repo_class:
            mock_repo = mock_repo_class.return_value
            mock_repo.get_verification_point = AsyncMock(return_value=None)

            response = client.get("/api/v1/evidence/transitions/nonexistent")

            assert response.status_code == 404


class TestContradictionsEndpoint:
    """Test GET /api/v1/evidence/contradictions/{interview_id}"""

    def test_get_contradictions_for_interview(self):
        """Test getting contradictions for an interview."""
        mock_ct = Contradiction(
            contradiction_id="ct_001",
            verification_point_id="vp_001",
            interview_id="int_001",
            claim_id="claim_001",
            conflicting_answers=[
                {"answer_id": "ans_001", "text": "Redis"},
                {"answer_id": "ans_002", "text": "Memcached"},
            ],
            contradiction_type="FACTUAL",
            severity="HIGH",
            description="Cache technology contradicted",
            clarification_question="Which caching solution?",
            resolution_status="UNRESOLVED",
            resolution_answer_id=None,
            resolved_at=None,
        )
        mock_ct.created_at = datetime(2026, 7, 30, 10, 0, 0)

        with patch("app.api.v1.evidence.EvidenceRepository") as mock_repo_class:
            mock_repo = mock_repo_class.return_value
            mock_repo.get_contradictions_for_interview = AsyncMock(return_value=[mock_ct])

            response = client.get("/api/v1/evidence/contradictions/int_001")

            assert response.status_code == 200
            data = response.json()

            assert data["interview_id"] == "int_001"
            assert data["total_count"] == 1
            assert len(data["contradictions"]) == 1

            ct = data["contradictions"][0]
            assert ct["contradiction_type"] == "FACTUAL"
            assert ct["severity"] == "HIGH"
            assert ct["resolution_status"] == "UNRESOLVED"

    def test_get_contradictions_filtered(self):
        """Test filtering contradictions by status."""
        with patch("app.api.v1.evidence.EvidenceRepository") as mock_repo_class:
            mock_repo = mock_repo_class.return_value
            mock_repo.get_contradictions_for_interview = AsyncMock(return_value=[])

            response = client.get(
                "/api/v1/evidence/contradictions/int_001?resolution_status=CLARIFIED"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["total_count"] == 0


class TestEvidenceEndpoint:
    """Test GET /api/v1/evidence/evidence/{vp_id}"""

    def test_get_evidence_for_verification_point(self):
        """Test getting evidence for a verification point."""
        mock_vp = VerificationPoint(
            verification_point_id="vp_001",
            claim_id="claim_001",
            competency_code="backend.cache",
            requirement_id=None,
            aspect="Redis implementation",
            expected_evidence={},
            current_state="PARTIALLY_SUPPORTED",
            strength=None,
            confidence=None,
            unresolved_reason_codes=None,
        )

        mock_ev = Evidence(
            evidence_id="ev_001",
            verification_point_id="vp_001",
            interview_id="int_001",
            answer_id="ans_001",
            evidence_type="DIRECT",
            spans=[{
                "start": 0,
                "end": 50,
                "text": "I implemented Redis",
                "quote_hash": "sha256:abc",
            }],
            summary="Redis implementation",
            extracted_by="MODEL",
            confidence=0.85,
        )
        mock_ev.created_at = datetime(2026, 7, 30, 10, 0, 0)

        with patch("app.api.v1.evidence.EvidenceRepository") as mock_repo_class:
            mock_repo = mock_repo_class.return_value
            mock_repo.get_verification_point = AsyncMock(return_value=mock_vp)
            mock_repo.get_evidence_for_verification_point = AsyncMock(return_value=[mock_ev])

            response = client.get("/api/v1/evidence/evidence/vp_001")

            assert response.status_code == 200
            data = response.json()

            assert data["verification_point_id"] == "vp_001"
            assert data["evidence_count"] == 1
            assert len(data["evidence"]) == 1
            assert data["evidence"][0]["evidence_type"] == "DIRECT"
            assert data["evidence"][0]["confidence"] == 0.85

    def test_get_evidence_not_found(self):
        """Test getting evidence for nonexistent VP."""
        with patch("app.api.v1.evidence.EvidenceRepository") as mock_repo_class:
            mock_repo = mock_repo_class.return_value
            mock_repo.get_verification_point = AsyncMock(return_value=None)

            response = client.get("/api/v1/evidence/evidence/nonexistent")

            assert response.status_code == 404

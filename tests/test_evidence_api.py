"""Tests for Evidence API endpoints."""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.core.ids import new_id
from app.main import app
from app.persistence.database import async_session_factory
from app.persistence.models import (
    Contradiction,
    Evidence,
    EvidenceTransition,
    Interview,
    ResumeClaim,
    ResumeSource,
    VerificationPoint,
)

client = TestClient(app)


def _register_user():
    """Register a user via the API and return (token, user_id)."""
    response = client.post(
        "/api/v1/register",
        json={"email": f"evid_{new_id('u')}@example.com", "password": "pass1234"},
    )
    assert response.status_code == 201, response.text
    token = response.json()["access_token"]
    me = client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    return token, me.json()["user_id"]


def _seed_resume_claim(user_id, claim_id, vp_id=None):
    """Insert a resume + claim (+ optional verification point) owned by the user."""
    async def _do():
        async with async_session_factory() as session:
            resume_id = new_id("resume")
            session.add(ResumeSource(
                resume_id=resume_id,
                user_id=user_id,
                source_id="src1",
                file_name="resume.txt",
                source_type="text",
            ))
            # No ORM relationship links these tables, so flush each parent before
            # inserting its child to keep PostgreSQL FK order explicit.
            await session.flush()
            session.add(ResumeClaim(
                claim_id=claim_id,
                resume_id=resume_id,
                data={},
                priority=0,
                confidence=0.5,
                disabled=False,
            ))
            await session.flush()
            if vp_id:
                session.add(VerificationPoint(
                    verification_point_id=vp_id,
                    claim_id=claim_id,
                    competency_code="backend.cache",
                    aspect="Redis implementation",
                    expected_evidence={"technical_details": True},
                    current_state="UNSEEN",
                ))
            await session.commit()
    asyncio.run(_do())


def _seed_interview(user_id, interview_id):
    """Insert an interview (with an owning resume) owned by the user."""
    async def _do():
        async with async_session_factory() as session:
            resume_id = new_id("resume")
            session.add(ResumeSource(
                resume_id=resume_id,
                user_id=user_id,
                source_id="src1",
                file_name="resume.txt",
                source_type="text",
            ))
            await session.flush()
            session.add(Interview(
                interview_id=interview_id,
                thread_id=interview_id,
                user_id=user_id,
                resume_id=resume_id,
                target_role="Backend Engineer",
                status="IN_PROGRESS",
            ))
            await session.commit()
    asyncio.run(_do())


class TestVerificationPointsEndpoint:
    """Test GET /api/v1/evidence/verification-points/{claim_id}"""

    def test_get_verification_points_for_claim(self):
        """Test getting verification points for a claim."""
        token, user_id = _register_user()
        claim_id = new_id("claim")
        _seed_resume_claim(user_id, claim_id)
        headers = {"Authorization": f"Bearer {token}"}

        # Mock verification point
        mock_vp = VerificationPoint(
            verification_point_id="vp_001",
            claim_id=claim_id,
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

            response = client.get(
                f"/api/v1/evidence/verification-points/{claim_id}", headers=headers
            )

            assert response.status_code == 200
            data = response.json()

            assert "verification_points" in data
            assert len(data["verification_points"]) == 1

            vp = data["verification_points"][0]
            assert vp["verification_point_id"] == "vp_001"
            assert vp["claim_id"] == claim_id
            assert vp["aspect"] == "Redis implementation"
            assert vp["current_state"] == "PARTIALLY_SUPPORTED"
            assert vp["strength"] == 0.75
            assert vp["confidence"] == "MEDIUM"
            assert vp["evidence_count"] == 2
            assert vp["transition_count"] == 2
            assert vp["has_contradictions"] is True

    def test_get_verification_points_empty(self):
        """Test getting verification points for a claim with no VPs."""
        token, user_id = _register_user()
        claim_id = new_id("claim")
        _seed_resume_claim(user_id, claim_id)
        headers = {"Authorization": f"Bearer {token}"}

        with patch("app.api.v1.evidence.EvidenceRepository") as mock_repo_class:
            mock_repo = mock_repo_class.return_value
            mock_repo.get_verification_points_for_claim = AsyncMock(return_value=[])

            response = client.get(
                f"/api/v1/evidence/verification-points/{claim_id}", headers=headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["verification_points"] == []

    def test_get_verification_points_unauthorized(self):
        """Test that a claim not owned by the user returns 404."""
        token, _user_id = _register_user()
        _other_token, other_user_id = _register_user()
        claim_id = new_id("claim")
        _seed_resume_claim(other_user_id, claim_id)  # owned by someone else
        headers = {"Authorization": f"Bearer {token}"}

        with patch("app.api.v1.evidence.EvidenceRepository"):
            response = client.get(
                f"/api/v1/evidence/verification-points/{claim_id}", headers=headers
            )
            assert response.status_code == 404


class TestTransitionsEndpoint:
    """Test GET /api/v1/evidence/transitions/{vp_id}"""

    def test_get_transitions_for_verification_point(self):
        """Test getting transitions for a verification point."""
        token, user_id = _register_user()
        vp_id = new_id("vp")
        claim_id = new_id("claim")
        _seed_resume_claim(user_id, claim_id, vp_id=vp_id)
        headers = {"Authorization": f"Bearer {token}"}

        # Mock VP
        mock_vp = VerificationPoint(
            verification_point_id=vp_id,
            claim_id=claim_id,
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
            verification_point_id=vp_id,
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
            verification_point_id=vp_id,
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

            response = client.get(
                f"/api/v1/evidence/transitions/{vp_id}", headers=headers
            )

            assert response.status_code == 200
            data = response.json()

            assert data["verification_point_id"] == vp_id
            assert data["current_state"] == "PARTIALLY_SUPPORTED"
            assert len(data["transitions"]) == 2

            # Check transitions
            assert data["transitions"][0]["from_state"] == "UNSEEN"
            assert data["transitions"][0]["to_state"] == "ADDRESSED"
            assert data["transitions"][1]["from_state"] == "ADDRESSED"
            assert data["transitions"][1]["to_state"] == "PARTIALLY_SUPPORTED"

    def test_get_transitions_not_found(self):
        """Test getting transitions for nonexistent VP."""
        token, user_id = _register_user()
        vp_id = new_id("vp")
        claim_id = new_id("claim")
        _seed_resume_claim(user_id, claim_id, vp_id=vp_id)
        headers = {"Authorization": f"Bearer {token}"}

        with patch("app.api.v1.evidence.EvidenceRepository") as mock_repo_class:
            mock_repo = mock_repo_class.return_value
            mock_repo.get_verification_point = AsyncMock(return_value=None)

            response = client.get(
                f"/api/v1/evidence/transitions/{vp_id}", headers=headers
            )

            assert response.status_code == 404


class TestContradictionsEndpoint:
    """Test GET /api/v1/evidence/contradictions/{interview_id}"""

    def test_get_contradictions_for_interview(self):
        """Test getting contradictions for an interview."""
        token, user_id = _register_user()
        interview_id = new_id("interview")
        _seed_interview(user_id, interview_id)
        headers = {"Authorization": f"Bearer {token}"}

        mock_ct = Contradiction(
            contradiction_id="ct_001",
            verification_point_id="vp_001",
            interview_id=interview_id,
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

            response = client.get(
                f"/api/v1/evidence/contradictions/{interview_id}", headers=headers
            )

            assert response.status_code == 200
            data = response.json()

            assert data["interview_id"] == interview_id
            assert data["total_count"] == 1
            assert len(data["contradictions"]) == 1

            ct = data["contradictions"][0]
            assert ct["contradiction_type"] == "FACTUAL"
            assert ct["severity"] == "HIGH"
            assert ct["resolution_status"] == "UNRESOLVED"

    def test_get_contradictions_filtered(self):
        """Test filtering contradictions by status."""
        token, user_id = _register_user()
        interview_id = new_id("interview")
        _seed_interview(user_id, interview_id)
        headers = {"Authorization": f"Bearer {token}"}

        with patch("app.api.v1.evidence.EvidenceRepository") as mock_repo_class:
            mock_repo = mock_repo_class.return_value
            mock_repo.get_contradictions_for_interview = AsyncMock(return_value=[])

            response = client.get(
                f"/api/v1/evidence/contradictions/{interview_id}?resolution_status=CLARIFIED",
                headers=headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["total_count"] == 0

    def test_get_contradictions_unauthorized(self):
        """Test that an interview not owned by the user returns 404."""
        token, _user_id = _register_user()
        _other_token, other_user_id = _register_user()
        interview_id = new_id("interview")
        _seed_interview(other_user_id, interview_id)  # owned by someone else
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get(
            f"/api/v1/evidence/contradictions/{interview_id}", headers=headers
        )
        assert response.status_code == 404


class TestEvidenceEndpoint:
    """Test GET /api/v1/evidence/evidence/{vp_id}"""

    def test_get_evidence_for_verification_point(self):
        """Test getting evidence for a verification point."""
        token, user_id = _register_user()
        vp_id = new_id("vp")
        claim_id = new_id("claim")
        _seed_resume_claim(user_id, claim_id, vp_id=vp_id)
        headers = {"Authorization": f"Bearer {token}"}

        mock_vp = VerificationPoint(
            verification_point_id=vp_id,
            claim_id=claim_id,
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
            verification_point_id=vp_id,
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

            response = client.get(
                f"/api/v1/evidence/evidence/{vp_id}", headers=headers
            )

            assert response.status_code == 200
            data = response.json()

            assert data["verification_point_id"] == vp_id
            assert data["evidence_count"] == 1
            assert len(data["evidence"]) == 1
            assert data["evidence"][0]["evidence_type"] == "DIRECT"
            assert data["evidence"][0]["confidence"] == 0.85

    def test_get_evidence_not_found(self):
        """Test getting evidence for nonexistent VP."""
        token, user_id = _register_user()
        vp_id = new_id("vp")
        claim_id = new_id("claim")
        _seed_resume_claim(user_id, claim_id, vp_id=vp_id)
        headers = {"Authorization": f"Bearer {token}"}

        with patch("app.api.v1.evidence.EvidenceRepository") as mock_repo_class:
            mock_repo = mock_repo_class.return_value
            mock_repo.get_verification_point = AsyncMock(return_value=None)

            response = client.get(
                f"/api/v1/evidence/evidence/{vp_id}", headers=headers
            )

            assert response.status_code == 404

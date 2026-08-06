"""Tests for the ability profile API observation-building logic.

Phase 2.4 Task #27: Verifies that interview reports are converted into
AbilityAggregator-compatible observations with correct evidence metrics.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.v1.abilities import (
    _build_observation,
    _evidence_metrics,
    _unresolved_contradictions,
)
from app.core.deps import get_current_user
from app.main import app
from app.persistence.database import get_session

client = TestClient(app)


class _Obj:
    """Simple attribute-bag for constructing mock model instances."""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class TestAbilityProfileEndpoint:
    """Test GET /api/v1/abilities/profile/{resume_id}"""

    def _override(self, user, session):
        app.dependency_overrides[get_current_user] = lambda: user
        app.dependency_overrides[get_session] = lambda: session

    def _teardown(self):
        app.dependency_overrides.clear()

    def _user(self, user_id="u1"):
        return _Obj(user_id=user_id, email=f"{user_id}@test.com")

    def _resume(self, user_id="u1"):
        return _Obj(resume_id="r1", user_id=user_id)

    def test_missing_resume_returns_404(self):
        """Test unknown resume IDs return 404."""
        session = AsyncMock()
        session.get.return_value = None
        self._override(self._user(), session)
        try:
            resp = client.get("/api/v1/abilities/profile/r_missing")
            assert resp.status_code == 404
        finally:
            self._teardown()

    def test_foreign_resume_returns_404(self):
        """Test another user's resume returns 404 (no existence leak)."""
        session = AsyncMock()
        session.get.return_value = self._resume(user_id="u_other")
        self._override(self._user(user_id="u1"), session)
        try:
            resp = client.get("/api/v1/abilities/profile/r1")
            assert resp.status_code == 404
        finally:
            self._teardown()

    def test_no_reports_returns_empty_profile(self):
        """Test a resume with no reports returns an empty profile."""
        session = AsyncMock()
        session.get.return_value = self._resume()
        interview_result = MagicMock()
        interview_result.all.return_value = []
        session.execute.return_value = interview_result
        self._override(self._user(), session)
        try:
            resp = client.get("/api/v1/abilities/profile/r1")
            assert resp.status_code == 200
            data = resp.json()
            assert data["total_interviews"] == 0
            assert data["competencies"] == []
        finally:
            self._teardown()

    def test_success_returns_aggregated_profile(self):
        """Test a report produces an aggregated per-competency profile."""
        session = AsyncMock()
        session.get.return_value = self._resume()

        interview = _Obj(interview_id="i1", user_id="u1")
        report = _Obj(
            data={
                "ability_scores": {"clarity": 80.0},
                "question_details": [{"depth": 4, "score": 80}],
                "claim_statuses": {
                    "c1": {"verified_points": ["vp1"], "partial_points": [], "missing_points": []}
                },
            },
            created_at=datetime(2026, 8, 4, 10, 0, 0),
        )
        interview_result = MagicMock()
        interview_result.all.return_value = [(interview, report)]

        session.execute.return_value = interview_result
        self._override(self._user(), session)
        try:
            resp = client.get("/api/v1/abilities/profile/r1")
            assert resp.status_code == 200
            data = resp.json()
            assert data["total_interviews"] == 1
            assert len(data["competencies"]) == 1
            comp = data["competencies"][0]
            assert comp["competency_code"] == "clarity"
            assert comp["profile"]["avg_score"] == 80.0
            assert comp["profile"]["last_evidence_status"] == "VERIFIED"
            assert comp["history"] == [
                {"interview_id": "i1", "score": 80.0, "created_at": "2026-08-04T10:00:00"}
            ]
        finally:
            self._teardown()


class TestEvidenceMetrics:
    """Test verification-point evidence aggregation from claim statuses."""

    def test_aggregates_verification_points(self):
        """Test counting from verified/partial/missing point arrays."""
        statuses = {
            "c1": {"status": "VERIFIED", "verified_points": ["vp1", "vp2"], "partial_points": [], "missing_points": []},
            "c2": {"status": "PARTIALLY_VERIFIED", "verified_points": ["vp3"], "partial_points": ["vp4"], "missing_points": ["vp5"]},
            "c3": {"status": "IN_PROGRESS", "verified_points": [], "partial_points": [], "missing_points": ["vp6"]},
        }

        metrics = _evidence_metrics(statuses)

        assert metrics["verification_points_addressed"] == 6
        assert metrics["verification_points_verified"] == 3
        assert metrics["evidence_strength"] == pytest.approx(0.5)
        assert metrics["evidence_status"] == "PARTIALLY_SUPPORTED"

    def test_all_points_verified_yields_verified(self):
        """Test that fully verified points produce VERIFIED status."""
        statuses = {
            "c1": {"verified_points": ["vp1", "vp2"], "partial_points": [], "missing_points": []},
        }

        metrics = _evidence_metrics(statuses)

        assert metrics["evidence_status"] == "VERIFIED"
        assert metrics["evidence_strength"] == 1.0

    def test_no_verified_points_yields_unverified(self):
        """Test that no verified points produce UNVERIFIED status."""
        statuses = {
            "c1": {"verified_points": [], "partial_points": [], "missing_points": ["vp1"]},
        }

        metrics = _evidence_metrics(statuses)

        assert metrics["evidence_status"] == "UNVERIFIED"
        assert metrics["evidence_strength"] == 0.0

    def test_legacy_string_statuses_fall_back_to_claim_count(self):
        """Test legacy reports where claim statuses are plain strings."""
        statuses = {"c1": "VERIFIED", "c2": "PARTIALLY_VERIFIED", "c3": "UNTOUCHED"}

        metrics = _evidence_metrics(statuses)

        assert metrics["verification_points_addressed"] == 3
        assert metrics["verification_points_verified"] == 1
        assert metrics["evidence_strength"] == pytest.approx(1 / 3)

    def test_mixed_point_and_legacy_statuses(self):
        """Test reports mixing point-array and legacy string statuses."""
        statuses = {
            "c1": {"status": "VERIFIED", "verified_points": ["vp1"], "partial_points": [], "missing_points": []},
            "c2": "VERIFIED",
            "c3": "PARTIALLY_VERIFIED",
        }

        metrics = _evidence_metrics(statuses)

        assert metrics["verification_points_addressed"] == 3
        assert metrics["verification_points_verified"] == 2
        assert metrics["evidence_strength"] == pytest.approx(2 / 3)
        assert metrics["evidence_status"] == "PARTIALLY_SUPPORTED"

    def test_partial_only_points_not_verified(self):
        """Test that partial-only points are not treated as VERIFIED."""
        statuses = {
            "c1": {"status": "PARTIALLY_VERIFIED", "verified_points": [], "partial_points": ["vp1", "vp2"], "missing_points": []},
        }

        metrics = _evidence_metrics(statuses)

        assert metrics["evidence_status"] == "UNVERIFIED"
        assert metrics["evidence_strength"] == 0.0

    def test_verified_with_partial_points_is_partial(self):
        """Test that verified plus partial points yields PARTIALLY_SUPPORTED."""
        statuses = {
            "c1": {"status": "PARTIALLY_VERIFIED", "verified_points": ["vp1"], "partial_points": ["vp2"], "missing_points": []},
        }

        metrics = _evidence_metrics(statuses)

        assert metrics["evidence_status"] == "PARTIALLY_SUPPORTED"
        assert metrics["evidence_strength"] == pytest.approx(0.5)


class TestUnresolvedContradictions:
    """Test report-level unresolved contradiction counting."""

    def test_counts_unresolved_only(self):
        """Test resolved entries are excluded; the rest are unresolved."""
        report_data = {
            "contradictions": [
                {"contradiction_id": "ct1"},
                {"contradiction_id": "ct2", "resolved": False},
                {"contradiction_id": "ct3", "resolved": True},
                "not-a-dict",
            ]
        }

        assert _unresolved_contradictions(report_data) == 3

    def test_missing_contradictions_returns_zero(self):
        """Test reports without contradiction data yield zero."""
        assert _unresolved_contradictions({}) == 0


class TestBuildObservation:
    """Test converting a report into an aggregator observation."""

    def test_builds_observation_from_report(self):
        """Test a typical report produces a valid observation."""
        report = {
            "ability_scores": {
                "technical_correctness": 78.0,
                "implementation_depth": 65.0,
            },
            "question_details": [
                {"question_id": "q1", "depth": 2, "score": 80},
                {"question_id": "q2", "depth": 4, "score": 76},
                {"question_id": "q3", "depth": 6, "score": 78},
            ],
            "claim_statuses": {
                "c1": {"status": "VERIFIED", "verified_points": ["vp1"], "partial_points": [], "missing_points": []},
                "c2": {"status": "PARTIALLY_VERIFIED", "verified_points": [], "partial_points": ["vp2"], "missing_points": ["vp3"]},
            },
            "contradictions": [{"contradiction_id": "x"}],
        }

        obs = _build_observation(report, "technical_correctness", "2026-08-04T00:00:00")

        assert obs is not None
        assert obs["avg_score"] == 78.0
        assert obs["question_count"] == 3
        assert obs["max_depth"] == 6
        # Depths 2/4/6 map to background/detail/deep angle labels
        assert obs["question_forms"] == ["background", "deep", "detail"]
        # 1 verified point out of 3 total
        assert obs["verification_points_verified"] == 1
        assert obs["verification_points_addressed"] == 3
        assert obs["evidence_strength"] == pytest.approx(1 / 3)
        assert obs["evidence_status"] == "PARTIALLY_SUPPORTED"
        assert obs["contradiction_count"] == 1

    def test_contradiction_count_derived_from_report(self):
        """Test contradiction count is derived per-report and skips resolved."""
        report = {
            "ability_scores": {"clarity": 90.0},
            "question_details": [{"depth": 3, "score": 90}],
            "claim_statuses": {"c1": {"verified_points": ["vp1"], "partial_points": [], "missing_points": []}},
            "contradictions": [
                {"contradiction_id": "ct1"},
                {"contradiction_id": "ct2", "resolved": True},
            ],
        }

        obs = _build_observation(report, "clarity", None)

        assert obs is not None
        assert obs["contradiction_count"] == 1

    def test_prefers_explicit_question_form(self):
        """Test explicit question_form values take precedence over depth angles."""
        report = {
            "ability_scores": {"clarity": 90.0},
            "question_details": [
                {"depth": 7, "score": 90, "question_form": "debugging"},
            ],
            "claim_statuses": {"c1": {"verified_points": ["vp1"], "partial_points": [], "missing_points": []}},
            "contradictions": [],
        }

        obs = _build_observation(report, "clarity", None)

        assert obs is not None
        assert obs["question_forms"] == ["debugging"]

    def test_depth_seven_does_not_yield_counterfactual_form(self):
        """Test that depth-7 questions are not labeled counterfactual."""
        report = {
            "ability_scores": {"architecture_tradeoffs": 82.0},
            "question_details": [{"depth": 7, "score": 82}],
            "claim_statuses": {"c1": {"verified_points": ["vp1"], "partial_points": [], "missing_points": []}},
            "contradictions": [],
        }

        obs = _build_observation(report, "architecture_tradeoffs", None)

        assert obs is not None
        assert "counterfactual" not in obs["question_forms"]
        assert "evolution" in obs["question_forms"]

    def test_missing_competency_returns_none(self):
        """Test that reports without the requested competency produce no observation."""
        report = {
            "ability_scores": {"clarity": 70.0},
            "question_details": [{"depth": 1, "score": 70}],
            "claim_statuses": {},
            "contradictions": [],
        }

        assert _build_observation(report, "architecture_tradeoffs", None) is None

    def test_no_points_returns_unverified(self):
        """Test reports without claims produce UNVERIFIED evidence status."""
        report = {
            "ability_scores": {"clarity": 70.0},
            "question_details": [{"depth": 1, "score": 70}],
            "claim_statuses": {},
            "contradictions": [],
        }

        obs = _build_observation(report, "clarity", None)

        assert obs is not None
        assert obs["evidence_status"] == "UNVERIFIED"
        assert obs["evidence_strength"] == 0.0

"""Tests for the answer version diff API.

Phase 2.4 Task #28: Verifies that per-question answer versions are returned
with diffs computed between consecutive versions.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from app.api.v1.answer_diff import _answer_score
from app.core.deps import get_current_user
from app.main import app
from app.persistence.database import get_session

client = TestClient(app)


class _Obj:
    """Simple attribute-bag for constructing mock model instances."""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def _interview(user_id="u1"):
    return _Obj(interview_id="i1", user_id=user_id)


def _answer(answer_id, text, evaluation=None, created_at=None):
    return _Obj(
        answer_id=answer_id,
        interview_id="i1",
        question_id="q1",
        answer_text=text,
        evaluation=evaluation,
        created_at=created_at or datetime(2026, 8, 5, 10, 0, 0),
    )


def _override(user, session):
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_session] = lambda: session


def _teardown():
    app.dependency_overrides.clear()


class TestAnswerVersionsEndpoint:
    """Test GET /api/v1/interviews/{id}/questions/{qid}/versions"""

    def test_missing_interview_returns_404(self):
        """Test unknown interview IDs return 404."""
        session = AsyncMock()
        session.get.return_value = None
        _override(_Obj(user_id="u1", email="u1@test.com"), session)
        try:
            resp = client.get("/api/v1/interviews/i_missing/questions/q1/versions")
            assert resp.status_code == 404
        finally:
            _teardown()

    def test_foreign_interview_returns_404(self):
        """Test another user's interview returns 404 (no existence leak)."""
        session = AsyncMock()
        session.get.return_value = _interview(user_id="u_other")
        _override(_Obj(user_id="u1", email="u1@test.com"), session)
        try:
            resp = client.get("/api/v1/interviews/i1/questions/q1/versions")
            assert resp.status_code == 404
        finally:
            _teardown()

    def test_no_answers_returns_empty_versions(self):
        """Test a question with no answers returns an empty version list."""
        session = AsyncMock()
        session.get.return_value = _interview()
        result = MagicMock()
        result.scalars().all.return_value = []
        session.execute.return_value = result
        _override(_Obj(user_id="u1", email="u1@test.com"), session)
        try:
            resp = client.get("/api/v1/interviews/i1/questions/q1/versions")
            assert resp.status_code == 200
            data = resp.json()
            assert data["versions"] == []
        finally:
            _teardown()

    def test_single_answer_has_no_diff(self):
        """Test a single answer returns one version with a null diff."""
        session = AsyncMock()
        session.get.return_value = _interview()
        result = MagicMock()
        result.scalars().all.return_value = [_answer("a1", "基础回答")]
        session.execute.return_value = result
        _override(_Obj(user_id="u1", email="u1@test.com"), session)
        try:
            resp = client.get("/api/v1/interviews/i1/questions/q1/versions")
            assert resp.status_code == 200
            versions = resp.json()["versions"]
            assert len(versions) == 1
            assert versions[0]["version_number"] == 1
            assert versions[0]["answer_id"] == "a1"
            assert versions[0]["diff"] is None
        finally:
            _teardown()

    def test_two_answers_compute_diff(self):
        """Test consecutive answers produce a diff with change metrics."""
        session = AsyncMock()
        session.get.return_value = _interview()
        result = MagicMock()
        result.scalars().all.return_value = [
            _answer("a1", "系统支持高并发，使用缓存提升性能。"),
            _answer("a2", "系统支持高并发，使用 Redis 缓存提升性能，QPS 提升到 1 万。"),
        ]
        session.execute.return_value = result
        _override(_Obj(user_id="u1", email="u1@test.com"), session)
        try:
            resp = client.get("/api/v1/interviews/i1/questions/q1/versions")
            assert resp.status_code == 200
            versions = resp.json()["versions"]
            assert len(versions) == 2
            assert versions[1]["version_number"] == 2
            diff = versions[1]["diff"]
            assert diff is not None
            assert diff["is_substantive_change"] is True
            assert diff["new_evidence"] is True
            assert diff["change_ratio"] > 0
        finally:
            _teardown()

    def test_answer_score_extracted_from_evaluation(self):
        """Test weighted score is derived from an answer evaluation."""
        evaluation = {
            "dimensions": [{"dimension": "technical_correctness", "score": 80}],
        }
        assert _answer_score(evaluation) == 80.0

    def test_missing_evaluation_yields_none(self):
        """Test answers without an evaluation yield a null score."""
        assert _answer_score(None) is None
        assert _answer_score("not-a-dict") is None

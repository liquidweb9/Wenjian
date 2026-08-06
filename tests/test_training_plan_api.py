"""Tests for the training plan API.

Phase 2.4 Task #30: Verifies listing, generation, and status updates of
training tasks derived from a resume's ability profile.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from app.core.deps import get_current_user
from app.main import app
from app.persistence.database import get_session

client = TestClient(app)


class _Obj:
    """Simple attribute-bag for constructing mock model instances."""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def _resume(user_id="u1"):
    return _Obj(resume_id="r1", user_id=user_id)


def _task(task_id="t1", user_id="u1", status="PENDING", priority=80):
    return _Obj(
        task_id=task_id,
        user_id=user_id,
        resume_id="r1",
        interview_id="i1",
        task_type="DEPTH_IMPROVEMENT",
        competency_code="clarity",
        title="深化「表达清晰度」的技术深度",
        description="补充细节",
        completion_criteria={"target_avg_score": 75},
        status=status,
        priority=priority,
        created_at=datetime(2026, 8, 5, 10, 0, 0),
        completed_at=None,
    )


def _report_data():
    return {
        "ability_scores": {"clarity": 60.0},
        "question_details": [{"depth": 4, "score": 60}],
        "claim_statuses": {
            "c1": {"verified_points": ["vp1"], "partial_points": [], "missing_points": []}
        },
        "contradictions": [],
    }


def _interview_report(interview_id="i1"):
    return (
        _Obj(interview_id=interview_id, user_id="u1", resume_id="r1"),
        _Obj(data=_report_data(), created_at=datetime(2026, 8, 5, 10, 0, 0)),
    )


def _override(user, session):
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_session] = lambda: session


def _teardown():
    app.dependency_overrides.clear()


def _user(user_id="u1"):
    return _Obj(user_id=user_id, email=f"{user_id}@test.com")


class TestListTasks:
    """Test GET /api/v1/training-plans"""

    def test_foreign_resume_returns_404(self):
        """Test listing tasks for another user's resume returns 404."""
        session = AsyncMock()
        session.get.return_value = _resume(user_id="u_other")
        _override(_user(), session)
        try:
            resp = client.get("/api/v1/training-plans", params={"resume_id": "r1"})
            assert resp.status_code == 404
        finally:
            _teardown()

    def test_lists_owned_tasks(self):
        """Test owned tasks are returned sorted by priority."""
        session = AsyncMock()
        session.get.return_value = _resume()
        result = MagicMock()
        result.scalars.return_value.all.return_value = [_task(priority=90), _task(task_id="t2", priority=70)]
        session.execute.return_value = result
        _override(_user(), session)
        try:
            resp = client.get("/api/v1/training-plans", params={"resume_id": "r1"})
            assert resp.status_code == 200
            tasks = resp.json()["tasks"]
            assert len(tasks) == 2
            assert tasks[0]["task_id"] == "t1"
            assert tasks[0]["completion_criteria"] == {"target_avg_score": 75}
        finally:
            _teardown()


class TestGenerateTasks:
    """Test POST /api/v1/training-plans/{resume_id}/generate"""

    def test_foreign_resume_returns_404(self):
        """Test generating for another user's resume returns 404."""
        session = AsyncMock()
        session.get.return_value = _resume(user_id="u_other")
        _override(_user(), session)
        try:
            resp = client.post("/api/v1/training-plans/r1/generate")
            assert resp.status_code == 404
        finally:
            _teardown()

    def test_generates_tasks_from_reports(self):
        """Test tasks are generated from ability profile observations."""
        session = AsyncMock()
        session.get.return_value = _resume()

        report_result = MagicMock()
        report_result.all.return_value = [_interview_report()]

        added_tasks: list = []

        def fake_add(task):
            added_tasks.append(task)

        session.add = MagicMock(side_effect=fake_add)

        final_scalars = MagicMock()
        final_scalars.all.side_effect = lambda: list(added_tasks)
        final_result = MagicMock()
        final_result.scalars.return_value = final_scalars

        session.execute.side_effect = [report_result, MagicMock(), final_result]
        _override(_user(), session)
        try:
            resp = client.post("/api/v1/training-plans/r1/generate")
            assert resp.status_code == 200
            tasks = resp.json()["tasks"]
            assert len(tasks) >= 1
            assert tasks[0]["resume_id"] == "r1"
            assert tasks[0]["status"] == "PENDING"
            assert tasks[0]["task_type"] in {
                "EVIDENCE_COMPLETION",
                "CONCEPT_REVIEW",
                "DEPTH_IMPROVEMENT",
                "CONTRADICTION_RESOLUTION",
                "FORM_DIVERSIFICATION",
                "TRANSFER_PRACTICE",
            }
        finally:
            _teardown()


class TestUpdateTaskStatus:
    """Test PATCH /api/v1/training-plans/{task_id}"""

    def test_invalid_status_returns_400(self):
        """Test unknown statuses are rejected."""
        session = AsyncMock()
        _override(_user(), session)
        try:
            resp = client.patch("/api/v1/training-plans/t1", json={"status": "NOPE"})
            assert resp.status_code == 400
        finally:
            _teardown()

    def test_foreign_task_returns_404(self):
        """Test updating another user's task returns 404."""
        session = AsyncMock()
        session.get.return_value = _task(user_id="u_other")
        _override(_user(), session)
        try:
            resp = client.patch("/api/v1/training-plans/t1", json={"status": "IN_PROGRESS"})
            assert resp.status_code == 404
        finally:
            _teardown()

    def test_updates_status(self):
        """Test a task status is updated."""
        task = _task()
        session = AsyncMock()
        session.get.return_value = task
        session.refresh = AsyncMock()
        _override(_user(), session)
        try:
            resp = client.patch("/api/v1/training-plans/t1", json={"status": "IN_PROGRESS"})
            assert resp.status_code == 200
            assert resp.json()["status"] == "IN_PROGRESS"
            assert task.status == "IN_PROGRESS"
        finally:
            _teardown()

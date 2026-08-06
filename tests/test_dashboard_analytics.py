"""Tests that dashboard/analytics aggregates are scoped to the current user.

M2.6: these endpoints previously returned global counts (all users) while the
resume/interview list pages filter by user, producing inconsistent numbers and
leaking other users' data in the dashboard's recent/in-progress sections.
"""

import asyncio

from fastapi.testclient import TestClient

from app.core.ids import new_id
from app.main import app
from app.persistence.database import async_session_factory
from app.persistence.models import (
    Interview,
    InterviewReport,
    ResumeRevision,
    ResumeSource,
)

client = TestClient(app)


def _register_user(prefix: str):
    """Register a user via the API and return (token, user_id)."""
    response = client.post(
        "/api/v1/register",
        json={"email": f"dash_{prefix}_{new_id('u')}@example.com", "password": "pass1234"},
    )
    assert response.status_code == 201, response.text
    token = response.json()["access_token"]
    me = client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    return token, me.json()["user_id"]


def _seed(user_a_id: str, user_b_id: str):
    """Seed: user A owns 2 resumes + 2 interviews (1 finished, 1 in-progress);
    user B owns 1 resume. Returns nothing."""
    async def _do():
        async with async_session_factory() as session:
            resume_a1 = new_id("resume")
            resume_a2 = new_id("resume")
            resume_b1 = new_id("resume")
            for rid, uid, name, status in (
                (resume_a1, user_a_id, "a-resume-1.txt", "CONFIRMED"),
                (resume_a2, user_a_id, "a-resume-2.txt", "PARSED_UNCONFIRMED"),
                (resume_b1, user_b_id, "b-resume.txt", "CONFIRMED"),
            ):
                session.add(ResumeSource(
                    resume_id=rid,
                    user_id=uid,
                    source_id="src1",
                    file_name=name,
                    source_type="text",
                ))
                session.add(ResumeRevision(
                    revision_id=new_id("rev"),
                    resume_id=rid,
                    status=status,
                ))
            # Flush parents before children without an ORM relationship.
            await session.flush()

            interview_finished = new_id("interview")
            interview_active = new_id("interview")
            session.add(Interview(
                interview_id=interview_finished,
                thread_id=interview_finished,
                user_id=user_a_id,
                resume_id=resume_a1,
                target_role="Backend Engineer",
                status="finished",
            ))
            session.add(Interview(
                interview_id=interview_active,
                thread_id=interview_active,
                user_id=user_a_id,
                resume_id=resume_a2,
                target_role="Backend Engineer",
                status="in_progress",
            ))
            session.add(InterviewReport(
                report_id=new_id("report"),
                interview_id=interview_finished,
                data={"overall_score": 80},
            ))
            session.add(InterviewReport(
                report_id=new_id("report"),
                interview_id=interview_active,
                data={"overall_score": 60},
            ))
            await session.commit()
    asyncio.run(_do())


class TestDashboardSummary:
    """Test GET /api/v1/dashboard/summary is user-scoped."""

    def _setup(self):
        token_a, user_a_id = _register_user("a")
        token_b, user_b_id = _register_user("b")
        _seed(user_a_id, user_b_id)
        return token_a, token_b

    def test_requires_auth(self):
        response = client.get("/api/v1/dashboard/summary")
        assert response.status_code == 401

    def test_user_a_sees_only_own_data(self):
        token_a, _ = self._setup()
        response = client.get(
            "/api/v1/dashboard/summary",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_resumes"] == 2
        assert data["pending_reviews"] == 1
        assert data["total_interviews"] == 2
        assert data["completed_interviews"] == 1
        assert data["in_progress_count"] == 1
        assert data["average_score"] == 70.0
        assert {r["file_name"] for r in data["recent_resumes"]} == {
            "a-resume-1.txt",
            "a-resume-2.txt",
        }
        assert len(data["in_progress_interviews"]) == 1
        assert data["in_progress_interviews"][0]["target_role"] == "Backend Engineer"

    def test_user_b_sees_only_own_data(self):
        _, token_b = self._setup()
        response = client.get(
            "/api/v1/dashboard/summary",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_resumes"] == 1
        assert data["total_interviews"] == 0
        assert data["completed_interviews"] == 0
        assert data["in_progress_count"] == 0
        assert data["average_score"] is None
        assert {r["file_name"] for r in data["recent_resumes"]} == {"b-resume.txt"}
        assert data["in_progress_interviews"] == []


class TestAnalyticsEndpoints:
    """Test GET /api/v1/analytics/summary and /trends are user-scoped."""

    def _setup(self):
        token_a, user_a_id = _register_user("c")
        token_b, user_b_id = _register_user("d")
        _seed(user_a_id, user_b_id)
        return token_a, token_b

    def test_requires_auth(self):
        assert client.get("/api/v1/analytics/summary").status_code == 401
        assert client.get("/api/v1/analytics/trends").status_code == 401

    def test_summary_user_scoped(self):
        token_a, token_b = self._setup()

        resp_a = client.get(
            "/api/v1/analytics/summary",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert resp_a.status_code == 200
        data_a = resp_a.json()
        assert data_a["total_interviews"] == 2
        assert data_a["average_score"] == 70.0
        assert data_a["score_distribution"]["41-60"] == 1  # score 60
        assert data_a["score_distribution"]["61-80"] == 1  # score 80

        resp_b = client.get(
            "/api/v1/analytics/summary",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert resp_b.status_code == 200
        data_b = resp_b.json()
        assert data_b["total_interviews"] == 0
        assert data_b["average_score"] is None

    def test_trends_user_scoped(self):
        token_a, token_b = self._setup()

        resp_a = client.get(
            "/api/v1/analytics/trends",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert resp_a.status_code == 200
        data_a = resp_a.json()
        # Both interviews land in the same calendar week, so the weekly series has
        # one bucket whose count reflects all 2 of user A's interviews.
        assert sum(w["count"] for w in data_a["interviews_over_time"]) == 2
        assert len(data_a["score_trend"]) == 1  # only finished interview has a score

        resp_b = client.get(
            "/api/v1/analytics/trends",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert resp_b.status_code == 200
        data_b = resp_b.json()
        assert data_b["interviews_over_time"] == []
        assert data_b["score_trend"] == []

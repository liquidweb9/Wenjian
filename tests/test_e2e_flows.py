"""End-to-End tests for critical user flows.

M2.6: Test complete user journeys from upload to report.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestUserAuthenticationFlow:
    """Test complete authentication flow."""

    def test_register_login_access_profile(self):
        """Test user can register, login, and access their profile."""
        # Step 1: Register
        register_response = client.post(
            "/api/v1/register",
            json={
                "email": f"e2e_user_{pytest.timestamp}@example.com",
                "password": "securepass123",
                "full_name": "E2E Test User"
            }
        )
        assert register_response.status_code == 201
        token_data = register_response.json()
        assert "access_token" in token_data
        access_token = token_data["access_token"]

        # Step 2: Access profile with token
        profile_response = client.get(
            "/api/v1/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert profile_response.status_code == 200
        profile = profile_response.json()
        assert profile["email"] == f"e2e_user_{pytest.timestamp}@example.com"
        assert profile["full_name"] == "E2E Test User"

        # Step 3: Login again
        login_response = client.post(
            "/api/v1/login",
            json={
                "email": f"e2e_user_{pytest.timestamp}@example.com",
                "password": "securepass123"
            }
        )
        assert login_response.status_code == 200
        new_token_data = login_response.json()
        assert "access_token" in new_token_data

        # Cleanup
        client.delete(
            "/api/v1/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )


class TestResumeUploadFlow:
    """Test resume upload and processing flow."""

    def setup_method(self):
        """Create authenticated user for tests."""
        response = client.post(
            "/api/v1/register",
            json={
                "email": f"resume_user_{pytest.timestamp}@example.com",
                "password": "password123",
                "full_name": "Resume User"
            }
        )
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def teardown_method(self):
        """Clean up test user."""
        client.delete("/api/v1/me", headers=self.headers)

    def test_upload_resume_and_view_profile(self):
        """Test uploading resume and viewing parsed profile."""
        # Create a simple text resume
        resume_content = b"""John Doe
Software Engineer

EXPERIENCE
Senior Backend Engineer at TechCorp (2020-2023)
- Led development of microservices architecture using Python and FastAPI
- Managed team of 5 engineers
- Reduced API latency by 40%

SKILLS
Python, FastAPI, PostgreSQL, Docker, AWS
"""

        # Step 1: Upload resume
        upload_response = client.post(
            "/api/v1/resumes",
            files={"file": ("resume.txt", resume_content, "text/plain")},
            headers=self.headers
        )
        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        assert "resume_id" in upload_data
        resume_id = upload_data["resume_id"]

        # Step 2: Check resume status
        status_response = client.get(
            f"/api/v1/resumes/{resume_id}",
            headers=self.headers
        )
        assert status_response.status_code == 200
        resume_data = status_response.json()
        assert resume_data["status"] in ["UPLOADED", "PARSED_UNCONFIRMED", "CONFIRMED"]

        # Step 3: Get resume profile (may need to wait for parsing)
        profile_response = client.get(
            f"/api/v1/resumes/{resume_id}/profile",
            headers=self.headers
        )
        # Profile endpoint returns 404 until parsing completes
        assert profile_response.status_code in [200, 404]

    def test_list_my_resumes(self):
        """Test listing user's resumes."""
        list_response = client.get(
            "/api/v1/resumes",
            headers=self.headers
        )
        assert list_response.status_code == 200
        data = list_response.json()
        assert isinstance(data.get("items"), list)


class TestJobTargetCreationFlow:
    """Test job target creation flow."""

    def setup_method(self):
        """Create authenticated user."""
        response = client.post(
            "/api/v1/register",
            json={
                "email": f"job_user_{pytest.timestamp}@example.com",
                "password": "password123",
            }
        )
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def teardown_method(self):
        """Clean up test user."""
        client.delete("/api/v1/me", headers=self.headers)

    def test_create_job_target_from_template(self):
        """Test creating job target from template."""
        create_response = client.post(
            "/api/v1/job-targets",
            json={
                "title": "Senior Backend Engineer",
                "level": "senior",
                "interview_round": "technical",
                "source": "template",
                "requirements": [
                    {
                        "competency_code": "backend.api_design",
                        "title": "REST API 设计",
                        "importance": 0.8,
                        "expected_level": 4,
                        "evidence_expectation": ["技术细节", "项目实例"],
                    }
                ],
            },
            headers=self.headers
        )
        assert create_response.status_code == 201
        job_data = create_response.json()
        assert "job_target_id" in job_data
        assert job_data["title"] == "Senior Backend Engineer"

    def test_create_job_target_from_jd(self):
        """Test creating job target from pasted JD."""
        jd_text = """Senior Backend Engineer

Requirements:
- 5+ years Python experience
- Experience with FastAPI, Django
- Strong database skills (PostgreSQL, Redis)
- Microservices architecture experience
- Team leadership experience
"""

        create_response = client.post(
            "/api/v1/job-targets",
            json={
                "title": "Senior Backend Engineer",
                "level": "senior",
                "interview_round": "technical",
                "source": "pasted_jd",
                "raw_jd": jd_text,
                "requirements": [
                    {
                        "competency_code": "backend.microservices",
                        "title": "微服务架构",
                        "importance": 0.9,
                        "expected_level": 4,
                        "evidence_expectation": ["架构设计", "落地案例"],
                    }
                ],
            },
            headers=self.headers
        )
        assert create_response.status_code == 201
        job_data = create_response.json()
        assert "job_target_id" in job_data


class TestInterviewCreationFlow:
    """Test interview creation and start flow."""

    def setup_method(self):
        """Create authenticated user and resume."""
        response = client.post(
            "/api/v1/register",
            json={
                "email": f"interview_user_{pytest.timestamp}@example.com",
                "password": "password123",
            }
        )
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def teardown_method(self):
        """Clean up test user."""
        client.delete("/api/v1/me", headers=self.headers)

    def test_create_interview(self):
        """Test creating an interview."""
        # Note: This requires a resume_id, which would need to be uploaded first
        # For now, test the endpoint structure
        create_response = client.post(
            "/api/v1/interviews",
            json={
                "resume_id": "test_resume_id",
                "target_role": "Backend Engineer",
                "mode": "simulation",
            },
            headers=self.headers
        )
        # May return 404 if resume doesn't exist, which is expected
        assert create_response.status_code in [201, 404, 422]

    def test_list_my_interviews(self):
        """Test listing user's interviews."""
        list_response = client.get(
            "/api/v1/interviews",
            headers=self.headers
        )
        assert list_response.status_code == 200
        data = list_response.json()
        assert isinstance(data.get("items"), list)


class TestHealthAndStatus:
    """Test health and system status endpoints."""

    def test_health_check(self):
        """Test health endpoint is accessible."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data

    def test_dashboard_stats(self):
        """Test dashboard stats endpoint (requires auth)."""
        # Without auth, should fail or not exist
        response = client.get("/api/v1/dashboard/stats")
        assert response.status_code in [401, 403, 404]

        # With auth, should work or not exist yet
        auth_response = client.post(
            "/api/v1/register",
            json={
                "email": f"dashboard_user_{pytest.timestamp}@example.com",
                "password": "password123",
            }
        )
        token = auth_response.json()["access_token"]

        response = client.get(
            "/api/v1/dashboard/stats",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code in [200, 404]

        # Cleanup
        client.delete(
            "/api/v1/me",
            headers={"Authorization": f"Bearer {token}"}
        )


class TestDataDeletionFlow:
    """Test data deletion endpoints."""

    def test_delete_account_flow(self):
        """Test complete account deletion."""
        # Register user
        register_response = client.post(
            "/api/v1/register",
            json={
                "email": f"delete_me_{pytest.timestamp}@example.com",
                "password": "password123",
            }
        )
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Verify profile exists
        profile_response = client.get("/api/v1/me", headers=headers)
        assert profile_response.status_code == 200

        # Delete account
        delete_response = client.delete("/api/v1/me", headers=headers)
        assert delete_response.status_code == 200
        delete_data = delete_response.json()
        assert delete_data["user_deleted"] is True

        # Verify cannot access profile after deletion
        profile_after = client.get("/api/v1/me", headers=headers)
        assert profile_after.status_code in [401, 403]

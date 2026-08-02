"""Tests for authentication system.

M2.6 Task #13: Tests for user registration, login, JWT tokens, and permissions.
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.core.ids import new_id
from app.persistence.models import User, ResumeSource, Interview
from app.persistence.repositories import (
    UserRepository,
    AuthResumeRepository as ResumeRepository,
    AuthInterviewRepository as InterviewRepository,
)
from app.core.exceptions import PermissionDeniedError


client = TestClient(app)


# ============================================================
# Password Hashing Tests
# ============================================================

class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_hash_password(self):
        """Test password hashing produces different hashes."""
        password = "testpassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Hashes should be different due to salt
        assert hash1 != hash2
        assert len(hash1) > 50  # bcrypt hashes are long

    def test_verify_correct_password(self):
        """Test verifying correct password."""
        password = "correctpassword"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_wrong_password(self):
        """Test verifying wrong password."""
        password = "correctpassword"
        wrong = "wrongpassword"
        hashed = hash_password(password)

        assert verify_password(wrong, hashed) is False

    def test_empty_password(self):
        """Test hashing empty password."""
        password = ""
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True
        assert verify_password("nonempty", hashed) is False


# ============================================================
# JWT Token Tests
# ============================================================

class TestJWTTokens:
    """Test JWT token creation and decoding."""

    def test_create_access_token(self):
        """Test creating access token."""
        user_id = "usr_test123"
        token = create_access_token({"sub": user_id})

        assert isinstance(token, str)
        assert len(token) > 50

    def test_decode_valid_token(self):
        """Test decoding valid token."""
        user_id = "usr_test456"
        token = create_access_token({"sub": user_id})

        payload = decode_access_token(token)

        assert payload is not None
        assert payload["sub"] == user_id
        assert "exp" in payload

    def test_decode_invalid_token(self):
        """Test decoding invalid token."""
        invalid_token = "invalid.jwt.token"

        payload = decode_access_token(invalid_token)

        assert payload is None

    def test_decode_expired_token(self):
        """Test decoding expired token."""
        user_id = "usr_expired"
        # Create token that expires immediately
        token = create_access_token({"sub": user_id}, expires_delta=timedelta(seconds=-1))

        payload = decode_access_token(token)

        # Expired tokens should return None
        assert payload is None

    def test_token_with_custom_expiration(self):
        """Test token with custom expiration."""
        user_id = "usr_custom"
        token = create_access_token({"sub": user_id}, expires_delta=timedelta(days=7))

        payload = decode_access_token(token)

        assert payload is not None
        assert payload["sub"] == user_id


# ============================================================
# Registration Tests
# ============================================================

class TestRegistration:
    """Test user registration endpoint."""

    def test_register_new_user(self):
        """Test registering a new user."""
        response = client.post(
            "/api/v1/register",
            json={
                "email": "newuser@example.com",
                "password": "securepassword123",
                "full_name": "New User"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_register_duplicate_email(self):
        """Test registering with existing email."""
        email = "duplicate@example.com"

        # First registration
        response1 = client.post(
            "/api/v1/register",
            json={
                "email": email,
                "password": "password1",
                "full_name": "First User"
            }
        )
        assert response1.status_code == 201

        # Second registration with same email
        response2 = client.post(
            "/api/v1/register",
            json={
                "email": email,
                "password": "password2",
                "full_name": "Second User"
            }
        )
        assert response2.status_code == 400
        assert "already registered" in response2.json()["detail"].lower()

    def test_register_invalid_email(self):
        """Test registering with invalid email."""
        response = client.post(
            "/api/v1/register",
            json={
                "email": "not-an-email",
                "password": "password123",
            }
        )

        assert response.status_code == 422  # Validation error

    def test_register_without_full_name(self):
        """Test registering without full name (optional field)."""
        response = client.post(
            "/api/v1/register",
            json={
                "email": "minimal@example.com",
                "password": "password123",
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data


# ============================================================
# Login Tests
# ============================================================

class TestLogin:
    """Test user login endpoint."""

    def test_login_success(self):
        """Test successful login."""
        email = "logintest@example.com"
        password = "testpassword"

        # Register user
        client.post(
            "/api/v1/register",
            json={"email": email, "password": password}
        )

        # Login
        response = client.post(
            "/api/v1/login",
            json={"email": email, "password": password}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self):
        """Test login with wrong password."""
        email = "wrongpwd@example.com"
        password = "correctpassword"

        # Register user
        client.post(
            "/api/v1/register",
            json={"email": email, "password": password}
        )

        # Login with wrong password
        response = client.post(
            "/api/v1/login",
            json={"email": email, "password": "wrongpassword"}
        )

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self):
        """Test login with non-existent email."""
        response = client.post(
            "/api/v1/login",
            json={
                "email": "nonexistent@example.com",
                "password": "anypassword"
            }
        )

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()


# ============================================================
# Get Current User Tests
# ============================================================

class TestGetCurrentUser:
    """Test getting current user profile."""

    def test_get_me_with_valid_token(self):
        """Test getting user profile with valid token."""
        email = "getme@example.com"
        password = "password123"

        # Register user
        register_response = client.post(
            "/api/v1/register",
            json={"email": email, "password": password, "full_name": "Test User"}
        )
        token = register_response.json()["access_token"]

        # Get profile
        response = client.get(
            "/api/v1/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == email
        assert data["full_name"] == "Test User"
        assert data["is_active"] is True
        assert "user_id" in data
        assert "created_at" in data

    def test_get_me_without_token(self):
        """Test getting profile without token."""
        response = client.get("/api/v1/me")

        assert response.status_code == 401
        assert "missing" in response.json()["detail"].lower()

    def test_get_me_with_invalid_token(self):
        """Test getting profile with invalid token."""
        response = client.get(
            "/api/v1/me",
            headers={"Authorization": "Bearer invalid.token.here"}
        )

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()


# ============================================================
# Repository Permission Tests
# ============================================================

@pytest.mark.asyncio
class TestResumePermissions:
    """Test resume repository enforces ownership."""

    async def test_get_own_resume(self, async_session: AsyncSession):
        """Test user can get their own resume."""
        user_id = new_id("user")
        resume_id = new_id("resume")

        # Create user
        user_repo = UserRepository(async_session)
        user = User(
            user_id=user_id,
            email="owner@example.com",
            hashed_password=hash_password("password"),
        )
        await user_repo.create(user)

        # Create resume owned by user
        resume_repo = ResumeRepository(async_session)
        resume = ResumeSource(
            resume_id=resume_id,
            user_id=user_id,
            source_id="src1",
            file_name="resume.pdf",
            source_type="PDF",
        )
        await resume_repo.create(resume)
        await async_session.commit()

        # User should be able to get their resume
        retrieved = await resume_repo.get_by_id(resume_id, user_id)
        assert retrieved is not None
        assert retrieved.resume_id == resume_id

    async def test_cannot_get_other_user_resume(self, async_session: AsyncSession):
        """Test user cannot get another user's resume."""
        owner_id = new_id("user")
        other_id = new_id("user")
        resume_id = new_id("resume")

        # Create owner
        user_repo = UserRepository(async_session)
        owner = User(
            user_id=owner_id,
            email="owner@example.com",
            hashed_password=hash_password("password"),
        )
        await user_repo.create(owner)

        # Create resume owned by owner
        resume_repo = ResumeRepository(async_session)
        resume = ResumeSource(
            resume_id=resume_id,
            user_id=owner_id,
            source_id="src1",
            file_name="resume.pdf",
            source_type="PDF",
        )
        await resume_repo.create(resume)
        await async_session.commit()

        # Other user should NOT be able to get this resume
        retrieved = await resume_repo.get_by_id(resume_id, other_id)
        assert retrieved is None

    async def test_list_only_own_resumes(self, async_session: AsyncSession):
        """Test user only sees their own resumes in list."""
        user1_id = new_id("user")
        user2_id = new_id("user")

        # Create users
        user_repo = UserRepository(async_session)
        user1 = User(user_id=user1_id, email="user1@example.com", hashed_password=hash_password("pwd"))
        user2 = User(user_id=user2_id, email="user2@example.com", hashed_password=hash_password("pwd"))
        await user_repo.create(user1)
        await user_repo.create(user2)

        # Create resumes for both users
        resume_repo = ResumeRepository(async_session)
        resume1 = ResumeSource(
            resume_id=new_id("resume"),
            user_id=user1_id,
            source_id="src1",
            file_name="resume1.pdf",
            source_type="PDF",
        )
        resume2 = ResumeSource(
            resume_id=new_id("resume"),
            user_id=user2_id,
            source_id="src2",
            file_name="resume2.pdf",
            source_type="PDF",
        )
        await resume_repo.create(resume1)
        await resume_repo.create(resume2)
        await async_session.commit()

        # User1 should only see their resume
        user1_resumes = await resume_repo.list_by_user(user1_id)
        assert len(user1_resumes) == 1
        assert user1_resumes[0].resume_id == resume1.resume_id

        # User2 should only see their resume
        user2_resumes = await resume_repo.list_by_user(user2_id)
        assert len(user2_resumes) == 1
        assert user2_resumes[0].resume_id == resume2.resume_id


@pytest.mark.asyncio
class TestInterviewPermissions:
    """Test interview repository enforces ownership."""

    async def test_get_own_interview(self, async_session: AsyncSession):
        """Test user can get their own interview."""
        user_id = new_id("user")
        resume_id = new_id("resume")
        interview_id = new_id("interview")

        # Create user and resume
        user_repo = UserRepository(async_session)
        user = User(user_id=user_id, email="owner@example.com", hashed_password=hash_password("pwd"))
        await user_repo.create(user)

        resume_repo = ResumeRepository(async_session)
        resume = ResumeSource(
            resume_id=resume_id,
            user_id=user_id,
            source_id="src1",
            file_name="resume.pdf",
            source_type="PDF",
        )
        await resume_repo.create(resume)

        # Create interview owned by user
        interview_repo = InterviewRepository(async_session)
        interview = Interview(
            interview_id=interview_id,
            user_id=user_id,
            thread_id=new_id("thread"),
            resume_id=resume_id,
            target_role="Backend Engineer",
        )
        await interview_repo.create(interview)
        await async_session.commit()

        # User should be able to get their interview
        retrieved = await interview_repo.get_by_id(interview_id, user_id)
        assert retrieved is not None
        assert retrieved.interview_id == interview_id

    async def test_cannot_get_other_user_interview(self, async_session: AsyncSession):
        """Test user cannot get another user's interview."""
        owner_id = new_id("user")
        other_id = new_id("user")
        resume_id = new_id("resume")
        interview_id = new_id("interview")

        # Create owner and resume
        user_repo = UserRepository(async_session)
        owner = User(user_id=owner_id, email="owner@example.com", hashed_password=hash_password("pwd"))
        await user_repo.create(owner)

        resume_repo = ResumeRepository(async_session)
        resume = ResumeSource(
            resume_id=resume_id,
            user_id=owner_id,
            source_id="src1",
            file_name="resume.pdf",
            source_type="PDF",
        )
        await resume_repo.create(resume)

        # Create interview owned by owner
        interview_repo = InterviewRepository(async_session)
        interview = Interview(
            interview_id=interview_id,
            user_id=owner_id,
            thread_id=new_id("thread"),
            resume_id=resume_id,
            target_role="Backend Engineer",
        )
        await interview_repo.create(interview)
        await async_session.commit()

        # Other user should NOT be able to get this interview
        retrieved = await interview_repo.get_by_id(interview_id, other_id)
        assert retrieved is None


# ============================================================
# Horizontal Privilege Escalation Tests
# ============================================================

class TestHorizontalPrivilegeEscalation:
    """Test that users cannot access each other's data (horizontal privilege escalation prevention)."""

    def test_cannot_access_other_user_resume_via_api(self):
        """Test user cannot access another user's resume via API."""
        # User 1 registers and uploads resume
        user1_response = client.post(
            "/api/v1/register",
            json={"email": "user1@test.com", "password": "pwd1"}
        )
        user1_token = user1_response.json()["access_token"]

        upload_response = client.post(
            "/api/v1/resumes/upload",
            headers={"Authorization": f"Bearer {user1_token}"},
            files={"file": ("resume.txt", b"Test resume content", "text/plain")}
        )
        resume_id = upload_response.json()["resume_id"]

        # User 2 registers
        user2_response = client.post(
            "/api/v1/register",
            json={"email": "user2@test.com", "password": "pwd2"}
        )
        user2_token = user2_response.json()["access_token"]

        # User 2 tries to access User 1's resume
        access_response = client.get(
            f"/api/v1/resumes/{resume_id}",
            headers={"Authorization": f"Bearer {user2_token}"}
        )

        # Should return 404 (not found) or 403 (forbidden)
        assert access_response.status_code in [403, 404]

    def test_cannot_access_other_user_interview_via_api(self):
        """Test user cannot access another user's interview via API."""
        # This test would follow similar pattern as above
        # Create interview for user1, try to access with user2's token
        # Expected: 403 or 404
        pass  # Implement when interview API endpoints are updated

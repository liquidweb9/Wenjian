"""End-to-End tests for critical user flows using async client.

M2.6: Test complete user journeys with proper async support.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
class TestUserAuthenticationFlow:
    """Test complete authentication flow."""

    async def test_register_login_access_profile(self):
        """Test user can register, login, and access their profile."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Step 1: Register
            register_response = await client.post(
                "/api/v1/register",
                json={
                    "email": f"e2e_async_user_{pytest.timestamp}@example.com",
                    "password": "securepass123",
                    "full_name": "E2E Async Test User"
                }
            )
            assert register_response.status_code == 201, f"Register failed: {register_response.text}"
            token_data = register_response.json()
            assert "access_token" in token_data
            access_token = token_data["access_token"]

            # Step 2: Access profile with token
            profile_response = await client.get(
                "/api/v1/me",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            assert profile_response.status_code == 200
            profile = profile_response.json()
            assert "e2e_async_user" in profile["email"]
            assert profile["full_name"] == "E2E Async Test User"

            # Step 3: Login again
            login_response = await client.post(
                "/api/v1/login",
                json={
                    "email": profile["email"],
                    "password": "securepass123"
                }
            )
            assert login_response.status_code == 200
            new_token_data = login_response.json()
            assert "access_token" in new_token_data

            # Cleanup
            delete_response = await client.delete(
                "/api/v1/me",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            assert delete_response.status_code == 200


@pytest.mark.asyncio
class TestHealthAndStatus:
    """Test health and system status endpoints."""

    async def test_health_check(self):
        """Test health endpoint is accessible."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert "version" in data

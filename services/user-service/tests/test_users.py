import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select

from app.models.user import User


@pytest_asyncio.fixture
async def authenticated_user_and_token(test_client: AsyncClient):
    """Create user and return user data with access token."""
    user_data = {
        "email": "auth_user@example.com",
        "password": "password123",
        "full_name": "Authenticated User"
    }
    
    # Signup
    signup_response = await test_client.post("/auth/signup", json=user_data)
    assert signup_response.status_code == 200
    user = signup_response.json()
    
    # Login
    login_data = {
        "username": user_data["email"],
        "password": user_data["password"]
    }
    login_response = await test_client.post("/auth/login", data=login_data)
    assert login_response.status_code == 200
    token_data = login_response.json()
    
    return {
        "user": user,
        "token": token_data["access_token"],
        "headers": {"Authorization": f"Bearer {token_data['access_token']}"}
    }


class TestUsers:
    """Test user management endpoints."""

    @pytest.mark.asyncio
    async def test_get_me_with_token(self, test_client: AsyncClient, authenticated_user_and_token: dict):
        """Test accessing /users/me with valid token."""
        auth_data = authenticated_user_and_token
        
        response = await test_client.get("/users/me", headers=auth_data["headers"])
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == auth_data["user"]["id"]
        assert data["email"] == auth_data["user"]["email"]
        assert data["full_name"] == auth_data["user"]["full_name"]
        assert data["is_active"] == auth_data["user"]["is_active"]
        assert data["is_admin"] == auth_data["user"]["is_admin"]

    @pytest.mark.asyncio
    async def test_get_me_without_token(self, test_client: AsyncClient):
        """Test accessing /users/me without token."""
        response = await test_client.get("/users/me")
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_me_with_invalid_token(self, test_client: AsyncClient):
        """Test accessing /users/me with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = await test_client.get("/users/me", headers=headers)
        
        assert response.status_code == 401
        assert "Invalid authentication credentials" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_me_with_malformed_token(self, test_client: AsyncClient):
        """Test accessing /users/me with malformed token."""
        headers = {"Authorization": "InvalidBearer token"}
        response = await test_client.get("/users/me", headers=headers)
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_me_full_name(self, test_client: AsyncClient, authenticated_user_and_token: dict):
        """Test updating user's full name."""
        auth_data = authenticated_user_and_token
        
        update_data = {"full_name": "Updated Full Name"}
        response = await test_client.put("/users/me", json=update_data, headers=auth_data["headers"])
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Full Name"
        assert data["id"] == auth_data["user"]["id"]
        assert data["email"] == auth_data["user"]["email"]

    @pytest.mark.asyncio
    async def test_update_me_is_active(self, test_client: AsyncClient, authenticated_user_and_token: dict):
        """Test updating user's active status."""
        auth_data = authenticated_user_and_token
        
        update_data = {"is_active": False}
        response = await test_client.put("/users/me", json=update_data, headers=auth_data["headers"])
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False
        assert data["id"] == auth_data["user"]["id"]

    @pytest.mark.asyncio
    async def test_update_me_multiple_fields(self, test_client: AsyncClient, authenticated_user_and_token: dict):
        """Test updating multiple user fields."""
        auth_data = authenticated_user_and_token
        
        update_data = {
            "full_name": "Completely New Name",
            "is_active": True
        }
        response = await test_client.put("/users/me", json=update_data, headers=auth_data["headers"])
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Completely New Name"
        assert data["is_active"] is True
        assert data["id"] == auth_data["user"]["id"]

    @pytest.mark.asyncio
    async def test_update_me_empty_update(self, test_client: AsyncClient, authenticated_user_and_token: dict):
        """Test updating with no fields (should return current user)."""
        auth_data = authenticated_user_and_token
        
        update_data = {}
        response = await test_client.put("/users/me", json=update_data, headers=auth_data["headers"])
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == auth_data["user"]["id"]
        assert data["email"] == auth_data["user"]["email"]
        # Should keep original full_name
        assert data["full_name"] == auth_data["user"]["full_name"]

    @pytest.mark.asyncio
    async def test_update_me_without_token(self, test_client: AsyncClient):
        """Test updating user profile without token."""
        update_data = {"full_name": "Unauthorized Update"}
        response = await test_client.put("/users/me", json=update_data)
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_me_with_invalid_token(self, test_client: AsyncClient):
        """Test updating user profile with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        update_data = {"full_name": "Unauthorized Update"}
        response = await test_client.put("/users/me", json=update_data, headers=headers)
        
        assert response.status_code == 401
        assert "Invalid authentication credentials" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_me_read_only_fields(self, test_client: AsyncClient, authenticated_user_and_token: dict):
        """Test that read-only fields are not updatable through /users/me."""
        auth_data = authenticated_user_and_token
        original_email = auth_data["user"]["email"]
        original_id = auth_data["user"]["id"]
        
        # Try to update email and id (should be ignored)
        update_data = {
            "email": "newemail@example.com",
            "id": 999,
            "full_name": "Updated Name"
        }
        response = await test_client.put("/users/me", json=update_data, headers=auth_data["headers"])
        
        assert response.status_code == 200
        data = response.json()
        
        # Email and ID should remain unchanged
        assert data["email"] == original_email
        assert data["id"] == original_id
        # But full_name should be updated
        assert data["full_name"] == "Updated Name"

    @pytest.mark.asyncio 
    async def test_user_persistence(self, test_client: AsyncClient, authenticated_user_and_token: dict):
        """Test that user updates persist between requests."""
        auth_data = authenticated_user_and_token
        
        # Update user
        update_data = {"full_name": "Persistent Name"}
        update_response = await test_client.put("/users/me", json=update_data, headers=auth_data["headers"])
        assert update_response.status_code == 200
        
        # Get user again to verify persistence
        get_response = await test_client.get("/users/me", headers=auth_data["headers"])
        assert get_response.status_code == 200
        
        data = get_response.json()
        assert data["full_name"] == "Persistent Name"

"""
Authentication tests for TalentSync Auth Gateway Service.

Comprehensive test suite for authentication endpoints including
user registration, login, logout, and token validation.
"""
import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient

from app.main import app
from app.schemas.auth import UserSignupRequest, UserLoginRequest


class TestAuthEndpoints:
    """Test suite for authentication endpoints."""
    
    @pytest.mark.asyncio
    async def test_signup_user_success(self, async_client: AsyncClient, valid_user_data: dict):
        """
        Test successful user registration.
        
        Args:
            async_client: Async HTTP client
            valid_user_data: Valid user registration data
        """
        with patch("app.routers.auth.supabase_service") as mock_service:
            # Mock successful signup
            mock_service.signup_user.return_value = (
                True,
                {
                    "id": "test-user-id",
                    "email": valid_user_data["email"],
                    "full_name": valid_user_data["full_name"],
                    "is_active": True,
                    "is_admin": False,
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                },
                None
            )
            
            # Mock successful login after signup
            mock_service.login_user.return_value = (
                True,
                {
                    "access_token": "test-access-token",
                    "token_type": "bearer",
                    "expires_in": 3600,
                    "user": {
                        "id": "test-user-id",
                        "email": valid_user_data["email"],
                        "full_name": valid_user_data["full_name"],
                        "is_active": True,
                        "is_admin": False,
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z",
                    }
                },
                None
            )
            
            response = await async_client.post("/auth/signup", json=valid_user_data)
            
            assert response.status_code == 201
            data = response.json()
            assert data["access_token"] == "test-access-token"
            assert data["token_type"] == "bearer"
            assert data["user"]["email"] == valid_user_data["email"]
            assert data["user"]["full_name"] == valid_user_data["full_name"]
    
    @pytest.mark.asyncio
    async def test_signup_user_already_exists(self, async_client: AsyncClient, valid_user_data: dict):
        """
        Test user registration with existing email.
        
        Args:
            async_client: Async HTTP client
            valid_user_data: Valid user registration data
        """
        with patch("app.routers.auth.supabase_service") as mock_service:
            # Mock user already exists
            mock_service.signup_user.return_value = (
                False,
                None,
                "User already registered"
            )
            
            response = await async_client.post("/auth/signup", json=valid_user_data)
            
            assert response.status_code == 409
            data = response.json()
            assert "already exists" in data["error"]
    
    @pytest.mark.asyncio
    async def test_signup_user_invalid_data(self, async_client: AsyncClient):
        """
        Test user registration with invalid data.
        
        Args:
            async_client: Async HTTP client
        """
        invalid_data = {
            "email": "invalid-email",
            "password": "weak",
            "full_name": ""
        }
        
        response = await async_client.post("/auth/signup", json=invalid_data)
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_login_user_success(self, async_client: AsyncClient, valid_login_data: dict):
        """
        Test successful user login.
        
        Args:
            async_client: Async HTTP client
            valid_login_data: Valid user login data
        """
        with patch("app.routers.auth.supabase_service") as mock_service:
            # Mock successful login
            mock_service.login_user.return_value = (
                True,
                {
                    "access_token": "test-access-token",
                    "token_type": "bearer",
                    "expires_in": 3600,
                    "user": {
                        "id": "test-user-id",
                        "email": valid_login_data["email"],
                        "full_name": "Test User",
                        "is_active": True,
                        "is_admin": False,
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z",
                    }
                },
                None
            )
            
            response = await async_client.post("/auth/login", json=valid_login_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["access_token"] == "test-access-token"
            assert data["token_type"] == "bearer"
            assert data["user"]["email"] == valid_login_data["email"]
    
    @pytest.mark.asyncio
    async def test_login_user_invalid_credentials(self, async_client: AsyncClient):
        """
        Test user login with invalid credentials.
        
        Args:
            async_client: Async HTTP client
        """
        with patch("app.routers.auth.supabase_service") as mock_service:
            # Mock failed login
            mock_service.login_user.return_value = (
                False,
                None,
                "Invalid credentials"
            )
            
            response = await async_client.post("/auth/login", json={
                "email": "test@example.com",
                "password": "wrongpassword"
            })
            
            assert response.status_code == 401
            data = response.json()
            assert "Invalid email or password" in data["error"]
    
    @pytest.mark.asyncio
    async def test_login_user_inactive_account(self, async_client: AsyncClient, valid_login_data: dict):
        """
        Test user login with inactive account.
        
        Args:
            async_client: Async HTTP client
            valid_login_data: Valid user login data
        """
        with patch("app.routers.auth.supabase_service") as mock_service:
            # Mock login with inactive user
            mock_service.login_user.return_value = (
                True,
                {
                    "access_token": "test-access-token",
                    "token_type": "bearer",
                    "expires_in": 3600,
                    "user": {
                        "id": "test-user-id",
                        "email": valid_login_data["email"],
                        "full_name": "Test User",
                        "is_active": False,  # Inactive user
                        "is_admin": False,
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z",
                    }
                },
                None
            )
            
            response = await async_client.post("/auth/login", json=valid_login_data)
            
            assert response.status_code == 403
            data = response.json()
            assert "Account is inactive" in data["error"]
    
    @pytest.mark.asyncio
    async def test_logout_user_success(self, async_client: AsyncClient, valid_token: str):
        """
        Test successful user logout.
        
        Args:
            async_client: Async HTTP client
            valid_token: Valid JWT token
        """
        with patch("app.routers.auth.supabase_service") as mock_service:
            # Mock successful logout
            mock_service.logout_user.return_value = (True, None)
            
            response = await async_client.post(
                "/auth/logout",
                headers={"Authorization": f"Bearer {valid_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Logout successful"
    
    @pytest.mark.asyncio
    async def test_logout_user_no_token(self, async_client: AsyncClient):
        """
        Test user logout without token.
        
        Args:
            async_client: Async HTTP client
        """
        response = await async_client.post("/auth/logout")
        
        assert response.status_code == 401
        data = response.json()
        assert "Authentication credentials required" in data["error"]
    
    @pytest.mark.asyncio
    async def test_get_current_user_success(self, async_client: AsyncClient, valid_token: str):
        """
        Test successful current user retrieval.
        
        Args:
            async_client: Async HTTP client
            valid_token: Valid JWT token
        """
        with patch("app.routers.auth.supabase_service") as mock_service:
            # Mock successful token validation
            mock_service.validate_token.return_value = (
                True,
                {
                    "id": "test-user-id",
                    "email": "test@example.com",
                    "full_name": "Test User",
                    "is_active": True,
                    "is_admin": False,
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                },
                None
            )
            
            response = await async_client.get(
                "/auth/me",
                headers={"Authorization": f"Bearer {valid_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == "test@example.com"
            assert data["full_name"] == "Test User"
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, async_client: AsyncClient):
        """
        Test current user retrieval with invalid token.
        
        Args:
            async_client: Async HTTP client
        """
        with patch("app.routers.auth.supabase_service") as mock_service:
            # Mock failed token validation
            mock_service.validate_token.return_value = (
                False,
                None,
                "Invalid token"
            )
            
            response = await async_client.get(
                "/auth/me",
                headers={"Authorization": "Bearer invalid-token"}
            )
            
            assert response.status_code == 401
            data = response.json()
            assert "Invalid or expired token" in data["error"]
    
    @pytest.mark.asyncio
    async def test_get_current_user_no_token(self, async_client: AsyncClient):
        """
        Test current user retrieval without token.
        
        Args:
            async_client: Async HTTP client
        """
        response = await async_client.get("/auth/me")
        
        assert response.status_code == 401
        data = response.json()
        assert "Authentication credentials required" in data["error"]


class TestUserEndpoints:
    """Test suite for user management endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_my_profile_success(self, async_client: AsyncClient, valid_token: str):
        """
        Test successful profile retrieval.
        
        Args:
            async_client: Async HTTP client
            valid_token: Valid JWT token
        """
        with patch("app.routers.users.supabase_service") as mock_service:
            # Mock successful profile retrieval
            mock_service.get_user_profile.return_value = (
                True,
                {
                    "id": "test-user-id",
                    "email": "test@example.com",
                    "full_name": "Test User",
                    "is_active": True,
                    "is_admin": False,
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                },
                None
            )
            
            response = await async_client.get(
                "/users/me",
                headers={"Authorization": f"Bearer {valid_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == "test@example.com"
            assert data["full_name"] == "Test User"
    
    @pytest.mark.asyncio
    async def test_update_my_profile_success(self, async_client: AsyncClient, valid_token: str):
        """
        Test successful profile update.
        
        Args:
            async_client: Async HTTP client
            valid_token: Valid JWT token
        """
        with patch("app.routers.users.supabase_service") as mock_service:
            # Mock successful profile update
            mock_service.update_user_profile.return_value = (
                True,
                {
                    "id": "test-user-id",
                    "email": "test@example.com",
                    "full_name": "Updated Test User",
                    "is_active": True,
                    "is_admin": False,
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                },
                None
            )
            
            update_data = {"full_name": "Updated Test User"}
            response = await async_client.put(
                "/users/me",
                json=update_data,
                headers={"Authorization": f"Bearer {valid_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["full_name"] == "Updated Test User"
    
    @pytest.mark.asyncio
    async def test_update_my_profile_no_updates(self, async_client: AsyncClient, valid_token: str):
        """
        Test profile update with no valid updates.
        
        Args:
            async_client: Async HTTP client
            valid_token: Valid JWT token
        """
        update_data = {}
        response = await async_client.put(
            "/users/me",
            json=update_data,
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "No valid updates provided" in data["error"]


class TestDependencies:
    """Test suite for FastAPI dependencies."""
    
    @pytest.mark.asyncio
    async def test_get_current_user_success(self, valid_token: str):
        """
        Test successful current user dependency.
        
        Args:
            valid_token: Valid JWT token
        """
        from app.dependencies import get_current_user
        from fastapi.security import HTTPAuthorizationCredentials
        
        with patch("app.dependencies.supabase_service") as mock_service:
            # Mock successful token validation
            mock_service.validate_token.return_value = (
                True,
                {
                    "id": "test-user-id",
                    "email": "test@example.com",
                    "full_name": "Test User",
                    "is_active": True,
                    "is_admin": False,
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                },
                None
            )
            
            credentials = HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials=valid_token
            )
            
            user = await get_current_user(credentials)
            assert user.email == "test@example.com"
            assert user.full_name == "Test User"
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """
        Test current user dependency with invalid token.
        """
        from app.dependencies import get_current_user
        from fastapi.security import HTTPAuthorizationCredentials
        from fastapi import HTTPException
        
        with patch("app.dependencies.supabase_service") as mock_service:
            # Mock failed token validation
            mock_service.validate_token.return_value = (
                False,
                None,
                "Invalid token"
            )
            
            credentials = HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials="invalid-token"
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials)
            
            assert exc_info.value.status_code == 401 
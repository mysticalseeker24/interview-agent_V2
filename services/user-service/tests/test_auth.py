import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select

from app.models.user import User


@pytest_asyncio.fixture
async def test_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }


@pytest_asyncio.fixture
async def duplicate_user_data():
    """Sample user data for duplicate email testing."""
    return {
        "email": "duplicate@example.com",
        "password": "password123",
        "full_name": "Duplicate User"
    }


class TestAuth:
    """Test authentication endpoints."""

    @pytest.mark.asyncio
    async def test_successful_signup(self, test_client: AsyncClient, test_user_data: dict):
        """Test successful user registration."""
        response = await test_client.post("/auth/signup", json=test_user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["full_name"] == test_user_data["full_name"]
        assert data["is_active"] is True
        assert data["is_admin"] is False
        assert "id" in data
        assert "hashed_password" not in data  # Should not expose password

    @pytest.mark.asyncio
    async def test_duplicate_email_signup(self, test_client: AsyncClient, test_user_data: dict):
        """Test signup with duplicate email."""
        # First signup
        response1 = await test_client.post("/auth/signup", json=test_user_data)
        assert response1.status_code == 200

        # Second signup with same email
        response2 = await test_client.post("/auth/signup", json=test_user_data)
        assert response2.status_code == 400
        assert "Email already registered" in response2.json()["detail"]

    @pytest.mark.asyncio
    async def test_invalid_email_signup(self, test_client: AsyncClient):
        """Test signup with invalid email."""
        invalid_data = {
            "email": "not-an-email",
            "password": "testpassword123",
            "full_name": "Test User"
        }
        response = await test_client.post("/auth/signup", json=invalid_data)
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_missing_password_signup(self, test_client: AsyncClient):
        """Test signup without password."""
        invalid_data = {
            "email": "test@example.com",
            "full_name": "Test User"
        }
        response = await test_client.post("/auth/signup", json=invalid_data)
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_successful_login(self, test_client: AsyncClient, test_user_data: dict):
        """Test successful login."""
        # First create a user
        signup_response = await test_client.post("/auth/signup", json=test_user_data)
        assert signup_response.status_code == 200

        # Then login
        login_data = {
            "username": test_user_data["email"],  # OAuth2PasswordRequestForm uses 'username'
            "password": test_user_data["password"]
        }
        response = await test_client.post("/auth/login", data=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    @pytest.mark.asyncio
    async def test_login_bad_email(self, test_client: AsyncClient, test_user_data: dict):
        """Test login with incorrect email."""
        # First create a user
        signup_response = await test_client.post("/auth/signup", json=test_user_data)
        assert signup_response.status_code == 200

        # Login with wrong email
        login_data = {
            "username": "wrong@example.com",
            "password": test_user_data["password"]
        }
        response = await test_client.post("/auth/login", data=login_data)
        
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_bad_password(self, test_client: AsyncClient, test_user_data: dict):
        """Test login with incorrect password."""
        # First create a user
        signup_response = await test_client.post("/auth/signup", json=test_user_data)
        assert signup_response.status_code == 200

        # Login with wrong password
        login_data = {
            "username": test_user_data["email"],
            "password": "wrongpassword"
        }
        response = await test_client.post("/auth/login", data=login_data)
        
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, test_client: AsyncClient):
        """Test login with non-existent user."""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "password123"
        }
        response = await test_client.post("/auth/login", data=login_data)
        
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_missing_credentials(self, test_client: AsyncClient):
        """Test login without credentials."""
        response = await test_client.post("/auth/login", data={})
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_full_auth_flow(self, test_client: AsyncClient, test_user_data: dict):
        """Test complete signup -> login -> access protected endpoint flow."""
        # 1. Signup
        signup_response = await test_client.post("/auth/signup", json=test_user_data)
        assert signup_response.status_code == 200
        user_data = signup_response.json()
        
        # 2. Login
        login_data = {
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        }
        login_response = await test_client.post("/auth/login", data=login_data)
        assert login_response.status_code == 200
        token_data = login_response.json()
        
        # 3. Access protected endpoint
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        me_response = await test_client.get("/users/me", headers=headers)
        assert me_response.status_code == 200
        
        me_data = me_response.json()
        assert me_data["id"] == user_data["id"]
        assert me_data["email"] == user_data["email"]

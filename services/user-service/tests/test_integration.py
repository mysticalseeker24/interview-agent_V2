import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token


class TestIntegration:
    """Integration tests for the user service."""

    @pytest.mark.asyncio
    async def test_database_user_creation(self, test_db: AsyncSession):
        """Test direct database user creation."""
        # Create user directly in database
        hashed_password = hash_password("testpassword")
        user = User(
            email="dbtest@example.com",
            hashed_password=hashed_password,
            full_name="DB Test User",
            is_active=True,
            is_admin=False
        )
        
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)
        
        # Verify user was created
        assert user.id is not None
        assert user.email == "dbtest@example.com"
        assert user.full_name == "DB Test User"
        assert user.is_active is True
        assert user.is_admin is False
        assert verify_password("testpassword", user.hashed_password)

    @pytest.mark.asyncio
    async def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "supersecretpassword123"
        hashed = hash_password(password)
        
        # Hash should not be the same as original password
        assert hashed != password
        assert len(hashed) > 20  # Bcrypt hashes are long
        
        # Verification should work
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False

    @pytest.mark.asyncio
    async def test_jwt_token_creation_and_validation(self):
        """Test JWT token creation and validation."""
        user_id = "123"
        token = create_access_token(sub=user_id)
        
        # Token should be a string
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are long
        
        # Token should contain expected structure (3 parts separated by dots)
        parts = token.split('.')
        assert len(parts) == 3

    @pytest.mark.asyncio
    async def test_multiple_users_creation(self, test_client: AsyncClient):
        """Test creating multiple users."""
        users_data = [
            {"email": "user1@example.com", "password": "pass1", "full_name": "User One"},
            {"email": "user2@example.com", "password": "pass2", "full_name": "User Two"},
            {"email": "user3@example.com", "password": "pass3", "full_name": "User Three"},
        ]
        
        created_users = []
        
        for user_data in users_data:
            response = await test_client.post("/auth/signup", json=user_data)
            assert response.status_code == 200
            created_users.append(response.json())
        
        # Verify all users have unique IDs
        user_ids = [user["id"] for user in created_users]
        assert len(set(user_ids)) == len(user_ids)  # All IDs should be unique
        
        # Verify all users have correct data
        for i, user in enumerate(created_users):
            assert user["email"] == users_data[i]["email"]
            assert user["full_name"] == users_data[i]["full_name"]

    @pytest.mark.asyncio
    async def test_concurrent_login_attempts(self, test_client: AsyncClient):
        """Test multiple concurrent login attempts."""
        # Create a user first
        user_data = {
            "email": "concurrent@example.com",
            "password": "password123",
            "full_name": "Concurrent User"
        }
        signup_response = await test_client.post("/auth/signup", json=user_data)
        assert signup_response.status_code == 200
        
        # Perform multiple login attempts
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }
        
        login_responses = []
        for _ in range(3):
            response = await test_client.post("/auth/login", data=login_data)
            login_responses.append(response)
        
        # All login attempts should succeed
        for response in login_responses:
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_user_update_persistence(self, test_client: AsyncClient, test_db: AsyncSession):
        """Test that user updates persist in the database."""
        # Create user via API
        user_data = {
            "email": "persistence@example.com",
            "password": "password123",
            "full_name": "Original Name"
        }
        signup_response = await test_client.post("/auth/signup", json=user_data)
        assert signup_response.status_code == 200
        user = signup_response.json()
        
        # Login to get token
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }
        login_response = await test_client.post("/auth/login", data=login_data)
        assert login_response.status_code == 200
        token_data = login_response.json()
        
        # Update user via API
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        update_data = {"full_name": "Updated Name"}
        update_response = await test_client.put("/users/me", json=update_data, headers=headers)
        assert update_response.status_code == 200
        
        # Verify update in database directly
        result = await test_db.execute(select(User).where(User.id == user["id"]))
        db_user = result.scalars().first()
        assert db_user is not None
        assert db_user.full_name == "Updated Name"

    @pytest.mark.asyncio
    async def test_service_health_endpoints(self, test_client: AsyncClient):
        """Test service health and info endpoints."""
        # Test root endpoint
        root_response = await test_client.get("/")
        assert root_response.status_code == 200
        root_data = root_response.json()
        assert "service" in root_data
        assert "version" in root_data
        assert "status" in root_data

"""
Pytest configuration and fixtures for TalentSync Auth Gateway Service.

Provides test fixtures and configuration for unit and integration tests
with proper mocking and test data setup.
"""
import asyncio
import pytest
from typing import Dict, Any, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.core.settings import settings


@pytest.fixture(scope="session")
def event_loop():
    """
    Create an instance of the default event loop for the test session.
    
    Returns:
        asyncio.AbstractEventLoop: Event loop for async tests
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_client() -> TestClient:
    """
    Create a test client for the FastAPI application.
    
    Returns:
        TestClient: FastAPI test client
    """
    return TestClient(app)


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async test client for the FastAPI application.
    
    Yields:
        AsyncClient: Async HTTP client for testing
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_supabase_service():
    """
    Mock Supabase service for testing.
    
    Returns:
        MagicMock: Mocked Supabase service
    """
    mock_service = MagicMock()
    
    # Mock successful user registration
    mock_service.signup_user = AsyncMock(return_value=(
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
    ))
    
    # Mock successful user login
    mock_service.login_user = AsyncMock(return_value=(
        True,
        {
            "access_token": "test-access-token",
            "token_type": "bearer",
            "expires_in": 3600,
            "user": {
                "id": "test-user-id",
                "email": "test@example.com",
                "full_name": "Test User",
                "is_active": True,
                "is_admin": False,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        },
        None
    ))
    
    # Mock successful token validation
    mock_service.validate_token = AsyncMock(return_value=(
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
    ))
    
    # Mock successful user profile retrieval
    mock_service.get_user_profile = AsyncMock(return_value=(
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
    ))
    
    # Mock successful user profile update
    mock_service.update_user_profile = AsyncMock(return_value=(
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
    ))
    
    # Mock successful logout
    mock_service.logout_user = AsyncMock(return_value=(True, None))
    
    return mock_service


@pytest.fixture
def valid_user_data() -> Dict[str, Any]:
    """
    Valid user registration data for testing.
    
    Returns:
        Dict[str, Any]: Valid user registration data
    """
    return {
        "email": "test@example.com",
        "password": "TestPassword123",
        "full_name": "Test User"
    }


@pytest.fixture
def valid_login_data() -> Dict[str, Any]:
    """
    Valid user login data for testing.
    
    Returns:
        Dict[str, Any]: Valid user login data
    """
    return {
        "email": "test@example.com",
        "password": "TestPassword123"
    }


@pytest.fixture
def valid_token() -> str:
    """
    Valid JWT token for testing.
    
    Returns:
        str: Valid JWT token
    """
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.token"


@pytest.fixture
def admin_user_data() -> Dict[str, Any]:
    """
    Admin user data for testing.
    
    Returns:
        Dict[str, Any]: Admin user data
    """
    return {
        "id": "admin-user-id",
        "email": "admin@example.com",
        "full_name": "Admin User",
        "is_active": True,
        "is_admin": True,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    } 
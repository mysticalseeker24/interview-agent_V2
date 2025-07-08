import pytest
import httpx
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "TalentSync User Service"
    assert data["status"] == "running"


def test_signup_endpoint():
    """Test user signup."""
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    response = client.post("/auth/signup", json=user_data)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["full_name"] == user_data["full_name"]
    assert "id" in data


def test_login_endpoint():
    """Test user login."""
    # First create a user
    user_data = {
        "email": "login@example.com",
        "password": "testpassword123",
        "full_name": "Login User"
    }
    client.post("/auth/signup", json=user_data)
    
    # Now try to login
    login_data = {
        "username": "login@example.com",
        "password": "testpassword123"
    }
    response = client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_me_endpoint():
    """Test getting current user profile."""
    # Create and login user
    user_data = {
        "email": "profile@example.com",
        "password": "testpassword123",
        "full_name": "Profile User"
    }
    client.post("/auth/signup", json=user_data)
    
    login_data = {
        "username": "profile@example.com",
        "password": "testpassword123"
    }
    login_response = client.post("/auth/login", data=login_data)
    token = login_response.json()["access_token"]
    
    # Get profile
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/users/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["full_name"] == user_data["full_name"]


if __name__ == "__main__":
    test_root_endpoint()
    test_signup_endpoint()
    test_login_endpoint()
    test_me_endpoint()
    print("✅ All tests passed!")

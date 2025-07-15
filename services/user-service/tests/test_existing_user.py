import os
import pytest

# Existing user credentials
existing_email = os.getenv("EXISTING_USER_EMAIL", "sakshamm510@gmail.com")
existing_password = os.getenv("EXISTING_USER_PASSWORD", "1234567890")

@pytest.mark.asyncio
async def test_existing_user_login(client):
    """Test login with existing user credentials."""
    # Login with existing user
    resp = await client.post(
        "/auth/login",
        json={"email": existing_email, "password": existing_password}
    )
    assert resp.status_code == 200, resp.text
    login_data = resp.json()
    assert "access_token" in login_data
    assert login_data["user"]["email"] == existing_email

    # Get current user info
    token = login_data["access_token"]
    resp = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200, resp.text
    user_data = resp.json()
    assert user_data["email"] == existing_email

@pytest.mark.asyncio
async def test_existing_user_profile(client):
    """Test profile operations with existing user."""
    # Login first
    resp = await client.post(
        "/auth/login",
        json={"email": existing_email, "password": existing_password}
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]

    # Get profile
    resp = await client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200, resp.text
    profile = resp.json()
    assert profile["email"] == existing_email
    assert "full_name" in profile

    # Test profile update (optional - you might want to skip this to avoid changing real user data)
    # resp = await client.put(
    #     "/users/me",
    #     headers={"Authorization": f"Bearer {token}"},
    #     json={"full_name": "Updated Test Name"}
    # )
    # assert resp.status_code == 200, resp.text 
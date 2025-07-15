import os
import uuid
import pytest

# Generate unique test email to avoid conflicts
def get_test_email():
    """Generate a unique test email to avoid conflicts."""
    base_email = os.getenv("TEST_EMAIL", "integration.test001@gmail.com")
    if "@" in base_email:
        username, domain = base_email.split("@", 1)
        unique_id = uuid.uuid4().hex[:6]
        return f"{username}_{unique_id}@{domain}"
    return base_email

# Test credentials
test_email = get_test_email()
test_password = os.getenv("TEST_PASSWORD", "TestPass123!")
test_name = os.getenv("TEST_FULL_NAME", "Integration Test")

@pytest.mark.asyncio
async def test_signup_login_logout(client, cleanup_container):
    # Signup new user
    resp = await client.post(
        "/auth/signup",
        json={"email": test_email, "password": test_password, "full_name": test_name}
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    # Capture created user id for cleanup
    cleanup_container["user_id"] = data["user"]["id"]
    assert data["user"]["email"] == test_email

    # Login with the new user
    resp = await client.post(
        "/auth/login",
        json={"email": test_email, "password": test_password}
    )
    assert resp.status_code == 200, resp.text
    login = resp.json()
    token = login["access_token"]
    assert login["user"]["id"] == cleanup_container["user_id"]

    # Get current user info
    resp = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["email"] == test_email

    # Logout user
    resp = await client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "Logout successful" 
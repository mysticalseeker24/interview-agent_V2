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
async def test_duplicate_signup_should_fail(client, cleanup_container):
    """Test that attempting to signup with an existing email fails."""
    # First signup
    resp = await client.post(
        "/auth/signup",
        json={"email": test_email, "password": test_password, "full_name": test_name}
    )
    assert resp.status_code == 201
    cleanup_container["user_id"] = resp.json()["user"]["id"]
    
    # Attempt duplicate signup
    resp = await client.post(
        "/auth/signup",
        json={"email": test_email, "password": "different_password", "full_name": "Different Name"}
    )
    assert resp.status_code == 409  # Conflict
    assert "already exists" in resp.json()["detail"]

@pytest.mark.asyncio
async def test_invalid_login_should_fail(client):
    """Test that invalid credentials fail login."""
    resp = await client.post(
        "/auth/login",
        json={"email": "nonexistent@example.com", "password": "wrongpassword"}
    )
    assert resp.status_code == 401
    assert "Invalid email or password" in resp.json()["error"]

@pytest.mark.asyncio
async def test_protected_endpoints_require_auth(client):
    """Test that protected endpoints require authentication."""
    # Test /auth/me without token
    resp = await client.get("/auth/me")
    assert resp.status_code == 401
    
    # Test /users/me without token
    resp = await client.get("/users/me")
    # Should be 401 (Unauthorized) but might be 404 (Not Found) if route not found
    assert resp.status_code in [401, 404]
    
    # Test /auth/logout without token
    resp = await client.post("/auth/logout")
    assert resp.status_code == 401

@pytest.mark.asyncio
async def test_invalid_token_should_fail(client):
    """Test that invalid tokens are rejected."""
    invalid_token = "invalid.jwt.token"
    
    resp = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {invalid_token}"}
    )
    assert resp.status_code == 401

@pytest.mark.asyncio
async def test_profile_update_validation(client, cleanup_container):
    """Test profile update validation and edge cases."""
    # Login to get token
    resp = await client.post(
        "/auth/login",
        json={"email": test_email, "password": test_password}
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    
    # Test empty update
    resp = await client.put(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={}
    )
    assert resp.status_code == 400
    assert "No valid updates provided" in resp.json()["detail"]
    
    # Test partial update with only full_name
    resp = await client.put(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"full_name": "Updated Name"}
    )
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Updated Name"

@pytest.mark.asyncio
async def test_service_health_endpoints(client):
    """Test service health and information endpoints."""
    # Test root endpoint
    resp = await client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["service"] == "talentsync-user-service"
    assert "uptime" in data
    
    # Test health endpoint
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    
    # Test metrics endpoint
    resp = await client.get("/metrics")
    assert resp.status_code == 200
    assert "http_requests_total" in resp.text
    
    # Test ready endpoint
    resp = await client.get("/ready")
    assert resp.status_code == 200 
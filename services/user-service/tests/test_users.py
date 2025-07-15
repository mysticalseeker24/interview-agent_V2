import os
import pytest

@pytest.mark.asyncio
async def test_get_and_update_profile(client, cleanup_container):
    # Re-login to get fresh token
    resp = await client.post(
        "/auth/login",
        json={"email": os.getenv("TEST_EMAIL"), "password": os.getenv("TEST_PASSWORD")}
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
    assert profile["full_name"] == os.getenv("TEST_FULL_NAME")

    # Update full_name
    new_name = "Updated Test Name"
    resp = await client.put(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"full_name": new_name}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["full_name"] == new_name

    # Revert change
    resp = await client.put(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"full_name": os.getenv("TEST_FULL_NAME")}
    )
    assert resp.status_code == 200 
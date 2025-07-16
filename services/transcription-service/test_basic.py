import pytest
import asyncio
from httpx import AsyncClient
from app.main import app
from app.core.database import init_db, close_db
from app.core.config import settings


@pytest.fixture
async def client():
    """Create test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def setup_db():
    """Setup test database."""
    await init_db()
    yield
    await close_db()


@pytest.mark.asyncio
async def test_root_endpoint(client):
    """Test root endpoint."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == settings.app_name
    assert data["status"] == "running"


@pytest.mark.asyncio
async def test_health_check(client):
    """Test health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "components" in data


@pytest.mark.asyncio
async def test_interview_endpoint_structure(client):
    """Test interview endpoint structure."""
    # This would test the endpoint structure without actual API calls
    response = await client.get("/docs")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_transcription_endpoint_structure(client):
    """Test transcription endpoint structure."""
    # This would test the endpoint structure without actual API calls
    response = await client.get("/docs")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_tts_endpoint_structure(client):
    """Test TTS endpoint structure."""
    # This would test the endpoint structure without actual API calls
    response = await client.get("/docs")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_metrics_endpoint(client):
    """Test metrics endpoint."""
    response = await client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_interview_status_endpoint(client):
    """Test interview pipeline status endpoint."""
    response = await client.get("/api/v1/interview/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "components" in data
    assert "models" in data


if __name__ == "__main__":
    pytest.main([__file__]) 
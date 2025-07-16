"""
Basic test to verify the media service works correctly.
"""
import asyncio
import tempfile
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import init_db, close_db
from app.core.config import get_settings

settings = get_settings()


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
async def setup_db():
    """Setup test database."""
    await init_db()
    yield
    await close_db()


def test_root_endpoint(client):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "TalentSync Media Service"
    assert "version" in data


def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_devices_endpoint(client):
    """Test the devices endpoint."""
    response = client.get("/api/v1/media/devices")
    assert response.status_code == 200
    data = response.json()
    assert "audio_inputs" in data
    assert "audio_outputs" in data
    assert "video_inputs" in data
    assert "platform" in data


def test_storage_stats_endpoint(client):
    """Test the storage stats endpoint."""
    response = client.get("/api/v1/media/storage/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_sessions" in data
    assert "total_chunks" in data
    assert "storage_used_bytes" in data


def test_monitoring_health(client):
    """Test the monitoring health endpoint."""
    response = client.get("/api/v1/monitoring/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "timestamp" in data


def test_prometheus_metrics(client):
    """Test the Prometheus metrics endpoint."""
    response = client.get("/api/v1/monitoring/metrics/prometheus")
    assert response.status_code == 200
    content = response.text
    assert "media_service_uptime_seconds" in content


if __name__ == "__main__":
    # Run basic tests
    print("Running basic tests...")
    
    # Test client
    test_client = TestClient(app)
    
    # Test root endpoint
    response = test_client.get("/")
    print(f"Root endpoint: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test health check
    response = test_client.get("/api/v1/health")
    print(f"Health check: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test devices endpoint
    response = test_client.get("/api/v1/media/devices")
    print(f"Devices endpoint: {response.status_code}")
    print(f"Response: {response.json()}")
    
    print("Basic tests completed!") 
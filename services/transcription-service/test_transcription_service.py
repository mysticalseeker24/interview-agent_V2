import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_transcribe_chunk_endpoint():
    # Example test for chunk transcription endpoint
    # This should be updated with actual payload and expected response
    payload = {
        "session_id": "test-session-1",
        "chunk_index": 0,
        "audio_data": "base64-encoded-audio-data"
    }
    response = client.post("/transcriptions/chunk", json=payload)
    assert response.status_code == 200
    assert "transcription_text" in response.json()

def test_complete_session_endpoint():
    # Example test for session completion endpoint
    payload = {
        "session_id": "test-session-1"
    }
    response = client.post("/transcriptions/complete", json=payload)
    assert response.status_code == 200
    assert "full_transcript" in response.json()

def test_invalid_chunk_index():
    payload = {
        "session_id": "test-session-1",
        "chunk_index": -1,
        "audio_data": "base64-encoded-audio-data"
    }
    response = client.post("/transcriptions/chunk", json=payload)
    assert response.status_code == 400

def test_missing_audio_data():
    payload = {
        "session_id": "test-session-1",
        "chunk_index": 0,
    }
    response = client.post("/transcriptions/chunk", json=payload)
    assert response.status_code == 422

def test_complete_session_no_session_id():
    payload = {}
    response = client.post("/transcriptions/complete", json=payload)
    assert response.status_code == 422


# Additional tests for integration and edge cases can be added here

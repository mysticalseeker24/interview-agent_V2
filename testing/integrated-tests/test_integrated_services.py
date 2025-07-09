import pytest
import requests

# Base URLs for services
INTERVIEW_SERVICE_URL = "http://localhost:8002"
FEEDBACK_SERVICE_URL = "http://localhost:8003"
TRANSCRIPTION_SERVICE_URL = "http://localhost:8004"
RESUME_SERVICE_URL = "http://localhost:8005"
MEDIA_SERVICE_URL = "http://localhost:8006"

@pytest.mark.integration
def test_interview_service_health():
    response = requests.get(f"{INTERVIEW_SERVICE_URL}/api/v1/health")
    assert response.status_code == 200
    assert response.json().get("status") == "healthy"

@pytest.mark.integration
def test_feedback_service_health():
    response = requests.get(f"{FEEDBACK_SERVICE_URL}/api/v1/health")
    assert response.status_code == 200
    assert response.json().get("status") == "healthy"

@pytest.mark.integration
def test_transcription_service_health():
    response = requests.get(f"{TRANSCRIPTION_SERVICE_URL}/api/v1/health")
    assert response.status_code == 200
    assert response.json().get("status") == "healthy"

@pytest.mark.integration
def test_resume_service_health():
    response = requests.get(f"{RESUME_SERVICE_URL}/api/v1/health")
    assert response.status_code == 200
    assert response.json().get("status") == "healthy"

@pytest.mark.integration
def test_media_service_health():
    response = requests.get(f"{MEDIA_SERVICE_URL}/api/v1/health")
    assert response.status_code == 200
    assert response.json().get("status") == "healthy"

@pytest.mark.integration
def test_end_to_end_interview_flow():
    # Step 1: Start a new interview session
    session_response = requests.post(f"{INTERVIEW_SERVICE_URL}/api/v1/sessions", json={"candidate_name": "John Doe"})
    assert session_response.status_code == 201
    session_id = session_response.json().get("session_id")

    # Step 2: Submit a response to a question
    question_response = requests.post(f"{INTERVIEW_SERVICE_URL}/api/v1/sessions/{session_id}/responses", json={"answer": "I have experience with Python and React."})
    assert question_response.status_code == 200

    # Step 3: Generate feedback
    feedback_response = requests.post(f"{FEEDBACK_SERVICE_URL}/api/v1/feedback/generate", json={"session_id": session_id})
    assert feedback_response.status_code == 202
    feedback_task_id = feedback_response.json().get("task_id")

    # Step 4: Check feedback status
    feedback_status_response = requests.get(f"{FEEDBACK_SERVICE_URL}/api/v1/feedback/status/{feedback_task_id}")
    assert feedback_status_response.status_code == 200
    assert feedback_status_response.json().get("status") == "completed"

    # Step 5: Retrieve feedback report
    feedback_report_response = requests.get(f"{FEEDBACK_SERVICE_URL}/api/v1/feedback/report/{session_id}")
    assert feedback_report_response.status_code == 200
    assert "report" in feedback_report_response.json()

    # Step 6: Transcribe audio
    transcription_response = requests.post(f"{TRANSCRIPTION_SERVICE_URL}/api/v1/transcribe", json={"session_id": session_id, "audio_file": "sample_audio.mp3"})
    assert transcription_response.status_code == 200
    assert "transcript" in transcription_response.json()

    # Step 7: Analyze resume
    resume_response = requests.post(f"{RESUME_SERVICE_URL}/api/v1/analyze", json={"resume_file": "sample_resume.pdf"})
    assert resume_response.status_code == 200
    assert "skills" in resume_response.json()

    # Step 8: Process media
    media_response = requests.post(f"{MEDIA_SERVICE_URL}/api/v1/process", json={"session_id": session_id, "media_file": "sample_video.mp4"})
    assert media_response.status_code == 200
    assert "processed" in media_response.json()

# TalentSync Feedback Service

This service handles all feedback generation, scoring, analytics, and reporting for interview sessions. It is designed to be called by the interview service and other platform components.

## Features
- AI-powered feedback report generation
- Per-question and session-level scoring
- Percentile ranking and analytics
- RESTful API for feedback creation and retrieval

## Tech Stack
- FastAPI
- SQLAlchemy (SQLite)
- Alembic
- Celery (optional for async tasks)

## Usage
- Start the service and call its endpoints from the interview service for feedback operations.

# Feedback Service

## Overview
The Feedback Service is a microservice designed to generate detailed feedback reports for technical interviews using Blackbox AI's `blackboxai/openai/o4-mini` model.

## Environment Variables
- `BLACKBOX_API_KEY`: API key for Blackbox AI.
- `BLACKBOX_MODEL`: Model ID for Blackbox AI (default: `blackboxai/openai/o4-mini`).
- `DATABASE_URL`: SQLite database URL.
- `PORT`: Port number for the service (default: `8010`).

## Endpoints
### POST `/feedback/generate`
Generates a feedback report based on session data.
- **Request Body**: JSON object containing session data.
- **Response**: JSON object with the generated feedback report.

## Running the Service
1. Navigate to the service directory:
   ```bash
   cd talentsync/services/feedback-service
   ```
2. Start the service:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8010 --reload
   ```

## Testing
Use the following command to test the `/feedback/generate` endpoint:
```powershell
Invoke-RestMethod -Uri "http://localhost:8010/feedback/generate" -Method Post -ContentType "application/json" -InFile .\test_session_data.json
```

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

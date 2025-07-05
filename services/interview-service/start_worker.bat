@echo off
REM Celery worker startup script for Interview Service (Windows)

REM Set default environment variables if not provided
if not defined CELERY_BROKER_URL set CELERY_BROKER_URL=redis://localhost:6379/1
if not defined CELERY_RESULT_BACKEND set CELERY_RESULT_BACKEND=redis://localhost:6379/1
if not defined DATABASE_URL set DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/talentsync_interview

REM Check for required environment variables
if "%OPENAI_API_KEY%"=="" (
    echo Warning: OPENAI_API_KEY not set. AI feedback generation will fail.
)

echo Starting Celery worker for Interview Service...
echo Broker: %CELERY_BROKER_URL%
echo Result Backend: %CELERY_RESULT_BACKEND%

REM Start Celery worker with feedback queue
celery -A app.tasks worker ^
    --loglevel=INFO ^
    --concurrency=2 ^
    --queues=feedback,default ^
    --hostname=interview-worker@%%h ^
    --pool=threads ^
    --max-tasks-per-child=10 ^
    --time-limit=1800 ^
    --soft-time-limit=1500

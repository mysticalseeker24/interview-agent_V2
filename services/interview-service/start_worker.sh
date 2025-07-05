#!/bin/bash
# Celery worker startup script for Interview Service

# Set default environment variables if not provided
export CELERY_BROKER_URL=${CELERY_BROKER_URL:-"redis://localhost:6379/1"}
export CELERY_RESULT_BACKEND=${CELERY_RESULT_BACKEND:-"redis://localhost:6379/1"}
export DATABASE_URL=${DATABASE_URL:-"postgresql+asyncpg://user:password@localhost:5432/talentsync_interview"}
export OPENAI_API_KEY=${OPENAI_API_KEY:-""}

# Check for required environment variables
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Warning: OPENAI_API_KEY not set. AI feedback generation will fail."
fi

# Check if Redis is accessible
if ! nc -z localhost 6379; then
    echo "Error: Redis is not accessible on localhost:6379"
    echo "Please start Redis or update CELERY_BROKER_URL"
    exit 1
fi

echo "Starting Celery worker for Interview Service..."
echo "Broker: $CELERY_BROKER_URL"
echo "Result Backend: $CELERY_RESULT_BACKEND"

# Start Celery worker with feedback queue
celery -A app.tasks worker \
    --loglevel=INFO \
    --concurrency=2 \
    --queues=feedback,default \
    --hostname=interview-worker@%h \
    --pool=threads \
    --max-tasks-per-child=10 \
    --time-limit=1800 \
    --soft-time-limit=1500

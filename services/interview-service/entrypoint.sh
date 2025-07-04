#!/bin/bash

# This script starts the interview service

# Run database migrations if available
if [ -f "alembic.ini" ]; then
    echo "Running database migrations..."
    alembic upgrade head
fi

# Start the FastAPI application with multiple workers
echo "Starting the interview service with REST API-based sync..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8002} --workers ${WORKERS:-4}

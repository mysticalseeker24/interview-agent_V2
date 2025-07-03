#!/bin/bash

# TalentSync Transcription Service Startup Script

echo "Starting TalentSync Transcription Service..."
echo "=================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo "Please edit .env file with your API keys before running the service."
    exit 1
fi

# Create uploads directory
mkdir -p uploads

# Start the service
echo "Starting Transcription Service on port 8005..."
python -m app.main

@echo off
REM TalentSync Transcription Service Startup Script for Windows

echo Starting TalentSync Transcription Service...
echo ==================================

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Check if .env file exists
if not exist ".env" (
    echo Creating .env file from example...
    copy .env.example .env
    echo Please edit .env file with your API keys before running the service.
    pause
    exit /b 1
)

REM Create uploads directory
if not exist "uploads" mkdir uploads

REM Start the service
echo Starting Transcription Service on port 8005...
python -m app.main

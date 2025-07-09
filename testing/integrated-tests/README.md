# Integrated Testing for TalentSync Services

## Overview
This document outlines the integrated testing procedures for the TalentSync platform, involving the following services:
- **Feedback Service**
- **Interview Service**
- **Media Service**
- **Resume Service**
- **Transcription Service**

## Objectives
- Validate seamless interaction between services.
- Ensure data flow integrity across the platform.
- Test end-to-end workflows as they will function with frontend integration.

## Prerequisites
- All services must be running locally:
  - Feedback Service: `http://localhost:8010`
  - Interview Service: `http://localhost:8002`
  - Media Service: `http://localhost:8003`
  - Resume Service: `http://localhost:8001`
  - Transcription Service: `http://localhost:8004`
- Valid API keys for OpenAI, Pinecone, AssemblyAI.
- Ensure the `data` directory contains extracted resume data.

## Testing Workflow
### 1. Resume Parsing
- Use the Resume Service to parse a real resume and extract structured data.
- Validate the extracted data against the original resume.

### 2. Media Upload
- Upload audio files using the Media Service.
- Verify chunked uploads and file integrity.

### 3. Transcription
- Process uploaded audio files using the Transcription Service.
- Validate STT results and persona-driven interview responses.

### 4. Interview Management
- Generate dynamic questions and follow-ups using the Interview Service.
- Ensure session tracking and duplicate prevention.

### 5. Feedback Generation
- Generate feedback reports using the Feedback Service.
- Validate report accuracy and completeness.

## Terminal Commands
### Resume Parsing
```powershell
Invoke-RestMethod -Uri "http://localhost:8001/resume/parse" -Method Post -ContentType "application/json" -InFile .\data\resume.json
```

### Media Upload
```powershell
Invoke-RestMethod -Uri "http://localhost:8003/media/upload" -Method Post -InFile .\test-files\audio.mp3
```

### Transcription
```powershell
Invoke-RestMethod -Uri "http://localhost:8004/transcription/process" -Method Post -ContentType "application/json" -InFile .\test-files\audio.json
```

### Interview Management
```powershell
Invoke-RestMethod -Uri "http://localhost:8002/interview/start" -Method Post -ContentType "application/json" -InFile .\test-files\session.json
```

### Feedback Generation
```powershell
Invoke-RestMethod -Uri "http://localhost:8010/feedback/generate" -Method Post -ContentType "application/json" -InFile .\test-files\session.json
```

## Monitoring
- Check logs for API call details and errors.
- Verify response times and data accuracy.

## Notes
- Ensure all services are running and accessible before testing.
- Use real-world data for validation wherever possible.

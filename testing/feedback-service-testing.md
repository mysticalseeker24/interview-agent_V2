# Feedback Service Testing

## Overview
This document outlines the testing procedures for the Feedback Service.

## Prerequisites
- Ensure the Feedback Service is running on `http://localhost:8010`.
- Prepare a valid `test_session_data.json` file with session data.

## Testing Endpoints
### POST `/feedback/generate`
Generates a feedback report based on session data.

#### Command
```powershell
Invoke-RestMethod -Uri "http://localhost:8010/feedback/generate" -Method Post -ContentType "application/json" -InFile .\test_session_data.json
```

#### Expected Response
- **Success**: JSON object containing the generated feedback report.
- **Failure**: Error message indicating the issue (e.g., invalid session data).

## Edge Cases
- Missing or invalid API key.
- Empty or malformed session data.
- Exceeding token limits.

## Monitoring
- Check logs for API call details and errors.
- Verify response times and accuracy of generated reports.

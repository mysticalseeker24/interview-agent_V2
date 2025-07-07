# Transcription Service Test Configuration

This directory contains test assets and utilities for the chunked transcription service.

## Directory Structure

```
test-assets/
├── audio/
│   ├── output2.mp3          # Main test audio file from interview-pilot-ai
│   └── [other audio files]  # Additional test audio samples
├── personas/
│   ├── ethan-guidelines.txt # Ethan persona guidelines from interview-pilot-ai
│   ├── meta-guidelines.txt  # Meta persona guidelines
│   └── [other personas]     # Additional persona files
└── integration/
    ├── audioToText_reference.py  # Reference implementation from interview-pilot-ai
    └── [other integration code]  # Additional integration utilities
```

## Test Files

### Core Tests
- `test_chunked_transcription.py` - Comprehensive service-level tests
- `test_chunked_api.py` - API endpoint tests
- `test_comprehensive.py` - Existing comprehensive tests
- `test_real_audio.py` - Real audio transcription tests

### Test Audio
- `output2.mp3` - Primary test audio file (copied from interview-pilot-ai)
- Contains real speech for testing OpenAI Whisper transcription

### Integration References
- `audioToText_reference.py` - Working OpenAI Whisper implementation from interview-pilot-ai
- Demonstrates successful patterns for audio transcription

### Personas & Guidelines
- `ethan-guidelines.txt` - Strategic planner persona guidelines
- `meta-guidelines.txt` - Meta interviewer guidelines
- Used for testing persona-based follow-up generation

## Running Tests

### Environment Setup
Make sure you have the `.env` file with:
```
OPENAI_API_KEY=your_openai_api_key_here
```

### Individual Tests
```bash
# Test chunked transcription functionality
python test_chunked_transcription.py

# Test API endpoints (requires service running)
python test_chunked_api.py

# Test real audio transcription
python test_real_audio.py
```

### Service Tests
```bash
# Start the service first
uvicorn app.main:app --reload --port 8000

# Then run API tests
python test_chunked_api.py
```

## Integration Testing

### Follow-Up Service Integration
The chunked transcription service integrates with:
- Interview Service (http://localhost:8002)
- Follow-Up Generation API
- Feedback Generation API

### Test Integration Hooks
```bash
# Test follow-up integration manually
curl -X POST "http://localhost:8000/transcribe/integrations/test-followup" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "123", "transcript_text": "I have experience with React and Node.js"}'

# Test feedback integration manually  
curl -X POST "http://localhost:8000/transcribe/integrations/test-feedback" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "123", "regenerate": false}'

# Check integration health
curl http://localhost:8000/transcribe/integrations/health
```

## Expected Test Outcomes

### Chunked Transcription Pipeline
1. ✅ Audio chunks transcribed with OpenAI Whisper
2. ✅ Segments and confidence scores captured
3. ✅ Session-level aggregation and deduplication
4. ✅ Integration hooks trigger follow-up and feedback services

### Performance Metrics
- Transcription accuracy: >90% for clear speech
- Confidence scores: Available for each segment
- Deduplication: Overlapping segments removed
- Integration latency: <2s for follow-up triggers

## Troubleshooting

### Common Issues
1. **OpenAI API Key**: Ensure `.env` file contains valid API key
2. **Audio Format**: Test audio should be MP3/WAV format
3. **Service Dependencies**: Interview service should be running for integration tests
4. **Database**: SQLite database is created automatically

### Debug Mode
Set environment variable for verbose logging:
```bash
export LOG_LEVEL=DEBUG
python test_chunked_transcription.py
```

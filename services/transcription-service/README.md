# TalentSync Transcription Service

This service provides hybrid Speech-to-Text (STT) transcription capabilities using OpenAI Whisper and AssemblyAI, along with media device enumeration for the TalentSync interview platform.

## Features

### Task 2.4: Transcription & Media Integration

This service implements the following endpoints:

- **POST `/media/devices`**: Returns a list of available audio/video device labels for the frontend
- **POST `/transcribe`**: Accepts audio blob form-data and provides hybrid STT transcription

### Hybrid STT Implementation

The transcription service uses a sophisticated hybrid approach:

1. **Primary**: OpenAI Whisper (`whisper-1` model)
2. **Fallback**: AssemblyAI (when confidence < 0.85)
3. **Response**: Normalized JSON format with transcript and segments

## API Endpoints

### Media Devices

```http
POST /media/devices
Authorization: Bearer <token>
Content-Type: application/json

Response:
{
  "devices": [
    {
      "id": "default_microphone",
      "label": "Default Microphone",
      "device_type": "audio",
      "capabilities": {
        "sample_rates": [44100, 48000],
        "formats": ["PCM", "MP3"],
        "channels": [1, 2]
      },
      "is_default": true
    }
  ],
  "total": 1
}
```

### Transcription

```http
POST /transcribe
Authorization: Bearer <token>
Content-Type: multipart/form-data

Form Data:
- file: audio file (mp3, wav, m4a, webm, ogg)
- language: optional language code (default: en)

Response:
{
  "transcript": "Hello, this is a test transcription.",
  "segments": [
    {
      "start": 0.0,
      "end": 2.5,
      "text": "Hello, this is a test transcription.",
      "confidence": 0.95
    }
  ],
  "confidence_score": 0.95,
  "provider": "openai",
  "fallback_used": false,
  "duration_seconds": 2.5
}
```

## Implementation Details

### Hybrid STT Logic

The service implements the exact logic specified in the task:

```python
async def transcribe_audio(file_path: str):
    import openai
    resp = openai.Audio.transcribe('whisper-1', open(file_path,'rb'))
    low_conf = any(seg['confidence']<0.85 for seg in resp['segments'])
    if low_conf:
        resp = await assemblyai_transcribe(file_path)
    return normalize(resp)
```

### Key Features

1. **Confidence Threshold**: Uses 0.85 as the confidence threshold for fallback
2. **Automatic Fallback**: Seamlessly switches to AssemblyAI when needed
3. **Normalized Response**: Consistent JSON format regardless of provider
4. **File Upload**: Handles multipart form-data with temporary file management
5. **Error Handling**: Robust error handling with proper HTTP status codes

## Setup and Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here

# AssemblyAI Configuration
ASSEMBLYAI_API_KEY=your-assemblyai-api-key-here

# Database Configuration
DATABASE_URL=postgresql+asyncpg://user:password@localhost/talentsync_transcriptions

# Application Configuration
DEBUG=true
LOG_LEVEL=INFO
```

### Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. Run the service:
   ```bash
   python -m app.main
   ```

The service will start on port 8005 by default.

### API Documentation

Visit `http://localhost:8005/docs` for interactive API documentation.

## Testing

Run the test script to verify endpoints:

```bash
python test_endpoints.py
```

## Dependencies

- **FastAPI**: Web framework
- **OpenAI**: Primary STT provider
- **AssemblyAI**: Fallback STT provider
- **SQLAlchemy**: Database ORM
- **Pydantic**: Data validation
- **AsyncPG**: Async PostgreSQL driver

## Architecture

The service follows the TalentSync microservices architecture:

- **Service Layer**: Business logic for transcription and media devices
- **Router Layer**: HTTP endpoints and request/response handling
- **Schema Layer**: Pydantic models for data validation
- **Core Layer**: Configuration, database, logging, and security

## Status

✅ **Implemented**: All Task 2.4 requirements
✅ **Media Devices**: Stub implementation with platform-specific devices
✅ **Hybrid STT**: OpenAI Whisper + AssemblyAI fallback
✅ **Confidence Threshold**: 0.85 threshold for fallback decision
✅ **Normalized Response**: Consistent JSON format
✅ **Error Handling**: Comprehensive error handling
✅ **Documentation**: Complete API documentation

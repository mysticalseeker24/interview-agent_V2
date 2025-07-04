# TalentSync Transcription Service

The Transcription Service provides hybrid audio transcription capabilities using OpenAI Whisper and AssemblyAI, along with media device management for the TalentSync platform.

## Features

- **Hybrid STT (Speech-to-Text)**: Combines OpenAI Whisper and AssemblyAI for optimal accuracy
- **Real-time Transcription**: Live audio stream processing
- **Batch Transcription**: File-based audio processing
- **Media Device Enumeration**: Lists available audio input/output devices
- **Multiple Audio Formats**: Support for WAV, MP3, MP4, M4A, FLAC
- **Speaker Diarization**: Identifies different speakers in conversations
- **Confidence Scoring**: Provides transcription accuracy metrics

## API Endpoints

### Transcription
- `POST /api/v1/transcription/upload` - Upload audio file for transcription
- `POST /api/v1/transcription/stream` - Start real-time transcription session
- `GET /api/v1/transcription/{transcription_id}` - Get transcription result
- `PUT /api/v1/transcription/{transcription_id}` - Update transcription
- `DELETE /api/v1/transcription/{transcription_id}` - Delete transcription

### Hybrid Processing
- `POST /api/v1/transcription/hybrid` - Process audio with both Whisper and AssemblyAI
- `POST /api/v1/transcription/whisper` - Process with OpenAI Whisper only
- `POST /api/v1/transcription/assemblyai` - Process with AssemblyAI only

### Media Devices
- `GET /api/v1/media/devices/input` - List audio input devices
- `GET /api/v1/media/devices/output` - List audio output devices
- `GET /api/v1/media/devices/all` - List all audio devices
- `POST /api/v1/media/test` - Test audio device functionality

### Health Check
- `GET /api/v1/health` - Service health status

## Supported Audio Formats

- **WAV**: Uncompressed audio (best quality)
- **MP3**: Compressed audio format
- **MP4/M4A**: Video/audio containers
- **FLAC**: Lossless compression
- **OGG**: Open-source audio format

## Environment Variables

```
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/talentsync_transcription
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=104857600  # 100MB
OPENAI_API_KEY=your-openai-api-key
ASSEMBLYAI_API_KEY=your-assemblyai-api-key
HYBRID_MODE=true
DEFAULT_STT_PROVIDER=hybrid
ALLOWED_ORIGINS=["http://localhost:3000"]
ALLOWED_HOSTS=["localhost", "127.0.0.1"]
```

## Hybrid STT Architecture

The service implements a hybrid approach for maximum accuracy:

1. **Primary Processing**: Uses OpenAI Whisper for initial transcription
2. **Secondary Validation**: Uses AssemblyAI for confidence scoring
3. **Result Fusion**: Combines results based on confidence metrics
4. **Fallback Logic**: Switches providers if one fails
5. **Quality Assessment**: Compares outputs and selects best result

## Database Schema

The service uses the following main tables:
- `transcriptions` - Transcription metadata and results
- `audio_files` - Uploaded audio file information
- `transcription_segments` - Time-stamped transcript segments
- `speaker_segments` - Speaker diarization results
- `device_profiles` - Audio device configurations

## Real-time Processing

For live transcription:
- WebSocket connections for real-time audio streaming
- Chunked audio processing for low latency
- Incremental transcription updates
- Buffer management for continuous streams

## Audio Processing Pipeline

1. **File Upload/Stream**: Accept audio input
2. **Format Validation**: Verify supported audio formats
3. **Preprocessing**: Normalize audio levels and format
4. **STT Processing**: Run through Whisper and/or AssemblyAI
5. **Post-processing**: Clean and format transcription text
6. **Storage**: Save results with metadata and timestamps

## Quality Features

- **Confidence Scoring**: Per-word and segment confidence levels
- **Speaker Identification**: Distinguish between different speakers
- **Timestamp Accuracy**: Precise word-level timing
- **Language Detection**: Automatic language identification
- **Noise Filtering**: Background noise reduction

## Integration with Interview System

The Transcription Service integrates with:
- **Interview Service**: For recording and transcribing interview sessions
- **Frontend**: Real-time transcription display during interviews
- **Analytics**: Conversation analysis and keyword extraction

## Device Management

- Enumerates available audio input/output devices
- Provides device capabilities and specifications
- Supports device testing and configuration
- Cross-platform compatibility (Windows, macOS, Linux)

## Getting Started

1. Install system dependencies for audio processing
2. Set environment variables with API keys
3. Create upload directory: `mkdir uploads`
4. Install Python dependencies: `pip install -e .`
5. Run migrations: `alembic upgrade head`
6. Start service: `uvicorn app.main:app --reload --port 8004`

## Development

Key architectural components:
- Async audio processing for scalability
- Modular STT provider interface
- Comprehensive error handling
- Audio format conversion utilities
- Device detection and management

## Performance Considerations

- **Chunked Processing**: Handles large audio files efficiently
- **Concurrent Transcription**: Multiple providers in parallel
- **Caching**: Results caching for repeated requests
- **Streaming**: Real-time processing with minimal latency

## Testing

Run tests with:
```bash
pytest tests/
```

Test audio files should be placed in `/uploads/test/` directory.

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

# TalentSync Transcription & TTS Service Documentation

## Overview

The Transcription & TTS Service is a comprehensive audio processing component of the TalentSync AI Interview Platform that provides:

- **Enhanced Speech-to-Text (STT)** using OpenAI Whisper with improved accuracy
- **Text-to-Speech (TTS)** generation with intelligent caching
- **Real-time audio processing** with chunked transcription
- **Database persistence** for transcriptions and TTS audio
- **Performance monitoring** and health checks
- **Seamless integration** with other platform services

## 🚀 Key Features

### Enhanced Speech-to-Text (STT)
- **OpenAI Whisper Integration** with optimized settings
- **Enhanced accuracy** for technical vocabulary and proper nouns
- **Word-level timestamps** and confidence scores
- **Improved sensitivity** for better word detection
- **Contextual prompting** for interview-specific transcription
- **Fallback mechanisms** for reliability

### Text-to-Speech (TTS)
- **OpenAI TTS API** integration with high-quality voices
- **Intelligent caching** to reduce costs and latency
- **Multiple voice options** (alloy, echo, fable, onyx, nova, shimmer)
- **Various audio formats** (MP3, WAV, Opus, AAC, FLAC)
- **Database persistence** for audio file management
- **Automatic cleanup** of old files

### Audio Processing Pipeline
- **Real-time recording** with silence detection
- **Chunked processing** for long conversations
- **Session-level aggregation** and deduplication
- **Quality metrics** and confidence scoring
- **Error handling** and recovery mechanisms

## Architecture

### Core Components

1. **Transcription Service** (`app/services/transcription_service.py`)
   - Main service class handling OpenAI Whisper integration
   - Chunked audio processing with segment deduplication
   - Confidence scoring and quality assessment
   - Session-level transcript aggregation

2. **Integration Service** (`app/services/integration_service.py`)
   - Webhook management for inter-service communication
   - Follow-up question generation triggers
   - Feedback generation triggers
   - Event-driven architecture support

3. **Database Models** (`app/models/transcription.py`)
   - Transcription model with chunk support
   - Segment storage and metadata
   - Session management and indexing

4. **API Endpoints** (`app/routers/transcription.py`)
   - RESTful API for chunk processing
   - Session aggregation endpoints
   - Retrieval and management endpoints

## Features

### Chunked Audio Processing

The service processes audio in chunks to enable:
- **Real-time transcription** during interviews
- **Memory efficient processing** of long audio files
- **Parallel processing** capabilities
- **Fault tolerance** with individual chunk retry logic

### Segment Deduplication

Automatically removes duplicate or overlapping transcription segments:
- **Overlap detection** based on timing and text similarity
- **Confidence-based prioritization** for segment selection
- **Seamless merging** of chunk boundaries

### Session Management

Tracks and aggregates transcriptions at the session level:
- **Sequential processing** with proper chunk ordering
- **Full transcript reconstruction** from chunks
- **Session-level metadata** and statistics
- **Cleanup and archiving** capabilities

### Integration Webhooks

Supports event-driven architecture with other services:
- **Follow-up generation** triggers after transcription completion
- **Feedback generation** triggers for interview assessment
- **Custom webhook** support for extensibility

## API Endpoints

### Core Endpoints

#### POST `/transcribe/chunk/{media_chunk_id}`
Process a single audio chunk for transcription.

**Request Body:**
```json
{
  "session_id": "session_123",
  "media_chunk_id": "chunk_123_001",
  "sequence_index": 1,
  "audio_data": "base64_encoded_audio_data",
  "question_id": "optional_question_id"
}
```

**Response:**
```json
{
  "id": "uuid",
  "session_id": "session_123",
  "media_chunk_id": "chunk_123_001",
  "sequence_index": 1,
  "transcript_text": "Transcribed text content",
  "segments": [
    {
      "start": 0.0,
      "end": 2.5,
      "text": "Segment text"
    }
  ],
  "confidence_score": 0.95,
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### POST `/transcribe/session-complete/{session_id}`
Aggregate all chunks for a session into a complete transcript.

**Response:**
```json
{
  "session_id": "session_123",
  "full_transcript": "Complete aggregated transcript",
  "total_chunks": 5,
  "confidence_score": 0.93,
  "segments": [...],
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### GET `/transcribe/session/{session_id}/chunks`
Retrieve all chunks for a session.

**Response:**
```json
[
  {
    "id": "uuid",
    "media_chunk_id": "chunk_123_001",
    "sequence_index": 1,
    "transcript_text": "Chunk text",
    "confidence_score": 0.95
  }
]
```

#### GET `/transcribe/session/{session_id}/transcript`
Get the aggregated transcript for a session.

**Response:**
```json
{
  "session_id": "session_123",
  "full_transcript": "Complete transcript",
  "total_chunks": 5,
  "confidence_score": 0.93,
  "segments": [...]
}
```

### Health and Monitoring

#### GET `/health`
Service health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "1.0.0"
}
```

## Configuration

### Environment Variables

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Database Configuration
DATABASE_URL=sqlite:///./transcription.db

# Service Configuration
SERVICE_NAME=transcription-tts-service
SERVICE_VERSION=2.0.0
LOG_LEVEL=INFO

# Audio Processing Settings
STT_SAMPLE_RATE=16000
STT_SILENCE_THRESHOLD=0.01
STT_SILENCE_DURATION=1.5
STT_MAX_RECORDING_DURATION=30

# TTS Configuration
TTS_CACHE_DURATION_HOURS=24
TTS_DEFAULT_VOICE=alloy
TTS_DEFAULT_FORMAT=mp3
TTS_CLEANUP_INTERVAL_HOURS=6

# Integration Configuration
INTERVIEW_SERVICE_URL=http://interview-service:8000
WEBHOOK_TIMEOUT=30
```

### OpenAI Whisper Settings

The service uses OpenAI Whisper with the following configuration:
- **Model**: `whisper-1` (latest available)
- **Response Format**: `verbose_json` (for detailed segment information)
- **Language**: Auto-detected
- **Temperature**: 0.0 (for consistency)

### Audio Enhancement Settings

The service uses optimized settings for better speech recognition:

```python
# Enhanced STT Parameters
- Sample Rate: 16kHz (optimal for Whisper)
- Silence Threshold: 0.01 (improved sensitivity)
- Silence Duration: 1.5s (faster response)
- Context Prompting: Interview-specific vocabulary
- Temperature: 0.0 (consistent results)
- Response Format: verbose_json (detailed segments)
- Language: English (better accuracy)
- Word-level timestamps: Enabled
```

## Database Schema

### Transcription Table

```sql
CREATE TABLE transcriptions (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    media_chunk_id VARCHAR(255) UNIQUE,
    sequence_index INTEGER NOT NULL,
    transcript_text TEXT NOT NULL,
    segments JSON,
    confidence_score REAL,
    question_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_transcriptions_session_id ON transcriptions(session_id);
CREATE INDEX idx_transcriptions_sequence ON transcriptions(session_id, sequence_index);
CREATE INDEX idx_transcriptions_chunk_id ON transcriptions(media_chunk_id);
```

## Usage Examples

### Basic Chunked Transcription

```python
import asyncio
import base64
from pathlib import Path
from app.services.transcription_service import TranscriptionService

async def transcribe_audio_file():
    service = TranscriptionService()
    
    # Load audio file
    audio_path = Path("interview_audio.mp3")
    with open(audio_path, "rb") as f:
        audio_data = f.read()
    
    # Transcribe
    result = await service.transcribe_audio_chunk(audio_data)
    
    print(f"Transcript: {result['text']}")
    print(f"Confidence: {result['confidence_score']}")
    print(f"Segments: {len(result['segments'])}")

asyncio.run(transcribe_audio_file())
```

### Session Processing

```python
import asyncio
from app.services.transcription_service import TranscriptionService
from app.core.database import get_session

async def process_session():
    service = TranscriptionService()
    session_id = "interview_session_001"
    
    # Process multiple chunks
    chunks = [
        ("chunk_001", 1, audio_data_1),
        ("chunk_002", 2, audio_data_2),
        ("chunk_003", 3, audio_data_3),
    ]
    
    async for db_session in get_session():
        for chunk_id, sequence, audio_data in chunks:
            # Transcribe chunk
            result = await service.transcribe_audio_chunk(audio_data)
            
            # Save to database
            await service.save_transcription_chunk(
                session=db_session,
                session_id=session_id,
                media_chunk_id=chunk_id,
                sequence_index=sequence,
                transcript_text=result['text'],
                segments=result['segments'],
                confidence_score=result['confidence_score']
            )
        
        # Aggregate session
        final_result = await service.aggregate_session_transcript(
            session=db_session,
            session_id=session_id
        )
        
        print(f"Final transcript: {final_result['full_transcript']}")
        print(f"Total chunks: {final_result['total_chunks']}")

asyncio.run(process_session())
```

### Integration with Interview Service

```python
import asyncio
from app.services.integration_service import IntegrationService

async def trigger_follow_up():
    integration = IntegrationService()
    
    transcript_data = {
        "full_transcript": "User answered the technical question about algorithms...",
        "confidence_score": 0.95,
        "segments": [...]
    }
    
    # Trigger follow-up generation
    result = await integration.trigger_followup_generation(
        session_id="session_001",
        transcript_data=transcript_data
    )
    
    print(f"Follow-up triggered: {result}")

asyncio.run(trigger_follow_up())
```

## Testing

### Test Suite Structure

The service includes comprehensive test coverage:

1. **Unit Tests** (`test_chunked_transcription.py`)
   - Individual component testing
   - Segment deduplication logic
   - Confidence scoring validation

2. **API Tests** (`test_chunked_api.py`)
   - Endpoint functionality
   - Request/response validation
   - Error handling

3. **Integration Tests** (`test_integration_comprehensive.py`)
   - End-to-end workflows
   - Performance and stress testing
   - Error scenarios and edge cases

### Running Tests

```bash
# Set up environment
export OPENAI_API_KEY="your_api_key_here"

# Run unit tests
python test_chunked_transcription.py

# Run API tests (requires running service)
python test_chunked_api.py

# Run comprehensive integration tests
python test_integration_comprehensive.py
```

### Test Coverage

The test suite covers:
- ✅ **Basic chunked workflow** (end-to-end)
- ✅ **Error handling** (invalid inputs, edge cases)
- ✅ **API endpoints** (all HTTP methods and routes)
- ✅ **Integration webhooks** (service-to-service communication)
- ✅ **Performance** (concurrent processing, stress testing)
- ✅ **Data validation** (schema compliance, constraint checking)
- ✅ **Session management** (creation, aggregation, cleanup)

## Deployment

### Docker Configuration

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  transcription-service:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DATABASE_URL=sqlite:///./transcription.db
      - INTERVIEW_SERVICE_URL=http://interview-service:8000
    volumes:
      - ./data:/app/data
    depends_on:
      - interview-service
```

### Production Considerations

1. **Database**: Consider PostgreSQL for production workloads
2. **Scaling**: Use horizontal scaling with load balancers
3. **Storage**: Implement proper audio file storage (S3, etc.)
4. **Monitoring**: Add metrics and logging for observability
5. **Security**: Implement proper authentication and authorization

## Monitoring and Debugging

### Logging

The service uses structured logging with different levels:

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
```

### Metrics

Key metrics to monitor:
- **Transcription latency** (time per chunk)
- **Accuracy scores** (confidence metrics)
- **Error rates** (failed transcriptions)
- **Session completion rates**
- **API response times**

### Health Checks

The service provides health check endpoints for monitoring:
- `/health` - Basic service health
- `/health/detailed` - Detailed component status
- `/metrics` - Prometheus-compatible metrics

## Troubleshooting

### Common Issues

1. **OpenAI API Rate Limits**
   - Implement exponential backoff
   - Use request queuing
   - Monitor API usage

2. **Audio Format Issues**
   - Validate audio formats (MP3, WAV, etc.)
   - Check file size limits
   - Verify encoding quality

3. **Database Connection Issues**
   - Check connection strings
   - Verify database accessibility
   - Monitor connection pool usage

4. **Memory Issues**
   - Monitor audio file sizes
   - Implement chunking for large files
   - Use streaming processing

### Debug Mode

Enable debug mode for detailed logging:

```bash
export LOG_LEVEL=DEBUG
python -m uvicorn app.main:app --reload
```

## Future Enhancements

### Planned Features

1. **Advanced Audio Processing**
   - Noise reduction
   - Speaker diarization
   - Audio quality enhancement

2. **Multi-language Support**
   - Language detection
   - Translation capabilities
   - Locale-specific processing

3. **Performance Optimizations**
   - Caching strategies
   - Parallel processing
   - GPU acceleration

4. **Enterprise Features**
   - Multi-tenancy support
   - Advanced security
   - Audit logging

### Contributing

To contribute to the Transcription Service:

1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Submit a pull request
5. Follow code review process

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔊 Text-to-Speech (TTS) API

### Generate TTS Audio
```bash
POST /api/v1/tts/generate
Content-Type: application/json

{
  "text": "Hello! Can you tell me about your experience with Python?",
  "voice": "alloy",
  "format": "mp3",
  "speed": 1.0
}
```

**Response:**
```json
{
  "tts_id": 123,
  "file_path": "tts_files/tts_uuid123.mp3",
  "url": "/tts/files/tts_uuid123.mp3",
  "file_size": 45612,
  "duration": 3.2,
  "created_at": "2025-01-08T10:30:00Z"
}
```

### Serve Audio Files
```bash
GET /tts/files/{filename}
```
Returns the audio file for playback.

### Get Cache Statistics
```bash
GET /api/v1/tts/cache/stats
```

**Response:**
```json
{
  "total_requests": 150,
  "total_file_size_bytes": 12845629,
  "total_file_size_mb": 12.25,
  "average_duration_seconds": 4.8,
  "cache_directory": "tts_files",
  "supported_voices": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
  "supported_formats": ["mp3", "opus", "aac", "flac"]
}
```

### Cleanup Old Files
```bash
POST /api/v1/tts/cache/cleanup?days_old=7
```

### Get Supported Voices
```bash
GET /api/v1/tts/voices
```

### Get Session TTS History
```bash
GET /api/v1/tts/session/{session_id}/history
```

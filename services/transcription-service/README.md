# TalentSync Transcription Service

A high-performance transcription service built for TalentSync platform, featuring Groq Whisper Large v3 for speech-to-text and Groq Play.ai TTS for text-to-speech synthesis.

## 🚀 Features

- **Real-time Chunked Processing**: Process audio in 5-minute chunks with 2-second overlap for seamless interviews
- **Groq Whisper Large v3**: State-of-the-art speech recognition with high accuracy
- **Groq Play.ai TTS**: High-quality text-to-speech synthesis with voice caching
- **Persona System**: 9 different interviewer personas with unique voices and personalities
- **Unified Groq API**: Single API key for both STT and TTS operations
- **Atomic File Operations**: Safe file handling with atomic writes
- **Comprehensive Caching**: Intelligent TTS caching to reduce API costs
- **Health Monitoring**: Built-in health checks for all components
- **Production Ready**: Docker support, logging, error handling, and monitoring

## 🏗️ Architecture

### Core Components

- **Groq STT Client**: Handles speech-to-text using Whisper Large v3
- **Groq TTS Client**: Manages text-to-speech synthesis with Play.ai model
- **Persona Service**: Manages interviewer personas with voice assignments
- **Interview Pipeline**: Complete STT → JSON → TTS flow for interviews
- **Chunked Processing**: Real-time audio chunk processing with overlap handling
- **Database Models**: SQLAlchemy models for transcriptions and TTS cache
- **RESTful API**: FastAPI endpoints for transcription and TTS operations

### Database Schema

```sql
-- Transcriptions table
CREATE TABLE transcriptions (
    id INTEGER PRIMARY KEY,
    chunk_id VARCHAR(255) NOT NULL,
    transcript_text TEXT NOT NULL,
    confidence FLOAT,
    session_id VARCHAR(255),
    sequence_index INTEGER,
    segments TEXT,
    language VARCHAR(10),
    duration_seconds FLOAT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- TTS Cache table
CREATE TABLE tts_cache (
    id INTEGER PRIMARY KEY,
    text TEXT NOT NULL,
    voice VARCHAR(50) NOT NULL,
    format VARCHAR(10) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size_bytes INTEGER,
    duration_seconds FLOAT,
    cache_hit_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Groq API key (for both STT and TTS)

### Environment Setup

1. Copy environment file:
```bash
cp env.example .env
```

2. Configure your API key:
```bash
# Required: Groq API key for both speech-to-text and text-to-speech
GROQ_API_KEY=your-groq-api-key-here
```

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the service:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8005
```

### Docker Deployment

1. Build the image:
```bash
docker build -t talentsync-transcription-service .
```

2. Run the container:
```bash
docker run -p 8005:8005 \
  -e GROQ_API_KEY=your-key \
  talentsync-transcription-service
```

## 📡 API Endpoints

### Interview Pipeline Endpoints

#### `POST /api/v1/interview/round`
Process a complete interview round (STT → JSON → TTS).

**Form Data:**
- `agent_question`: Question the agent is asking
- `session_id`: Interview session ID
- `round_number`: Current round number (default: 1)
- `user_audio`: User's audio response file
- `domain`: Optional domain for persona selection
- `persona_name`: Optional specific persona name

**Response:**
```json
{
  "session_id": "session-123",
  "round_number": 1,
  "agent_question": "Tell me about your experience.",
  "agent_question_audio_url": "/tts/files/abc123.wav",
  "user_response": {
    "raw_text": "I have 5 years of experience...",
    "structured_json": {...},
    "confidence": 0.95,
    "segments": [...],
    "language": "en"
  },
  "agent_reply": "Thank you for that response...",
  "agent_reply_audio_url": "/tts/files/def456.wav",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### `GET /api/v1/interview/status`
Get pipeline component health status.

#### `POST /api/v1/interview/tts-only`
Generate TTS audio only.

#### `POST /api/v1/interview/stt-only`
Transcribe audio only.

### Transcription Endpoints

#### `POST /api/v1/transcribe/`
Transcribe an audio chunk file.

**Form Data:**
- `chunk_id`: Unique chunk identifier
- `session_id`: Session identifier
- `sequence_index`: Chunk order (0, 1, 2, ...)
- `overlap_seconds`: Overlap duration (default: 2.0)
- `file`: Audio file (webm, mp3, wav, m4a, ogg)

**Response:**
```json
{
  "transcript": "Hello, this is a test transcription.",
  "segments": [...],
  "confidence": 0.95,
  "language": "en",
  "duration_seconds": 5.2
}
```

#### `POST /api/v1/transcribe/chunk`
Process audio chunk with base64 data.

**Request Body:**
```json
{
  "session_id": "session-123",
  "chunk_id": "chunk-456",
  "sequence_index": 0,
  "audio_data": "base64-encoded-audio-data",
  "overlap_seconds": 2.0
}
```

#### `POST /api/v1/transcribe/session-complete`
Complete a session and get full transcript.

**Request Body:**
```json
{
  "session_id": "session-123",
  "total_chunks": 5
}
```

### Persona Endpoints

#### `GET /api/v1/personas/`
Get summary of all available personas.

#### `GET /api/v1/personas/domains`
Get list of available domains.

#### `GET /api/v1/personas/domain/{domain}`
Get all personas for a specific domain.

#### `GET /api/v1/personas/{domain}/{persona_name}`
Get specific persona details.

#### `GET /api/v1/personas/voices`
Get available voices and their assignments.

#### `POST /api/v1/personas/select`
Select appropriate persona based on criteria.

### TTS Endpoints

#### `POST /api/v1/tts/generate`
Generate text-to-speech audio.

**Request Body:**
```json
{
  "text": "Hello, this is a test.",
  "voice": "Briggs-PlayAI",
  "format": "wav"
}
```

**Response:**
```json
{
  "file_url": "/tts/files/abc123.wav",
  "file_path": "/app/tts_cache/abc123.wav",
  "file_size_bytes": 10240,
  "duration_seconds": 3.5,
  "is_cached": false
}
```

#### `GET /api/v1/tts/cache-info`
Get TTS cache statistics.

#### `POST /api/v1/tts/cache/cleanup`
Clean up old cached files.

### Health & Monitoring

#### `GET /health`
Service health check.

#### `GET /metrics`
Service metrics.

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GROQ_API_KEY` | Groq API key (required) | - |
| `GROQ_BASE_URL` | Groq API base URL | https://api.groq.com/openai/v1 |
| `GROQ_STT_MODEL` | STT model name | whisper-large-v3 |
| `GROQ_TTS_MODEL` | TTS model name | playai-tts |
| `GROQ_DEFAULT_VOICE` | Default TTS voice | Briggs-PlayAI |
| `PORT` | Service port | 8005 |
| `DATABASE_URL` | Database connection string | SQLite |
| `MAX_FILE_SIZE` | Maximum file size in bytes | 100MB |
| `DEFAULT_OVERLAP_SECONDS` | Chunk overlap duration | 2.0 |
| `MAX_CHUNK_DURATION` | Maximum chunk duration | 300s |

### Available Voices

The service supports all Groq Play.ai voices:
- Arista-PlayAI, Atlas-PlayAI, Basil-PlayAI, Briggs-PlayAI
- Calum-PlayAI, Celeste-PlayAI, Cheyenne-PlayAI, Chip-PlayAI
- Cillian-PlayAI, Deedee-PlayAI, Fritz-PlayAI, Gail-PlayAI
- Indigo-PlayAI, Mamaw-PlayAI, Mason-PlayAI, Mikail-PlayAI
- Mitch-PlayAI, Quinn-PlayAI, Thunder-PlayAI

### Persona System

The service includes a comprehensive persona system with 9 different interviewer personas:

**Individual Personas:**
- Emma (Enthusiastic Networker) - Uses Celeste-PlayAI voice
- Liam (Methodical Analyst) - Uses Atlas-PlayAI voice

**Job-Specific Personas:**
- Maya (AI/ML Expert) - Uses Arista-PlayAI voice
- Noah (Data-Driven Decider) - Uses Basil-PlayAI voice
- Jordan (DevOps Specialist) - Uses Calum-PlayAI voice
- Liam DSA (Methodical Analyst DSA) - Uses Cillian-PlayAI voice
- Maya ML (AI/ML Expert ML) - Uses Deedee-PlayAI voice
- Olivia (Empathetic Listener Resume) - Uses Fritz-PlayAI voice
- Taylor (Full-Stack Developer) - Uses Gail-PlayAI voice

Each persona has unique personality traits, expertise areas, and interview approaches. The system automatically assigns appropriate voices based on persona characteristics.

### Chunked Processing

The service is designed for real-time interview processing:

- **Chunk Size**: 5 minutes maximum
- **Overlap**: 2 seconds between chunks
- **Processing**: Background processing with status tracking
- **Aggregation**: Automatic transcript assembly with deduplication

## 🧪 Testing

### Automated Testing

Run the comprehensive test suite:

```bash
# Install testing dependencies
python setup_testing.py

# Run comprehensive service tests
python test_comprehensive_service.py

# Run pytest tests
pytest test_*.py -v

# Run with coverage
pytest test_*.py --cov=app --cov-report=html
```

### Live Mock Interview Testing

Test the service through an interactive mock interview:

```bash
# Start the service
uvicorn app.main:app --reload --port 8005

# In another terminal, run the mock interview
python test_live_mock_interview.py
```

The mock interview system allows you to:
- Select from 9 different interviewer personas
- Experience TTS-generated questions with persona-specific voices
- Record audio responses (or use simulated responses)
- Test the complete STT → JSON → TTS pipeline
- Save interview summaries for analysis

### Test Files Overview

- **`test_comprehensive_service.py`**: Comprehensive automated testing of all service components
- **`test_live_mock_interview.py`**: Interactive terminal-based mock interview system
- **`setup_testing.py`**: Setup script for testing environment
- **`test_requirements.txt`**: Testing dependencies

### Manual Testing

1. Test interview round:
```bash
curl -X POST "http://localhost:8005/api/v1/interview/round" \
  -F "agent_question=Tell me about your experience" \
  -F "session_id=session-1" \
  -F "round_number=1" \
  -F "user_audio=@test-audio.mp3"
```

2. Test transcription:
```bash
curl -X POST "http://localhost:8005/api/v1/transcribe/" \
  -F "chunk_id=test-1" \
  -F "session_id=session-1" \
  -F "sequence_index=0" \
  -F "file=@test-audio.mp3"
```

3. Test TTS:
```bash
curl -X POST "http://localhost:8005/api/v1/tts/generate" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "voice": "Briggs-PlayAI"}'
```

4. Test Persona System:
```bash
# Get all personas
curl "http://localhost:8005/api/v1/personas/"

# Get personas by domain
curl "http://localhost:8005/api/v1/personas/domain/software-engineering"

# Get voice assignments
curl "http://localhost:8005/api/v1/personas/voices"
```

5. Check health:
```bash
curl "http://localhost:8005/health"
```

### Integration Testing

The service integrates with:
- **Media Service**: Receives chunk uploads
- **Interview Service**: Provides real-time transcripts
- **Feedback Service**: Sends completed transcripts

## 📊 Monitoring

### Health Checks

- Database connectivity
- Groq API availability
- File system access
- Model availability

### Metrics

- Transcription requests per minute
- TTS cache hit/miss rates
- Average processing times
- Error rates by endpoint

### Logging

Structured logging with:
- Request/response logging
- Error tracking
- Performance metrics
- API call monitoring

## 🔒 Security

- Input validation and sanitization
- File type restrictions
- Size limits enforcement
- CORS configuration
- Error message sanitization

## 🚀 Production Deployment

### Docker Compose

```yaml
version: '3.8'
services:
  transcription-service:
    build: .
    ports:
      - "8005:8005"
    environment:
      - GROQ_API_KEY=${GROQ_API_KEY}
    volumes:
      - ./uploads:/app/uploads
      - ./tts_cache:/app/tts_cache
    restart: unless-stopped
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: transcription-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: transcription-service
  template:
    metadata:
      labels:
        app: transcription-service
    spec:
      containers:
      - name: transcription-service
        image: talentsync-transcription-service:latest
        ports:
        - containerPort: 8005
        env:
        - name: GROQ_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: groq-api-key
```

## 🤝 Contributing

1. Follow the TalentSync coding conventions
2. Add tests for new features
3. Update documentation
4. Ensure all health checks pass

## 📝 License

MIT License - see LICENSE file for details.

## 🆘 Support

For issues and questions:
- Check the health endpoint: `/health`
- Review logs for error details
- Test API endpoints with the provided examples
- Consult the TalentSync documentation 
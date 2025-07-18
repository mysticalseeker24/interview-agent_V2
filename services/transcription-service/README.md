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
- **Automatic Cache Cleanup**: TTS cache automatically cleaned after each interview session
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
- **Cache Management**: Automatic TTS cache cleanup after interview sessions

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

1. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

2. **Initialize Database** (Required for TTS cache):
```bash
python init_database.py
```

3. **Start the Service**:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8005
```

4. **Verify Service Health**:
```bash
curl http://localhost:8005/health
```

5. **Run Tests** (Optional):
```bash
# Comprehensive automated tests
python test_comprehensive_service.py

# Interactive mock interview
python test_live_mock_interview.py
```

### Docker Deployment

1. **Build the Image**:
```bash
docker build -t talentsync-transcription-service .
```

2. **Run the Container**:
```bash
docker run -p 8005:8005 \
  -e GROQ_API_KEY=your-key \
  talentsync-transcription-service
```

**Note**: The Docker container automatically initializes the database on startup, so no manual database setup is required.

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

**Note**: After each interview round, the TTS cache is automatically cleaned to free up disk space.

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

**Note**: This endpoint is automatically called after each interview session to maintain optimal disk usage.

### Health & Monitoring

#### `GET /health`
Service health check.

#### `GET /api/v1/health`
Detailed health status with component checks.

## 🧪 Testing

### Automated Testing
```bash
# Run comprehensive test suite
python test_comprehensive_service.py

# Test specific components
python setup_testing.py
```

### Interactive Testing
```bash
# Run live mock interview simulation
python test_live_mock_interview.py
```

### Manual API Testing
```bash
# Test TTS generation
curl -X POST "http://localhost:8005/api/v1/tts/generate" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is a test.", "voice": "Briggs-PlayAI", "format": "wav"}'

# Test transcription
curl -X POST "http://localhost:8005/api/v1/transcribe/" \
  -F "file=@test_audio.wav" \
  -F "chunk_id=test-chunk" \
  -F "session_id=test-session"
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GROQ_API_KEY` | Groq API key for STT and TTS | Yes | - |
| `DATABASE_URL` | SQLite database URL | No | `sqlite:///./transcription_service.db` |
| `UPLOAD_DIR` | Audio upload directory | No | `./uploads` |
| `TTS_CACHE_DIR` | TTS cache directory | No | `./tts_cache` |
| `LOG_LEVEL` | Logging level | No | `INFO` |

### Persona System

The service includes 9 different interviewer personas:

#### Individual Personas
- **Emma** (Arista-PlayAI): Enthusiastic networker
- **Liam** (Briggs-PlayAI): Methodical analyst

#### Job-Specific Personas
- **AI Engineering**: Maya (Arista-PlayAI)
- **Data Analyst**: Noah (Briggs-PlayAI)
- **DevOps**: Jordan (Arista-PlayAI)
- **DSA**: Liam (Briggs-PlayAI)
- **Machine Learning**: Maya (Arista-PlayAI)
- **Resume-based**: Olivia (Arista-PlayAI)
- **Software Engineering**: Taylor (Briggs-PlayAI)

## 🗄️ Database Management

### Automatic Initialization
The database is automatically initialized when:
- Running `python init_database.py` manually
- Starting the Docker container (automatic)
- First service startup (if database doesn't exist)

### Manual Database Operations
```bash
# Initialize database manually
python init_database.py

# Reset database (WARNING: Deletes all data)
rm transcription_service.db
python init_database.py
```

## 🧹 Cache Management

### Automatic TTS Cache Cleanup
- **When**: After each interview round completion
- **What**: Removes old TTS audio files to free disk space
- **Why**: Prevents disk space issues during long interview sessions
- **How**: Automatic cleanup triggered by interview pipeline

### Manual Cache Management
```bash
# Get cache statistics
curl http://localhost:8005/api/v1/tts/cache-info

# Manual cache cleanup
curl -X POST http://localhost:8005/api/v1/tts/cache/cleanup
```

## 📊 Monitoring & Logs

### Health Checks
- Service health: `GET /health`
- Component status: `GET /api/v1/health`
- Database connectivity
- Groq API connectivity
- File system access

### Logging
- Request/response logging
- Error tracking
- Performance metrics
- Cache hit/miss statistics

## 🚀 Production Deployment

### Docker Compose
```yaml
version: '3.9'
services:
  transcription-service:
    build: ./services/transcription-service
    ports:
      - "8005:8005"
    environment:
      - GROQ_API_KEY=${GROQ_API_KEY}
    volumes:
      - transcription_data:/app/uploads
      - tts_cache:/app/tts_cache
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8005/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  transcription_data:
  tts_cache:
```

### Environment Variables for Production
```env
GROQ_API_KEY=your-production-groq-key
LOG_LEVEL=WARNING
DATABASE_URL=sqlite:///./transcription_service.db
UPLOAD_DIR=/app/uploads
TTS_CACHE_DIR=/app/tts_cache
```

## 🔒 Security Considerations

- API key management via environment variables
- Input validation for all endpoints
- File type validation for audio uploads
- Automatic cleanup of temporary files
- Database connection security
- Rate limiting for API endpoints

## 📈 Performance Optimization

- TTS caching to reduce API calls
- Chunked audio processing
- Database connection pooling
- Automatic cache cleanup
- Optimized file handling

## 🐛 Troubleshooting

### Common Issues

1. **Database not initialized**
   ```bash
   python init_database.py
   ```

2. **TTS cache directory missing**
   ```bash
   mkdir -p tts_cache
   ```

3. **Groq API errors**
   - Verify API key is correct
   - Check API quota limits
   - Ensure network connectivity

4. **Audio file issues**
   - Supported formats: webm, mp3, wav, m4a, ogg
   - Maximum file size: 100MB
   - Check file permissions

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
uvicorn app.main:app --reload --host 0.0.0.0 --port 8005
```

## 📝 Changelog

### v2.0.0
- Added automatic TTS cache cleanup after interviews
- Enhanced database initialization in Docker
- Improved error handling and logging
- Added comprehensive testing suite
- Updated documentation with proper initialization steps

### v1.0.0
- Initial release with Groq Whisper Large v3 and PlayAI TTS
- Persona system with 9 different voices
- Interview pipeline with STT → JSON → TTS flow
- Real-time chunked audio processing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details. 
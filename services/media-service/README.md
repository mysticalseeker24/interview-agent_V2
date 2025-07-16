# TalentSync Media Service

A high-performance FastAPI microservice for chunked audio/video uploads, device enumeration, and media file management for AI-powered interviews.

## Features
- Chunked audio/video uploads with session management
- Device enumeration for frontend dropdowns
- File validation and storage (uploads/)
- Event emission to other services (transcription, interview)
- Async background processing (Celery)
- Health checks and Prometheus metrics
- SQLite metadata DB

## Quickstart

### Docker
```bash
docker build -t media-service .
docker run -p 8003:8003 -v $(pwd)/uploads:/app/uploads media-service
```

### Local Development
```bash
pip install -r requirements.txt
cp env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
# In another terminal (for background tasks):
celery -A app.workers.celery_app worker --loglevel=info
```

## Configuration
Set these in `.env` or as environment variables:
```
APP_NAME=TalentSync Media Service
PORT=8003
DATABASE_URL=sqlite+aiosqlite:///./media_service.db
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=104857600
ALLOWED_EXTENSIONS_STR=webm,mp3,wav,m4a,ogg
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
TRANSCRIPTION_SERVICE_URL=http://transcription-service:8002
INTERVIEW_SERVICE_URL=http://interview-service:8001
```

## API Endpoints
| Method | Path                                 | Description                       |
|--------|--------------------------------------|-----------------------------------|
| POST   | /media/chunk-upload                  | Upload a media chunk              |
| POST   | /media/session                       | Create a new upload session       |
| GET    | /media/session/{session_id}/summary  | Get session summary               |
| GET    | /media/session/{session_id}/gaps     | Find missing chunk indices        |
| DELETE | /media/session/{session_id}          | Delete session and files          |
| GET    | /media/devices                       | Enumerate audio/video devices     |
| GET    | /media/storage/stats                 | Storage usage statistics          |
| POST   | /media/validate-file                 | Validate file before upload       |
| GET    | /health                              | Health check                      |
| GET    | /metrics                             | JSON metrics                      |
| GET    | /prometheus                          | Prometheus metrics                |

## Health & Metrics
- `/health` – Service health (JSON)
- `/metrics` – System metrics (JSON)
- `/prometheus` – Prometheus scrape endpoint

## File Structure
```
app/
  core/         # Config, DB
  models/       # SQLAlchemy models
  schemas/      # Pydantic schemas
  routers/      # FastAPI routes
  services/     # Business logic
  workers/      # Celery tasks
uploads/        # Uploaded media files
```

## Contributing
1. Fork the repo
2. Create a feature branch
3. Add tests for your changes
4. Ensure all tests pass
5. Submit a pull request

## License
MIT License © 2025 TalentSync 
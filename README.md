# TalentSync - AI-Powered Interview Platform

TalentSync is an intelligent, AI-powered interview platform that delivers personalized technical interviews through domain-specific modules, adaptive questioning, and real-time audio capabilities with comprehensive performance analytics.

## 🚀 Features

### Core Interview Capabilities
- **Domain-Specific Modules**: Software Engineering, Machine Learning, Data Structures & Algorithms, Resume-Driven Questions
- **Intelligent Question Generation**: RAG-powered follow-up questions based on candidate responses
- **Semantic Search**: Vector-based question retrieval using Pinecone and OpenAI embeddings
- **Resume-Driven Interviews**: Dynamic question generation based on candidate background
- **Real-time Transcription**: Enhanced STT using OpenAI Whisper and AssemblyAI with chunked processing
- **Text-to-Speech**: OpenAI TTS integration with persona-driven voice synthesis
- **Interactive Interviews**: Real-time conversational AI with audio input/output capabilities

### AI & Machine Learning
- **Vector Database Integration**: Pinecone for semantic question similarity and retrieval
- **Embedding Generation**: OpenAI text-embedding-ada-002 for question vectorization
- **Dynamic Follow-up Generation**: o4-mini powered contextual follow-up questions with anti-hallucination
- **Semantic Analysis**: Sentence-transformers for response similarity scoring
- **Post-Interview Feedback**: AI-driven comprehensive analysis with percentile rankings
- **Resume Analysis**: NLP-powered skill extraction and experience parsing
- **Performance Analytics**: Multi-dimensional scoring and historical comparisons

### Platform Features
- **Microservices Architecture**: Scalable, maintainable service-oriented design
- **Background Processing**: Async import and sync operations for large datasets
- **Comprehensive APIs**: RESTful endpoints with OpenAPI documentation
- **Database Flexibility**: Hybrid PostgreSQL + vector database architecture
- **Production-Ready**: Docker containerization with health checks and monitoring

### Enhanced Audio Capabilities
- **Chunked Audio Processing**: Intelligent audio segmentation with 20% overlap deduplication
- **Multi-Model STT**: Hybrid OpenAI Whisper + AssemblyAI for optimal accuracy
- **Advanced TTS**: OpenAI TTS-1 integration with voice caching and persona support
- **Real-time Conversations**: Interactive interview system with live audio processing
- **Session Aggregation**: Multi-turn conversation tracking with complete transcription history
- **Audio Device Management**: Comprehensive microphone and speaker configuration
- **Performance Optimization**: SQLite-based caching for TTS audio files

## 🏗️ Architecture

TalentSync employs a clean microservices architecture optimized for scalability and maintainability:

### Active Services

#### **User Service** (Port 8001) - *Authentication & Profile Management*
- **JWT Authentication**: Secure stateless authentication with bcrypt password hashing
- **User Registration & Login**: Email validation and secure account creation
- **Profile Management**: User profile updates and account management
- **Role-Based Access Control**: Admin and user role management with permissions
- **Security Features**: Password hashing, token expiration, input validation
- **SQLite Database**: Lightweight, reliable user data storage with async operations
- **Inter-Service Integration**: JWT verification for other microservices
- **Comprehensive Testing**: 29+ test cases covering all authentication scenarios
- **Pre-seeded Users**: Development users with standardized credentials
- **API Documentation**: Complete OpenAPI/Swagger documentation

#### **Interview Service** (Port 8002) - *Core Service*
- Interview module and question management
- RAG pipeline for semantic question retrieval with Pinecone vector database
- **Dynamic Follow-Up Generation**: o4-mini powered contextual follow-up questions with anti-hallucination
- **Post-Interview Feedback System**: Comprehensive analysis using semantic similarity, fluency metrics, and AI narratives
- Session orchestration with question tracking and duplicate prevention
- Vector database synchronization with OpenAI embeddings
- Dataset import and management (SWE, ML, DSA, Resume datasets)
- Background task processing with Celery for bulk operations and feedback generation

#### **Resume Service** (Port 8003) - *JSON Storage*
- Resume file upload and parsing (PDF, DOCX, TXT) with local JSON storage
- NLP-powered skill extraction using spaCy en_core_web_lg model
- Thread-safe JSON file operations with atomic writes
- User-based directory organization for scalable file management
- Integration with interview service via internal API endpoints
- No database dependencies - simplified architecture for faster deployment

#### **Transcription Service** (Port 8004) - *Enhanced STT/TTS*
- **Advanced Speech-to-Text**: Hybrid system using OpenAI Whisper + AssemblyAI
- **Chunked Audio Processing**: Intelligent audio segmentation with overlap detection and deduplication
- **Text-to-Speech Integration**: OpenAI TTS (tts-1) with voice synthesis and audio caching
- **Persona-Driven Interviews**: Real-time conversational AI with persona-based responses
- **Session Management**: Multi-turn conversation tracking with aggregated transcriptions
- **Real-time Audio**: WebSocket support for live transcription and TTS playback
- **Audio Device Management**: Comprehensive device enumeration and configuration
- **Multiple Format Support**: WAV, MP3, MP4, FLAC with intelligent format detection
- **Speaker Diarization**: Advanced speaker identification and confidence scoring
- **Caching System**: SQLite-based TTS audio caching for performance optimization

#### **Media Service** (Port 8005) - *Chunked Media Management*
- **Chunked Upload System**: Handles audio/video chunks with sequence management and gap detection
- **Device Enumeration**: Lists available cameras and microphones for frontend selection
- **Session Management**: Tracks upload sessions with metadata and completion detection
- **File Organization**: Structured storage with session-based directories (uploads/{session_id}/)
- **Event Emission**: Notifies Transcription Service of new chunks via HTTP webhooks
- **Background Processing**: Celery workers for metadata extraction and file validation
- **Shared Storage**: Docker volume mounted by both Media and Transcription services
- **Performance Monitoring**: Prometheus metrics and comprehensive health checks
- **Multiple Format Support**: WebM, MP3, WAV, M4A, OGG with validation
- **Inter-Service Integration**: RESTful APIs for Interview Service coordination

### Infrastructure Components
- **PostgreSQL**: Primary database for interview, user, transcription services
- **Local JSON Storage**: Resume service uses file-based storage for simplified deployment
- **Redis**: Caching, session management, and background task queues
- **Pinecone**: Vector database for semantic search and RAG operations
- **Nginx**: API Gateway, reverse proxy, and load balancing

## 🛠️ Technology Stack

### Backend Services
- **Framework**: FastAPI with async/await support
- **Database**: PostgreSQL 13+ with SQLAlchemy ORM (interview, user, transcription services)
- **Storage**: Local JSON files with thread-safe operations (resume service)
- **Vector DB**: Pinecone for embeddings and semantic search
- **Caching**: Redis for performance optimization
- **AI/ML**: OpenAI o4-mini, GPT-4, Whisper, TTS-1, text-embedding-ada-002, sentence-transformers
- **Background Tasks**: Celery with Redis broker for async processing

### Development & Operations
- **Containerization**: Docker with multi-stage builds
- **Orchestration**: Docker Compose for local development
- **API Documentation**: OpenAPI/Swagger with automatic generation
- **Testing**: pytest with async support and comprehensive fixtures
- **Monitoring**: Prometheus metrics and health check endpoints
- **Code Quality**: Black, isort, mypy for code formatting and type checking

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- PostgreSQL 14+
- Redis 6+

### Environment Setup

1. **Clone and navigate to the project**
   ```bash
   git clone <repository-url>
   cd talentsync
   ```

2. **Set up environment variables**
   ```powershell
   # Copy the central environment template
   Copy-Item ".env.example" ".env"
   
   # Update API keys and configuration in .env file
   # Required: OPENAI_API_KEY, PINECONE_API_KEY, ASSEMBLYAI_API_KEY
   ```

3. **Test API Keys (Optional but Recommended)**
   ```powershell
   # Test Pinecone connection
   python -c "
   from pinecone import Pinecone
   import os
   from dotenv import load_dotenv
   
   load_dotenv()
   pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
   print('✅ Pinecone connection successful!')
   print('Available indexes:', pc.list_indexes())
   "
   
   # Test OpenAI connection
   python -c "
   from openai import OpenAI
   import os
   from dotenv import load_dotenv
   
   load_dotenv()
   client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
   print('✅ OpenAI connection successful!')
   print('Available models:', len(list(client.models.list())))
   "
   ```

4. **Launch with Docker Compose**
   ```powershell
   docker-compose up -d
   ```

5. **Initialize databases**
   ```powershell
   # Run migrations for each service
   docker-compose exec user-service alembic upgrade head
   docker-compose exec interview-service alembic upgrade head
   docker-compose exec resume-service alembic upgrade head
   docker-compose exec transcription-service alembic upgrade head
   ```

### Service Endpoints

Once running, services are available at:

- **User Service**: http://localhost:8001
  - API Docs: http://localhost:8001/docs
  - Health: http://localhost:8001/health

- **Interview Service**: http://localhost:8002
  - API Docs: http://localhost:8002/docs
  - Health: http://localhost:8002/health

- **Resume Service**: http://localhost:8003
  - API Docs: http://localhost:8003/docs
  - Health: http://localhost:8003/health

- **Transcription Service**: http://localhost:8004
  - API Docs: http://localhost:8004/docs
  - Health: http://localhost:8004/health

- **API Gateway (nginx)**: http://localhost

### Development Mode

For development, you can run services individually using the central requirements.txt:

```powershell
# Install dependencies
pip install -r requirements.txt

# Download spaCy English model
python -m spacy download en_core_web_sm

# Test API connections (recommended before starting services)
python -c "
from pinecone import Pinecone
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# Test Pinecone
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
print('✅ Pinecone connected')

# Test OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
print('✅ OpenAI connected')
"

# Terminal 1: Interview Service (Core)
cd services/interview-service
uvicorn app.main:app --reload --port 8002

# Terminal 2: User Service
cd services/user-service  
uvicorn app.main:app --reload --port 8001

# Terminal 3: Resume Service
cd services/resume-service
uvicorn app.main:app --reload --port 8003

# Terminal 4: Transcription Service
cd services/transcription-service
uvicorn app.main:app --reload --port 8004
```

### Optional Setup Steps

```bash
# Import question datasets (Optional)
curl -X POST http://localhost:8002/api/v1/datasets/import/all

# Install spaCy English model for resume parsing
python -m spacy download en_core_web_sm
```

## 📊 Datasets

The platform includes comprehensive question datasets for different domains:

### Available Datasets
- **SWE_dataset.json**: 80+ Software Engineering questions covering system design, algorithms, and best practices
- **ML_dataset.json**: 80+ Machine Learning questions covering algorithms, models, and techniques  
- **DSA_dataset.json**: 80+ Data Structures and Algorithms problems with complexity analysis
- **Resume_dataset.json**: Template questions for resume-driven interviews
- **Resumes_dataset.json**: Sample resumes for testing and development

### Dataset Features
- **Structured Format**: Consistent JSON schema with metadata
- **Difficulty Levels**: Easy, Medium, Hard classifications
- **Follow-up Templates**: Predefined follow-up question patterns
- **Ideal Answers**: Reference answers for assessment
- **Domain Tagging**: Categorized for vector search optimization

### Import Process
```bash
# Import all datasets
curl -X POST http://localhost:8002/api/v1/datasets/import/all

# Import specific dataset
curl -X POST "http://localhost:8002/api/v1/datasets/import/path?file_path=/path/to/SWE_dataset.json"

# Check import status
curl http://localhost:8002/api/v1/health
```

## 🔧 Configuration

### Central Configuration

All configuration is managed through a single `.env` file in the root directory. Copy `.env.example` to `.env` and update the values:

#### Required API Keys
```bash
# AI Services
OPENAI_API_KEY=your-openai-api-key-here
PINECONE_API_KEY=your-pinecone-api-key-here
ASSEMBLYAI_API_KEY=your-assemblyai-api-key-here

# Security
SECRET_KEY=your-secret-key-here-change-in-production-make-it-very-long-and-random

# Database
DATABASE_URL=postgresql+asyncpg://talentsync:secret@localhost:5432/talentsync
```

#### Optional Configuration
```bash
# CORS for frontend (if different from defaults)
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:8010"]

# Logging
LOG_LEVEL=INFO
DEBUG=false

# File Upload Limits
MAX_FILE_SIZE=10485760  # 10MB for resumes
TRANSCRIPTION_MAX_FILE_SIZE=52428800  # 50MB for audio
```

#### Resume Service
```bash
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/talentsync_resumes
OPENAI_API_KEY=your-openai-api-key
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10485760
```

#### Transcription Service
```bash
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/talentsync_transcription
OPENAI_API_KEY=your-openai-api-key
ASSEMBLYAI_API_KEY=your-assemblyai-api-key
UPLOAD_DIR=./uploads
TTS_CACHE_DIR=./tts_files
MAX_AUDIO_FILE_SIZE=52428800  # 50MB
CHUNK_OVERLAP_THRESHOLD=0.2   # 20% overlap for deduplication
```

## 🧪 Testing

### Running Tests

Each service includes comprehensive test suites:

```bash
# Test individual services
cd services/interview-service && pytest tests/ -v
cd services/user-service && pytest tests/ -v
cd services/resume-service && pytest tests/ -v
cd services/transcription-service && pytest tests/ -v

# Run with coverage
pytest --cov=app tests/ --cov-report=html
```

### API Testing

Test API endpoints using the interactive documentation:

- Interview Service: http://localhost:8002/docs
- User Service: http://localhost:8001/docs  
- Resume Service: http://localhost:8003/docs
- Transcription Service: http://localhost:8004/docs

## 📚 API Documentation

Each service provides comprehensive API documentation:

### OpenAPI/Swagger Documentation
- **Interview Service**: http://localhost:8002/docs
- **User Service**: http://localhost:8001/docs
- **Resume Service**: http://localhost:8003/docs
- **Transcription Service**: http://localhost:8004/docs

### Service-Specific Documentation
- [Interview Service README](services/interview-service/README.md) - Core orchestration and RAG pipeline
- [User Service README](services/user-service/README.md) - Authentication and user management
- [Resume Service README](services/resume-service/README.md) - Resume parsing and analysis
- [Transcription Service README](services/transcription-service/README.md) - Audio transcription and device management

## 🔍 Monitoring & Health Checks

### Health Endpoints
Each service provides health check endpoints for monitoring:

```bash
# Service health
curl http://localhost:8001/api/v1/health  # User Service
curl http://localhost:8002/api/v1/health  # Interview Service
curl http://localhost:8003/api/v1/health  # Resume Service  
curl http://localhost:8004/api/v1/health  # Transcription Service

# Database connectivity
curl http://localhost:8002/api/v1/health/database

# Vector database health
curl http://localhost:8002/api/v1/health/vector
```

### Metrics
Prometheus metrics are available at `/metrics` endpoint for each service:

```bash
curl http://localhost:8002/metrics  # Interview Service metrics
```

## 🚀 Production Deployment

### Docker Compose Production
```bash
# Production deployment with optimized settings
docker-compose up -d
```

### Environment-Specific Configuration
- **Development**: Local PostgreSQL, Redis, and Pinecone emulator
- **Staging**: Cloud databases with test API keys  
- **Production**: Production databases, monitoring, and security configurations

### Security Considerations
- JWT token authentication with configurable expiration
- CORS configuration for frontend integration
- Rate limiting on authentication endpoints
- Input validation and sanitization
- Secure file upload handling

## 🛠️ Development

### Code Quality Standards
- **Type Hints**: Full typing support with mypy
- **Linting**: Black, isort, and flake8 for consistent formatting
- **Testing**: pytest with async support and comprehensive fixtures
- **Documentation**: Comprehensive docstrings and API documentation

### Project Structure
```
talentsync/
├── services/
│   ├── interview-service/     # Core orchestration service
│   ├── user-service/         # Authentication and user management
│   ├── resume-service/       # Resume parsing and analysis
│   └── transcription-service/ # Audio transcription
├── docs/                     # Technical documentation
├── frontend/                 # Frontend application (when added)
├── scripts/                  # Development and deployment scripts
├── ssl/                      # SSL certificates directory
├── docker-compose.yml        # Central Docker configuration
├── nginx.conf               # Reverse proxy configuration
├── .env.example             # Central environment template
├── requirements.txt         # Central Python dependencies
└── README.md               # This file
```

## 🚀 Getting Started

Follow these instructions to get TalentSync up and running on your local machine:

### Prerequisites

- Docker and Docker Compose
- Git
- OpenAI API key (for LLM capabilities, embeddings, and transcription)
- Pinecone API key (for vector database - or use the included local emulator)
- AssemblyAI API key (optional, for enhanced transcription capabilities)
- 8GB+ RAM and 4+ CPU cores for running all services

### Installation and Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/talentsync.git
   cd talentsync
   ```

2. Create a `.env` file in the root directory with the required API keys:
   ```
   # Required API Keys
   OPENAI_API_KEY=your_openai_api_key
   PINECONE_API_KEY=your_pinecone_api_key  # or use "local" for the emulator
   ASSEMBLYAI_API_KEY=your_assemblyai_api_key  # optional
   
   # Security
   SECRET_KEY=your-secret-key-here-change-in-production
   ```

3. Start all services with Docker Compose:
   ```bash
   docker-compose up -d
   ```

4. Verify all services are running:
   ```bash
   python check_services.py
   ```

5. Import the interview question datasets (first time setup):
   ```bash
   curl -X POST http://localhost:8003/api/v1/datasets/import/all
   ```

6. Access the web application at http://localhost:3000

### Checking Service Status

The included `check_services.py` script provides a quick way to verify that all services are operational:

```bash
python check_services.py
```

This will display the health status of all services in the stack:
- User Service (8001)
- Media Service (8002)  
- Interview Service (8003)
- Resume Service (8004)
- Transcription Service (8005)
- Feedback Service (8006)
- Frontend (3000)
- Nginx Proxy (80)

### Running Individual Services for Development

While Docker Compose is the recommended way to run the full system, you can run individual services for development:

#### Interview Service (Core)

```powershell
cd services/interview-service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8003
```

#### Frontend

```powershell
cd frontend
npm install
npm run dev
```

The development frontend will be available at http://localhost:5173 and will connect to the backend services through the nginx proxy.

### Using the Integrated Platform

1. **User Authentication**: Sign up or log in at the landing page
2. **Browse Modules**: Explore interview modules by domain and difficulty on the dashboard 
3. **Start Session**: Select a module to create a new interview session
4. **Prepare in Lobby**:
   - Upload your resume for personalized questions
   - Test your microphone and camera
   - Adjust audio settings
5. **Complete Interview**:
   - Answer questions asked by the AI interviewer
   - Audio is automatically recorded, transcribed, and analyzed
   - Dynamic follow-up questions are generated based on your responses
6. **Review Feedback**:
   - Receive comprehensive performance analytics
   - Get AI-generated feedback on strengths and areas for improvement
   - Compare your performance against historical data

### Integrated Services Architecture

TalentSync uses a microservices architecture with all services integrated through an nginx proxy:

| Service | Port | Description | Integration Points |
|---------|------|-------------|-------------------|
| Frontend | 3000 | React application | Connects to all backend services via nginx proxy |
| User Service | 8001 | Authentication & profiles | Provides JWT authentication for all services |
| Media Service | 8002 | Audio/video handling | Processes and stores interview media files |
| Interview Service | 8003 | Core orchestration | Manages interview sessions and questions |
| Resume Service | 8004 | Resume parsing | Extracts information from uploaded resumes |
| Transcription Service | 8005 | STT/TTS | Handles audio transcription and text-to-speech |
| Feedback Service | 8006 | Analytics & reports | Generates interview performance reports |
| Nginx Proxy | 80 | API Gateway | Routes all API requests to appropriate services |

### Key Integration Points

- **API Gateway**: All backend API requests go through the nginx proxy at `/api/*` endpoints
- **Shared Authentication**: JWT tokens issued by the User Service are validated across all services
- **Resource Sharing**: Services share resources through Docker volumes:
  - `media_uploads`: Shared between Media and Transcription services
  - `resume_uploads`: Used by the Resume service for storing parsed resumes
  - `audio_uploads`: Used by Transcription service for audio processing
- **Database**: Interview Service now uses SQLite instead of PostgreSQL for simplified deployment
- **Vector Database**: Pinecone (or local emulator) for semantic search capabilities

### Health and Monitoring

You can check the health of individual services at their health endpoints:

```bash
curl http://localhost:8001/api/v1/health  # User Service
curl http://localhost:8002/api/v1/health  # Media Service
curl http://localhost:8003/api/v1/health  # Interview Service
curl http://localhost:8004/api/v1/health  # Resume Service
curl http://localhost:8005/api/v1/health  # Transcription Service
curl http://localhost:8006/api/v1/health  # Feedback Service
```

Or use the provided health check script for a comprehensive overview:

```bash
python check_services.py
```

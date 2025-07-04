# TalentSync - AI-Powered Interview Platform

TalentSync is an intelligent, AI-powered interview platform that delivers personalized technical interviews through domain-specific modules, adaptive questioning, and real-time audio capabilities with comprehensive performance analytics.

## 🚀 Features

### Core Interview Capabilities
- **Domain-Specific Modules**: Software Engineering, Machine Learning, Data Structures & Algorithms, Resume-Driven Questions
- **Intelligent Question Generation**: RAG-powered follow-up questions based on candidate responses
- **Semantic Search**: Vector-based question retrieval using Pinecone and OpenAI embeddings
- **Resume-Driven Interviews**: Dynamic question generation based on candidate background
- **Real-time Transcription**: Hybrid STT using OpenAI Whisper and AssemblyAI

### AI & Machine Learning
- **Vector Database Integration**: Pinecone for semantic question similarity and retrieval
- **Embedding Generation**: OpenAI text-embedding-ada-002 for question vectorization
- **Intelligent Follow-ups**: Context-aware question progression
- **Resume Analysis**: NLP-powered skill extraction and experience parsing
- **Performance Analytics**: AI-driven interview assessment and feedback

### Platform Features
- **Microservices Architecture**: Scalable, maintainable service-oriented design
- **Background Processing**: Async import and sync operations for large datasets
- **Comprehensive APIs**: RESTful endpoints with OpenAPI documentation
- **Database Flexibility**: Hybrid PostgreSQL + vector database architecture
- **Production-Ready**: Docker containerization with health checks and monitoring

## 🏗️ Architecture

TalentSync employs a clean microservices architecture optimized for scalability and maintainability:

### Active Services

#### **User Service** (Port 8001)
- User authentication and profile management
- JWT token-based security with role-based access control
- OAuth2 with Password flow
- Password reset and user management APIs

#### **Interview Service** (Port 8002) - *Core Service*
- Interview module and question management
- RAG pipeline for semantic question retrieval
- Vector database synchronization with Pinecone
- Session orchestration and progress tracking
- Dataset import and management (SWE, ML, DSA, Resume datasets)
- Background task processing for bulk operations

#### **Resume Service** (Port 8003)
- Resume file upload and parsing (PDF, DOCX, TXT)
- NLP-powered skill extraction and experience analysis
- Resume embedding generation for semantic search
- Job matching and compatibility scoring
- Integration with interview question generation

#### **Transcription Service** (Port 8004)
- Hybrid speech-to-text using OpenAI Whisper + AssemblyAI
- Real-time audio transcription with WebSocket support
- Audio device enumeration and management
- Multiple format support (WAV, MP3, MP4, FLAC)
- Speaker diarization and confidence scoring

### Infrastructure Components
- **PostgreSQL**: Primary database with hybrid relational/vector capabilities
- **Redis**: Caching, session management, and background task queues
- **Pinecone**: Vector database for semantic search and RAG operations
- **Nginx**: API Gateway, reverse proxy, and load balancing

## 🛠️ Technology Stack

### Backend Services
- **Framework**: FastAPI with async/await support
- **Database**: PostgreSQL 13+ with SQLAlchemy ORM
- **Vector DB**: Pinecone for embeddings and semantic search
- **Caching**: Redis for performance optimization
- **AI/ML**: OpenAI GPT-4, Whisper, text-embedding-ada-002
- **Background Tasks**: FastAPI background tasks with async processing

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
- Valid API keys (OpenAI, Pinecone, AssemblyAI)

### Environment Setup

1. **Clone and navigate to the project**
   ```bash
   git clone <repository-url>
   cd talentsync
   ```

2. **Create environment configuration**
   ```bash
   cp .env.example .env
   ```
   
   Update `.env` with your API keys:
   ```bash
   # API Keys (Required)
   OPENAI_API_KEY=your_openai_api_key_here
   PINECONE_API_KEY=your_pinecone_api_key_here
   ASSEMBLYAI_API_KEY=your_assemblyai_api_key_here
   
   # Database Configuration
   DATABASE_URL=postgresql+asyncpg://talentsync:secret@localhost:5432/talentsync
   REDIS_URL=redis://localhost:6379
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

4. **Start infrastructure services**
   ```bash
   # PostgreSQL
   docker run --name talentsync-postgres -e POSTGRES_USER=talentsync -e POSTGRES_PASSWORD=secret -e POSTGRES_DB=talentsync -p 5432:5432 -d postgres:14
   
   # Redis
   docker run --name talentsync-redis -p 6379:6379 -d redis:6-alpine
   ```

5. **Start Interview Service**
   ```bash
   cd services/interview-service
   uvicorn app.main:app --reload --port 8002
   ```

6. **Import datasets and sync vectors**
   ```bash
   # Import all datasets into PostgreSQL
   Invoke-RestMethod -Method POST -Uri "http://localhost:8002/api/v1/datasets/import/all"
   
   # Sync questions to Pinecone vector database
   Invoke-RestMethod -Method POST -Uri "http://localhost:8002/api/v1/vectors/sync/questions/all"
   ```

7. **Test the RAG pipeline**
   ```bash
   # Test semantic search
   Invoke-RestMethod -Method GET -Uri "http://localhost:8002/api/v1/vectors/search?query=distributed%20systems&top_k=3"
   ```

8. **Access API documentation**
   Open browser: `http://localhost:8002/docs`

### ✅ Verified Working Setup

The system is currently operational with:
- **95 questions imported** across 5 modules (DSA, ML, Resume, SWE)
- **Vector embeddings stored** in Pinecone for semantic search
- **RAG pipeline functional** with high-quality semantic matching
- **All API endpoints tested** and working
- **Complete documentation** available at `/docs`

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

### Contributing Guidelines
1. Follow the coding conventions in `docs/talent_sync_coding_conventions.md`
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Use meaningful commit messages and PR descriptions
5. Ensure all health checks pass before deployment

## 📄 License

Copyright © 2025 TalentSync. All rights reserved.

## 🔗 Additional Resources

- [Technical Architecture](docs/talent_sync_tech_architecture.md)
- [Project Specifications](docs/talent_sync_project_spec.md)
- [Coding Conventions](docs/talent_sync_coding_conventions.md)

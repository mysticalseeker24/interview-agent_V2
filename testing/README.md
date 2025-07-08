# TalentSync Testing Documentation

This directory contains comprehensive testing documentation for all TalentSync services.

## 🎯 Quick Start

Each service has its own dedicated testing guide with complete setup and validation procedures.

## 📁 Testing Guides

### Core Services
- **[User Service Testing](user-service-testing.md)** - JWT authentication, profile management, security testing
- **[Interview Service Testing](interview-service-testing.md)** - Dynamic question generation, follow-up creation, RAG pipeline
- **[Resume Service Testing](resume-service-testing.md)** - Multi-template resume parsing, text-to-JSON pipeline
- **[Transcription Service Testing](transcription-service-testing.md)** - Enhanced STT/TTS, chunked audio, persona interviews
- **[Media Service Testing](media-service-testing.md)** - Chunked uploads, device enumeration, session management

### Upcoming Services
- **User Service Testing** - Authentication, user management
- **Frontend Testing** - UI/UX validation, integration testing

## 🚀 Service Status Overview

| Service | Status | Testing | Key Features |
|---------|--------|---------|--------------|
| User Service | ✅ Complete | ✅ Validated | JWT auth, Profile management, Security |
| Interview Service | ✅ Complete | ✅ Validated | RAG, Follow-ups, o4-mini |
| Resume Service | ✅ Complete | ✅ Validated | Multi-template, LLM enhancement |
| Transcription Service | ✅ Complete | ✅ Validated | Enhanced STT/TTS, Chunked Audio, Personas |
| Media Service | ✅ Complete | ✅ Validated | Chunked uploads, Device enumeration, Events |
| Frontend | 🔄 In Progress | ⏳ Pending | React UI |

## 🛠️ Infrastructure Requirements

### Essential Infrastructure
- **PostgreSQL 14+** - Primary database for interview service
- **SQLite** - Local database for media service metadata
- **Redis 6+** - Caching, session management, and background tasks
- **Python 3.11+** - Runtime environment

### API Keys Required
- **OpenAI API Key** - For LLM features (interview + resume services)
- **Pinecone API Key** - For vector database (interview service)
- **AssemblyAI API Key** - For transcription service (upcoming)

### Development Tools
- **Docker** - For PostgreSQL and Redis
- **Node.js** - For frontend development
- **Git** - Version control

## 🧪 Testing Workflow

### 1. Environment Setup
```bash
# Clone and navigate to project
git clone <repository>
cd talentsync

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### 2. Infrastructure Start
```bash
# Start PostgreSQL and Redis
docker run --name talentsync-postgres -e POSTGRES_USER=talentsync -e POSTGRES_PASSWORD=secret -e POSTGRES_DB=talentsync -p 5432:5432 -d postgres:14
docker run --name talentsync-redis -p 6379:6379 -d redis:6-alpine
```

### 3. Service Testing
```bash
# Test individual services (follow specific testing guides)
cd services/user-service && python -m pytest tests/ -v
cd services/interview-service && python test_codebase.py
cd services/resume-service && python test_comprehensive.py
cd services/media-service && python test_comprehensive.py
```

### 4. Integration Testing
```bash
# Test service-to-service communication
# Start all services and run integration tests
```

## 📊 Performance Benchmarks

### User Service
- **User Registration**: ~100ms average
- **User Login**: ~80ms average
- **Profile Retrieval**: ~20ms average
- **Token Validation**: ~5ms average

### Interview Service
- **Question Generation**: ~1-2 seconds
- **Follow-up Creation**: ~2-4 seconds (with LLM)
- **Vector Search**: ~200-800ms
- **Database Query**: ~100-500ms

### Resume Service
- **Basic Extraction**: ~0.8s per resume
- **LLM Enhancement**: ~8-12s per resume
- **Confidence Improvement**: +5-15% with LLM
- **Cost**: $0.001-0.005 per resume (with LLM)

### Media Service
- **Chunk Upload**: <2 seconds for 10MB file
- **Session Summary**: <100ms
- **Device Enumeration**: <50ms
- **Health Check**: <20ms
- **Concurrent Users**: 100+ simultaneous uploads

## 🔧 Common Setup Issues

### Dependency Issues
```bash
# Fix Pinecone package
pip uninstall pinecone-client -y && pip install pinecone

# Install spaCy model
python -m spacy download en_core_web_sm
```

### Infrastructure Issues
```bash
# Check PostgreSQL
docker exec -it talentsync-postgres psql -U talentsync -d talentsync -c "SELECT version();"

# Check Redis
docker exec -it talentsync-redis redis-cli ping

# Check User Service Health
curl http://localhost:8001/

# Check Media Service Storage
ls -la services/media-service/uploads/

# Test Media Service Health
curl http://localhost:8005/health
```

### API Key Issues
```bash
# Validate OpenAI
python -c "import openai; client = openai.OpenAI(api_key='your-key'); print('✅ OpenAI OK')"

# Validate Pinecone
python -c "from pinecone import Pinecone; pc = Pinecone(api_key='your-key'); print('✅ Pinecone OK')"
```

## 📈 Testing Metrics

### Coverage Goals
- **Unit Tests**: >80% code coverage per service
- **Integration Tests**: All API endpoints validated
- **Performance Tests**: Response time benchmarks
- **Load Tests**: Concurrent user simulation

### Quality Gates
- **All tests pass** before deployment
- **Performance within benchmarks**
- **Security scan clean**
- **Documentation updated**

## 🔐 Security Testing

### API Security
- Authentication validation
- Authorization checks
- Input sanitization
- Rate limiting verification

### Data Security
- Encryption at rest and in transit
- PII handling compliance
- API key protection
- Database security

## 📚 Additional Resources

- **[Project Architecture](../docs/talent_sync_tech_architecture.md)** - System design and components
- **[API Documentation](../docs/talent_sync_project_spec.md)** - Complete API specifications
- **[Coding Standards](../docs/talent_sync_coding_conventions.md)** - Development guidelines

## 🤝 Contributing

When adding new services or features:

1. Create service-specific testing guide
2. Include comprehensive test scripts
3. Document performance benchmarks
4. Validate integration points
5. Update this overview documentation

## 📞 Support

For testing issues or questions:
- Check service-specific testing guides
- Review troubleshooting sections
- Validate environment setup
- Ensure all prerequisites are met

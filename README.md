# TalentSync Platform

A comprehensive AI-powered talent management and interview platform with advanced resume parsing, intelligent interview preparation, and automated feedback systems.

## 🚀 Overview

TalentSync is a modern microservices-based platform designed to revolutionize the hiring process through AI-powered resume analysis, intelligent interview preparation, and comprehensive candidate evaluation.

## 🏗️ Architecture

### Core Services

| Service                | Port  | Description                                 | Status              |
|------------------------|-------|---------------------------------------------|---------------------|
| **Resume Service**     | 8004  | LLM-powered resume parsing with 95% accuracy| ✅ Production Ready  |
| **User Service**       | 8001  | Authentication and user management          | ✅ Production Ready  |
| **Interview Service**  | 8002  | AI interview preparation and question gen   | ✅ Production Ready  |
| **Media Service**      | 8003  | Chunked audio/video uploads & device mgmt   | ✅ Production Ready  |
| **Transcription Service** | 8005 | Audio/video transcription and analysis      | ✅ Production Ready  |
| **Feedback Service**   | 8006  | AI-powered interview feedback and scoring   | ✅ Production Ready  |

### Technology Stack

- **Backend**: FastAPI, Python 3.11
- **AI/ML**: OpenAI GPT-4o-mini, Groq Whisper Large v3, Groq PlayAI TTS, spaCy, TensorFlow
- **Database**: PostgreSQL with Supabase, SQLite (service-specific)
- **File Storage**: Local + Cloud storage
- **Containerization**: Docker & Docker Compose
- **API**: RESTful APIs with OpenAPI documentation

## 🎯 Key Features

### Resume Service
- LLM-powered parsing (PDF, DOCX, TXT)
- Large file support, confidence scoring, domain detection

### Interview Service
- Dynamic, context-aware question generation
- Domain-specific content, follow-up logic

### User Service
- Secure authentication (JWT, Supabase)
- Role and profile management

### **Media Service**
- Chunked audio/video uploads for interviews
- Device enumeration for frontend (cameras, mics)
- Session management and file validation
- Event emission to transcription and interview services
- Async background processing (Celery)
- Health checks and Prometheus metrics

### Transcription & Feedback
- High-accuracy audio/video transcription (Groq Whisper Large v3)
- High-quality text-to-speech synthesis (Groq PlayAI TTS)
- 9 different interviewer personas with unique voices and personalities
- Automated feedback and scoring (Blackbox AI)
- Real-time chunked processing with 2-second overlap

## 🚀 Quick Start

### Prerequisites
```bash
# Required environment variables
export OPENAI_API_KEY="your-openai-api-key"
export GROQ_API_KEY="your-groq-api-key"  # For STT and TTS
export SUPABASE_URL="your-supabase-url"
export SUPABASE_KEY="your-supabase-key"
```

### Development Setup
```bash
git clone <repository-url>
cd talentsync

# Set up environment variables
cp services/interview-service/env.example services/interview-service/.env
# Edit .env with your API keys

# Upload datasets and start interview service
cd services/interview-service
python start_service.py

# Or start individual services
cd ../media-service
uvicorn app.main:app --reload --port 8003
```

### Production Deployment
```bash
# Upload datasets first (if not already done)
cd services/interview-service
python upload_datasets_to_pinecone.py

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Or deploy individual services
cd services/media-service
docker build -t media-service .
docker run -p 8003:8003 media-service
```

## 📁 Project Structure
```
talentsync/
├── data/                          # Interview datasets
├── docs/                          # Documentation
├── services/                      # Microservices
│   ├── resume-service/           # LLM-powered resume parsing
│   ├── user-service/             # Authentication & user management
│   ├── interview-service/        # AI interview preparation
│   ├── media-service/            # Audio/video uploads & device mgmt
│   ├── transcription-service/    # Audio/video transcription
│   └── feedback-service/         # AI feedback & scoring
└── supabase/                     # Database migrations
```

## 🔧 Configuration

Set environment variables in `.env` or as needed for each service. See each service's `env.example` for details.

## 📊 Dataset Management

The Interview Service uses Pinecone as a vector database for storing question embeddings. Before running the service, you need to upload datasets:

### Dataset Upload Process
```bash
# Upload all datasets to Pinecone
cd services/interview-service
python upload_datasets_to_pinecone.py

# Upload specific dataset only
python upload_datasets_to_pinecone.py --dataset DSA_dataset.json

# Verify existing upload
python upload_datasets_to_pinecone.py --verify-only

# Test RAG pipeline
python upload_datasets_to_pinecone.py --test-rag
```

### Supported Datasets
- **DSA_dataset.json**: Data Structures & Algorithms (243 questions)
- **DevOps_dataset.json**: DevOps & Infrastructure (243 questions)
- **Kubernetes_dataset.json**: Kubernetes-specific questions (243 questions)
- **AI_Engineering_dataset.json**: AI Engineering (243 questions)
- **ML_dataset.json**: Machine Learning (243 questions)
- **LLM_NLP_dataset.json**: LLM/NLP topics (243 questions)
- **SWE_dataset.json**: Software Engineering (243 questions)
- **Resume_dataset.json**: Resume-based questions (243 questions)
- **Resumes_dataset.json**: Resume data for personalization (888 entries)

### Performance Features
- **Batch Processing**: Uploads questions in configurable batches (default: 50)
- **Caching**: Multi-level caching for embeddings and generated questions
- **Circuit Breakers**: Prevents cascading failures from external services
- **Progress Tracking**: Real-time upload progress and statistics

## 📈 API Endpoints

Each service exposes RESTful endpoints. See `/docs` on each service for OpenAPI documentation.

## 🧪 Testing

- Run `pytest` in each service directory for unit/integration tests.
- Use the provided test scripts for end-to-end and API testing.

## 🔒 Security Features

- Rate limiting, input validation, error handling, CORS, JWT authentication

## 📊 Monitoring & Analytics

- Health checks: `/health` endpoint on each service
- Metrics: `/metrics` and `/prometheus` endpoints (where available)

## 🚀 Deployment

- Use Docker Compose for local and production deployments
- Kubernetes manifests available for advanced orchestration

## 🔄 CI/CD Pipeline

- Automated testing, builds, and deployment via GitHub Actions

## 📚 Documentation

- [Technical Architecture](docs/talentsync-technical-architecture.md)
- [Coding Conventions](docs/talentsync-coding-conventions.md)
- [Project Specifications](docs/talentsync-project-specs.md)
- [Supabase Migration Guide](docs/supabase-migration-guide.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes and add tests
4. Submit a pull request

## 📄 License

MIT License

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the troubleshooting guide

---

**TalentSync Platform** - Revolutionizing talent management with AI-powered solutions. 
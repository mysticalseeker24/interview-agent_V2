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
- **AI/ML**: OpenAI GPT-4o-mini, spaCy, TensorFlow
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
- High-accuracy audio/video transcription (Groq Whisper)
- Automated feedback and scoring (Blackbox AI)

## 🚀 Quick Start

### Prerequisites
```bash
# Required environment variables
export OPENAI_API_KEY="your-openai-api-key"
export SUPABASE_URL="your-supabase-url"
export SUPABASE_KEY="your-supabase-key"
```

### Development Setup
```bash
git clone <repository-url>
cd talentsync
docker-compose up -d
# Or start individual services
cd services/media-service
uvicorn app.main:app --reload --port 8003
```

### Production Deployment
```bash
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
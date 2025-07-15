# TalentSync - AI-Powered Interview Platform

A comprehensive microservices-based platform for conducting AI-powered technical interviews with real-time feedback and analytics.

## 🚀 Quick Start

### Prerequisites

- **Node.js** (v18 or higher)
- **Python** (v3.9 or higher)
- **Docker** and **Docker Compose**
- **Git**

### 1. Supabase Local Setup (Required First)

Before starting any services, you must set up Supabase locally:

#### Install Supabase CLI
```bash
# Using npm (recommended)
npm install -g supabase

# Or using other package managers
# Homebrew (macOS): brew install supabase/tap/supabase
# Scoop (Windows): scoop bucket add supabase https://github.com/supabase/scoop-bucket.git && scoop install supabase
```

#### Initialize and Start Supabase
```bash
# Navigate to project root
cd talentsync

# Initialize Supabase (if not already done)
supabase init

# Start local Supabase
supabase start

# Verify it's running
supabase status
```

**Local Supabase URLs:**
- **Studio Dashboard**: http://localhost:54323
- **API URL**: http://127.0.0.1:54321
- **Database**: postgresql://postgres:postgres@127.0.0.1:54322/postgres

#### Database Schema Setup
```bash
# Apply migrations to create required tables
supabase db reset

# This will create the user_profiles table and RLS policies
```

### 2. Environment Configuration

Copy the example environment files and configure your services:

```bash
# User Service
cp services/user-service/.env.example services/user-service/.env

# Resume Service
cp services/resume-service/env.example services/resume-service/.env

# Edit the .env files with your local Supabase credentials
# The default local credentials are already in the templates
```

### 3. Start Services

#### User Service
```bash
cd services/user-service

# Install dependencies
pip install -r requirements.txt

# Start the service
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

#### Resume Service
```bash
cd services/resume-service

# Install dependencies
pip install -r requirements.txt

# Download spaCy model (required)
python -m spacy download en_core_web_lg

# Start the service
python main.py
```

**Service URLs:**
- **User Service API**: http://localhost:8001
- **Resume Service API**: http://localhost:8004
- **Health Checks**: http://localhost:8001/health, http://localhost:8004/api/v1/health

## 📁 Project Structure

```
talentsync/
├── services/                 # Microservices
│   ├── user-service/        # Authentication & User Management ✅
│   ├── resume-service/      # Resume Parsing & Analysis ✅
│   ├── interview-service/   # Interview Logic & Question Management 🚧
│   ├── feedback-service/    # AI Feedback Generation 🚧
│   ├── media-service/       # Audio/Video Processing 🚧
│   └── transcription-service/ # Speech-to-Text & TTS 🚧
├── data/                    # Interview Datasets
│   ├── AI_Engineering_dataset.json
│   ├── DevOps_dataset.json
│   ├── DSA_dataset.json
│   ├── Kubernetes_dataset.json
│   ├── LLM_NLP_dataset.json
│   ├── ML_dataset.json
│   ├── Resume_dataset.json
│   ├── Resumes_dataset.json
│   └── SWE_dataset.json
├── docs/                    # Documentation
│   ├── talentsync-coding-conventions.md
│   ├── talentsync-project-specs.md
│   ├── talentsync-technical-architecture.md
│   └── supabase-migration-guide.md
├── supabase/               # Local Supabase Configuration
│   ├── config.toml
│   ├── migrations/
│   └── seed.sql
└── testing/               # Service Testing Documentation
```

## 🔧 Services Overview

### User Service ✅ (Complete)
- **Status**: Production Ready
- **Port**: 8001
- **Features**: 
  - User authentication (signup/login)
  - Profile management
  - JWT token handling
  - Supabase integration
- **Tech Stack**: FastAPI, Supabase, Python
- **Testing**: Comprehensive integration tests

### Resume Service ✅ (Complete)
- **Status**: Production Ready
- **Port**: 8004
- **Features**: 
  - Multi-format resume parsing (PDF, DOCX, TXT)
  - Advanced text extraction with fallback methods
  - Entity recognition using spaCy
  - Optional LLM enhancement for improved accuracy
  - Structured JSON output with confidence scoring
- **Tech Stack**: FastAPI, spaCy, PyPDF2, OpenAI
- **Performance**: 3-20 seconds processing time per document

### Interview Service 🚧 (In Progress)
- **Status**: Development
- **Port**: 8002
- **Features**: 
  - Question management
  - Interview session handling
  - Dynamic follow-up questions
- **Tech Stack**: FastAPI, Pinecone, OpenAI

### Feedback Service 🚧 (Planned)
- **Status**: Planned
- **Port**: 8003
- **Features**: 
  - AI-powered feedback generation
  - Performance analytics
  - Score calculation
- **Tech Stack**: FastAPI, OpenAI, ML models

### Media Service 🚧 (Planned)
- **Status**: Planned
- **Port**: 8005
- **Features**: 
  - Audio/video processing
  - Real-time streaming
  - Media storage
- **Tech Stack**: FastAPI, WebRTC, FFmpeg

### Transcription Service 🚧 (Planned)
- **Status**: Planned
- **Port**: 8006
- **Features**: 
  - Speech-to-text conversion
  - Text-to-speech synthesis
  - Real-time transcription
- **Tech Stack**: FastAPI, Whisper, TTS engines

## 🧪 Testing

### User Service Testing
```bash
cd services/user-service

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run integration tests
pytest tests/test_integration.py
```

### Resume Service Testing
```bash
cd services/resume-service

# Run comprehensive tests
python test_comprehensive.py

# Test LLM integration
python test_llm_integration.py

# Test PDF workflow
python test_pdf_workflow.py
```

### Supabase Testing
```bash
# Test Supabase connection
supabase status

# Reset database (clears all data)
supabase db reset

# View logs
supabase logs
```

## 🔒 Security

### Environment Variables
- All sensitive data is stored in `.env` files
- Never commit `.env` files to version control
- Use different credentials for development/staging/production

### Supabase Security
- RLS (Row Level Security) policies are enabled
- JWT tokens are used for authentication
- Service role keys are restricted to backend services only

## 🚀 Deployment

### Local Development
```bash
# Start all services (when implemented)
docker-compose up -d

# Or start individually
cd services/user-service && python -m uvicorn app.main:app --reload
cd services/resume-service && python main.py
```

### Production Deployment
1. Set up cloud Supabase project
2. Configure production environment variables
3. Deploy services to cloud infrastructure
4. Set up monitoring and logging

## 📚 API Documentation

### User Service API
- **OpenAPI Docs**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

### Resume Service API
- **OpenAPI Docs**: http://localhost:8004/docs
- **Health Check**: http://localhost:8004/api/v1/health

### Available Endpoints

#### User Service
- `POST /auth/signup` - User registration
- `POST /auth/login` - User authentication
- `GET /users/profile` - Get user profile
- `PUT /users/profile` - Update user profile
- `GET /health` - Health check

#### Resume Service
- `POST /upload` - Upload and process resume files
- `GET /resume/{id}` - Retrieve processed resume data
- `GET /resumes` - List all processed resumes
- `DELETE /resume/{id}` - Delete a resume
- `POST /process-text` - Process raw text directly
- `GET /pipeline/info` - Get pipeline information

## 🔧 Development

### Adding New Services
1. Create new service directory in `services/`
2. Follow the established patterns from user-service
3. Add service documentation to this README
4. Update docker-compose.yml (when implemented)

### Code Conventions
- Follow PEP 8 for Python code
- Use FastAPI for all backend services
- Implement comprehensive testing
- Document all APIs with OpenAPI/Swagger

### Database Migrations
```bash
# Create new migration
supabase migration new migration_name

# Apply migrations
supabase db reset

# View migration history
supabase migration list
```

## 🐛 Troubleshooting

### Common Issues

#### Supabase Connection Issues
```bash
# Check if Supabase is running
supabase status

# Restart Supabase
supabase stop
supabase start

# Reset database
supabase db reset
```

#### Service Connection Issues
- Verify environment variables are set correctly
- Check if required ports are available
- Ensure all dependencies are installed

#### Resume Service Issues
```bash
# Check spaCy model installation
python -c "import spacy; spacy.load('en_core_web_lg')"

# Reinstall spaCy model if needed
python -m spacy download en_core_web_lg
```

#### Database Issues
```bash
# Reset database
supabase db reset

# View database logs
supabase logs db
```

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Follow coding conventions
4. Add tests for new features
5. Update documentation
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Support

For support and questions:
- Create an issue in the repository
- Check the documentation in the `docs/` folder
- Review the service-specific README files

---

**Last Updated**: January 2025
**Version**: 0.1.0 
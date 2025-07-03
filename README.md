# TalentSync - AI-Powered Interview Platform

TalentSync is an end-to-end AI-powered interview platform designed to simulate real-world technical interviews through domain-specific modules, adaptive questioning, and real-time audio/video capabilities.

## 🚀 Features

- **Dynamic Interview Modules**: 8 core domains (Software Engineering, DevOps, Kubernetes, DSA, ML, AI Engineering, LLMs, Resume-Driven)
- **Adaptive AI Interviewer**: Personalized Q&A based on candidate profiles and responses
- **Real-time Audio/Video**: Professional browser-based interview experience
- **Performance Analytics**: Comprehensive scoring with AI-generated feedback
- **Microservices Architecture**: Scalable, maintainable service-oriented design

## 🏗️ Architecture

TalentSync uses a microservices architecture with the following components:

### Core Services
- **User Service** (Port 8001): Authentication and profile management
- **Interview Service** (Port 8002): Module management and session orchestration
- **Resume Service** (Port 8003): Resume parsing and analysis
- **Media Service** (Port 8004): Audio/video handling and WebRTC signaling
- **Transcription Service** (Port 8005): Speech-to-text with Whisper & AssemblyAI
- **Feedback Service** (Port 8006): Performance scoring and AI feedback
- **Admin Service** (Port 8007): Administrative management and analytics

### Infrastructure
- **PostgreSQL**: Primary database for structured data
- **Redis**: Caching, session state, and task queues
- **Pinecone**: Vector database for RAG-based question generation
- **Nginx**: API Gateway and reverse proxy

## 🛠️ Tech Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy, Pydantic
- **Frontend**: React + Vite + JavaScript (inline CSS)
- **Database**: PostgreSQL, Redis, Pinecone
- **AI/ML**: OpenAI GPT-4, Whisper, spaCy, Transformers
- **Infrastructure**: Docker, Docker Compose, Nginx
- **Testing**: PyTest, Jest, React Testing Library

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- Node.js 18+

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd talentsync
   ```

2. **Configure environment variables**
   ```bash
   # Copy environment examples for each service
   cp services/user-service/.env.example services/user-service/.env
   cp services/interview-service/.env.example services/interview-service/.env
   # ... repeat for all services
   ```

3. **Start the services**
   ```bash
   docker-compose -f infra/docker-compose.yml up -d
   ```

4. **Verify services are running**
   ```bash
   # Check service health
   curl http://localhost:8001/health  # User Service
   curl http://localhost:8002/health  # Interview Service
   # ... check other services
   ```

## 📁 Project Structure

```
talentsync/
├── services/                 # Microservices
│   ├── user-service/        # Authentication & profiles
│   ├── interview-service/   # Interview orchestration
│   ├── resume-service/      # Resume parsing
│   ├── media-service/       # Audio/video handling
│   ├── transcription-service/ # Speech-to-text
│   ├── feedback-service/    # Performance analytics
│   └── admin-service/       # Administrative functions
├── frontend/                # React frontend application
├── infra/                   # Infrastructure configurations
│   ├── docker-compose.yml   # Development environment
│   └── nginx.conf          # API Gateway configuration
└── docs/                    # Project documentation
```

## 🔧 Service Details

### User Service
- JWT-based authentication
- User profile management
- Role-based access control

### Interview Service
- Module and question management
- Session lifecycle orchestration
- RAG-based question generation

### Resume Service
- PDF/document parsing
- NLP-based skill extraction
- Resume-driven question generation

### Media Service
- WebRTC signaling
- Audio/video capture
- Real-time streaming

### Transcription Service
- Hybrid STT (Whisper + AssemblyAI)
- Speaker diarization
- Timestamped transcripts

### Feedback Service
- Multi-dimensional scoring
- Semantic similarity analysis
- AI-generated feedback reports

### Admin Service
- System analytics
- User management
- Content moderation

## 🧪 Testing

Run tests for all services:
```bash
# Backend tests
cd services/user-service && python -m pytest
cd services/interview-service && python -m pytest
# ... repeat for all services

# Frontend tests
cd frontend && npm test
```

## 📊 Monitoring

- **Health Checks**: Each service exposes `/health` endpoint
- **Metrics**: Prometheus metrics at `/metrics`
- **Logs**: Centralized logging with structured format

## 🔒 Security

- JWT-based authentication
- Input validation with Pydantic
- Rate limiting
- CORS configuration
- Secret management via environment variables

## 📈 Scalability

- Microservices architecture
- Async/await patterns
- Database connection pooling
- Redis caching
- Horizontal scaling ready

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Follow coding conventions in `/docs/talent_sync_coding_conventions.md`
4. Add tests for new features
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support, please contact the TalentSync team or create an issue in the repository.

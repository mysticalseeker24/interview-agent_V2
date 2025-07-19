# TalentSync Interview Service

A high-performance AI-powered interview simulation service that provides dynamic, adaptive questioning using RAG (Retrieval-Augmented Generation) and OpenAI's o4-mini model.

## 🚀 Features

### Core Capabilities
- **Dynamic Follow-up Generation**: AI-powered contextual questions based on candidate responses
- **Confidence-Based Question Selection**: Multi-tier strategy for optimal question quality
- **Vector Search**: Pinecone-powered semantic question matching
- **Session Management**: Redis-backed interview session orchestration
- **Domain-Specific Interviews**: Support for 7 specialized domains
- **Performance Optimization**: Caching, circuit breakers, and async processing

### Confidence-Based Follow-up System

The service implements a sophisticated **confidence-based question selection strategy** that ensures interview continuity regardless of vector search quality:

#### **Confidence Assessment Process**
- **Multi-Factor Scoring**: Combines similarity scores, domain matching, question length, and type preferences
- **Quality Validation**: Ensures questions meet technical and conversational standards
- **Performance Tracking**: Real-time monitoring of generation methods and confidence levels

#### **Generation Strategy Selection**
| Confidence Range | Strategy | Method | Description |
|-----------------|----------|--------|-------------|
| **0.7 - 1.0** | `high_confidence_llm` | LLM Refinement | Refine top vector candidates with o4-mini |
| **0.4 - 0.69** | `low_confidence_llm` | Contextual Generation | Generate new question based on answer context |
| **0.2 - 0.39** | `fallback_rag` | Best RAG Candidate | Use the best available vector search result |
| **0.0 - 0.19** | `domain_fallback` | Domain-Specific | Use pre-defined domain questions |

#### **Fallback Mechanisms**
- **Contextual Generation**: When confidence is medium, generates questions based on answer content
- **Domain Fallbacks**: Pre-defined questions for each domain and difficulty level
- **Ultimate Fallback**: Generic questions to maintain interview flow

## 🏗️ Architecture

### Service Components
- **Follow-up Service**: Confidence-based question generation with multiple strategies
- **Pinecone Service**: Vector database integration with circuit breaker pattern
- **Session Service**: Redis-backed session management with TTL
- **Auth Integration**: Supabase authentication with JWT validation

### Data Flow
```
1. User provides answer
   ↓
2. Generate embedding (50ms)
   ↓
3. Vector search in Pinecone (100ms)
   ↓
4. Calculate confidence scores
   ↓
5. Determine generation strategy:
   ├── High confidence (≥0.7): LLM refinement
   ├── Medium confidence (0.4-0.69): Contextual generation
   ├── Low confidence (0.2-0.39): Best RAG candidate
   └── Very low confidence (<0.2): Domain fallback
   ↓
6. Generate follow-up question
   ↓
7. Cache result with confidence score
   ↓
8. Return question to frontend
```

## 🎯 Supported Domains

The service supports **7 specialized interview domains**:

| Domain | Description | Key Topics | Difficulty Levels |
|--------|-------------|------------|-------------------|
| **DSA** | Data Structures & Algorithms | Arrays, Trees, Graphs, Dynamic Programming | Easy, Medium, Hard |
| **DevOps** | DevOps & Infrastructure | CI/CD, Docker, Kubernetes, Cloud Platforms | Easy, Medium, Hard |
| **AI Engineering** | AI Engineering | MLOps, Model Deployment, AI Infrastructure | Medium, Hard |
| **Machine Learning** | Machine Learning | Supervised/Unsupervised Learning, Deep Learning | Easy, Medium, Hard |
| **Data Science** | Data Science | Data Analysis, Statistics, Visualization | Easy, Medium, Hard |
| **Software Engineering** | Software Engineering | System Design, Architecture, Best Practices | Easy, Medium, Hard |
| **Resume-Based** | Resume-Based Interview | Experience Analysis, Skill Assessment | Medium |

## 🔧 Configuration

### Environment Variables
```env
# Service Configuration
APP_NAME=TalentSync Interview Service
APP_VERSION=1.0.0
DEBUG=false
PORT=8006

# Performance & Latency Configuration
REQUEST_TIMEOUT=1.0
FOLLOWUP_GENERATION_TIMEOUT=0.2
MAX_FOLLOWUP_GENERATION_TIME=0.5
CACHE_TTL=600
SESSION_TTL=3600

# Pinecone Vector Database Configuration
PINECONE_API_KEY=your-pinecone-api-key-here
PINECONE_ENV=us-west1-gcp
PINECONE_INDEX_NAME=questions-embeddings

# OpenAI Configuration for o4-mini
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_CHAT_MODEL=o4-mini
OPENAI_MAX_TOKENS=300
OPENAI_TEMPERATURE=0.1
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key-here

# Redis Configuration for Session Storage
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=20
REDIS_CONNECT_TIMEOUT=0.1

# External Service URLs
RESUME_SERVICE_URL=http://localhost:8004
MEDIA_SERVICE_URL=http://localhost:8002
TRANSCRIPTION_SERVICE_URL=http://localhost:8005
FEEDBACK_SERVICE_URL=http://localhost:8010

# Dataset Configuration
DATASET_PATH=../../data
SUPPORTED_DOMAINS=["dsa", "devops", "ai-engineering", "machine-learning", "data-science", "software-engineering", "resume-based"]
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Redis server
- Pinecone account and API key
- OpenAI API key
- Supabase project

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd talentsync/services/interview-service

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp env.example .env
# Edit .env with your API keys

# Run the service
uvicorn app.main:app --host 0.0.0.0 --port 8006 --reload
```

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d interview-service
```

## 📡 API Endpoints

### Follow-up Generation
```http
POST /api/v1/followup/generate
Content-Type: application/json

{
  "answer_text": "I implemented a binary search tree with O(log n) complexity",
  "domain": "dsa",
  "difficulty": "medium",
  "use_llm": true,
  "max_candidates": 5
}
```

### Session Management
```http
POST /api/v1/sessions/
GET /api/v1/sessions/{session_id}
PUT /api/v1/sessions/{session_id}
GET /api/v1/sessions/{session_id}/next-question
```

### Vector Search
```http
POST /api/v1/search/vector
GET /api/v1/search/similar/{question_id}
POST /api/v1/search/embedding
```

### Health & Monitoring
```http
GET /health
GET /metrics
GET /api/v1/health/detailed
```

## 🔍 Performance Monitoring

### Metrics Available
- **Generation Times**: Average, P95, P99 response times
- **Cache Performance**: Hit rates and efficiency
- **Confidence Distribution**: Distribution of confidence scores
- **Strategy Usage**: Frequency of each generation method
- **Error Rates**: Failure rates and error types

### Health Checks
- **Service Health**: Overall service status
- **Dependency Health**: Pinecone, Redis, OpenAI connectivity
- **Performance Health**: Response time monitoring
- **Circuit Breaker Status**: External service health

## 🧪 Testing

### Test Follow-up Generation
```bash
# Test the confidence-based system
curl -X POST "http://localhost:8006/api/v1/followup/test" \
  -H "Authorization: Bearer your-token"
```

### Test Vector Search
```bash
# Test semantic search capabilities
curl -X POST "http://localhost:8006/api/v1/search/test" \
  -H "Authorization: Bearer your-token"
```

## 🔒 Security

### Authentication
- **Supabase Auth**: JWT token validation
- **Role-based Access**: User and admin roles
- **API Key Management**: Secure external service integration

### Data Protection
- **Input Validation**: Pydantic schema validation
- **Rate Limiting**: Request throttling
- **Circuit Breakers**: External service protection

## 📊 Performance Benchmarks

### Target Metrics
- **API Response Time**: < 200ms for follow-up generation
- **Vector Search**: < 100ms for semantic queries
- **Session Operations**: < 50ms for Redis operations
- **Concurrent Users**: 1000+ simultaneous interviews
- **Throughput**: 1000+ RPS with Uvicorn workers

### Optimization Features
- **Async Processing**: Non-blocking I/O operations
- **Connection Pooling**: Optimized database connections
- **Caching Strategy**: Multi-level caching for performance
- **Circuit Breakers**: Resilience against external failures

## 🔄 Integration

### Frontend Integration
The service integrates seamlessly with the TalentSync frontend:
- **Real-time Questions**: WebSocket-based question delivery
- **Session Management**: Persistent interview sessions
- **Progress Tracking**: Real-time interview progress updates

### External Services
- **Resume Service**: Resume-based question generation
- **Transcription Service**: Audio processing integration
- **Media Service**: File management and storage
- **Feedback Service**: Post-interview analysis

## 🚀 Future Enhancements

### Planned Features
- **Multi-language Support**: International interview capabilities
- **Advanced Analytics**: Predictive performance modeling
- **Employer Portal**: Recruiter dashboard integration
- **Mobile Support**: Native mobile applications

### Performance Improvements
- **Global Vector Index**: Sharded Pinecone indices
- **Advanced Caching**: Redis cluster for high availability
- **Auto-scaling**: Kubernetes-based scaling
- **Real-time Monitoring**: Advanced observability

## 📝 License

This project is part of the TalentSync platform. See the main repository for licensing information.

## 🤝 Contributing

Please refer to the main TalentSync repository for contribution guidelines and development setup instructions. 
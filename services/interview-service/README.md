# TalentSync Interview Service

A high-performance, AI-powered interview service that generates contextual follow-up questions based on candidate responses using advanced RAG (Retrieval-Augmented Generation) and LLM technologies.

## 🚀 Features

- **Intelligent Follow-up Generation**: Context-aware follow-up questions using OpenAI's o4-mini model
- **Vector Search**: Fast semantic search using Pinecone vector database
- **Resume-Based Interviewing**: Generate questions based on candidate resume content
- **Session Management**: Complete interview session lifecycle management
- **Performance Optimized**: Circuit breakers, caching, and async operations
- **Health Monitoring**: Comprehensive health checks and performance metrics
- **Scalable Architecture**: Microservice-ready with Supabase backend

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │  Interview       │    │   Pinecone      │
│   (React/Next)  │◄──►│  Service         │◄──►│   Vector DB     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   Supabase       │
                       │   PostgreSQL     │
                       └──────────────────┘
```

## 🛠️ Technology Stack

- **Backend**: FastAPI (Python 3.11+)
- **Database**: Supabase (PostgreSQL)
- **Vector Database**: Pinecone
- **AI Models**: OpenAI o4-mini, text-embedding-ada-002
- **Caching**: In-memory LRU cache with TTL
- **Monitoring**: Built-in health checks and performance metrics

## 📋 Prerequisites

- Python 3.11 or higher
- Pinecone account and API key
- OpenAI API key
- Supabase project and credentials
- Node.js 18+ (for frontend)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd talentsync/services/interview-service
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file based on `env.example`:

```bash
cp env.example .env
```

Configure the following environment variables:

```env
# Pinecone Configuration
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENV=us-west1-gcp
PINECONE_INDEX_NAME=questions-embeddings

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key
OPENAI_CHAT_MODEL=o4-mini
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key
```

### 4. Database Setup

Run the Supabase migration:

```bash
python run_supabase_migration.py
```

### 5. Upload Datasets (Optional)

Upload interview questions to Pinecone:

```bash
python upload_datasets_to_pinecone.py
```

### 6. Start the Service

```bash
python start_service.py
```

Or run directly:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8006 --reload
```

## 🧪 Testing

### Run Unit Tests

```bash
python test_interview_service.py
```

### Run Live Testing

Comprehensive end-to-end testing with real resume data:

```bash
# Test with default resume
python live_testing.py --verbose

# Test with specific resume
python live_testing.py --resume-id "Alice Smith" --verbose

# Test specific domain
python live_testing.py --domain "machine-learning" --verbose
```

### Test Results

The service should pass all tests:
- ✅ Resume-based question generation
- ✅ Vector search functionality
- ✅ Session management
- ✅ Performance under load
- ✅ Health checks

## 📚 API Endpoints

### Core Endpoints

- `POST /followup/generate` - Generate follow-up questions
- `POST /sessions/` - Create interview session
- `GET /sessions/{session_id}` - Get session details
- `POST /vector/search` - Semantic search for questions
- `GET /health` - Service health check

### Health & Monitoring

- `GET /health/` - Basic health check
- `GET /health/detailed` - Comprehensive health status
- `GET /metrics` - Performance metrics
- `GET /health/ping` - Simple ping endpoint

## 🔧 Configuration

### Performance Settings

```env
# Request timeouts
REQUEST_TIMEOUT=5.0
FOLLOWUP_GENERATION_TIMEOUT=3.0
MAX_FOLLOWUP_GENERATION_TIME=5.0

# Cache configuration
CACHE_TTL=600
MAX_CACHE_SIZE=500

# Circuit breaker
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60
```

### Supported Domains

- `dsa` - Data Structures & Algorithms
- `devops` - DevOps & Infrastructure
- `ai-engineering` - AI & Machine Learning
- `machine-learning` - ML & Data Science
- `data-science` - Data Science & Analytics
- `software-engineering` - Software Development
- `resume-based` - Resume-specific questions

## 🐳 Docker Deployment

### Build Image

```bash
docker build -t talentsync-interview-service .
```

### Run Container

```bash
docker run -p 8006:8006 \
  -e PINECONE_API_KEY=your-key \
  -e OPENAI_API_KEY=your-key \
  -e SUPABASE_URL=your-url \
  talentsync-interview-service
```

### Docker Compose

```yaml
version: '3.8'
services:
  interview-service:
    build: .
    ports:
      - "8006:8006"
    environment:
      - PINECONE_API_KEY=${PINECONE_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - SUPABASE_URL=${SUPABASE_URL}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8006/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## 📊 Performance Metrics

The service provides comprehensive performance monitoring:

- **Response Times**: Average, P95, P99 response times
- **Cache Hit Rates**: Follow-up question cache efficiency
- **Error Rates**: Success/failure ratios
- **Throughput**: Requests per second
- **Resource Usage**: Memory and CPU utilization

## 🔍 Troubleshooting

### Common Issues

1. **Pinecone Connection Timeout**
   - Check API key and environment
   - Verify index exists and is accessible
   - Check network connectivity

2. **OpenAI API Errors**
   - Verify API key is valid
   - Check rate limits and quotas
   - Ensure model names are correct

3. **Supabase Connection Issues**
   - Verify URL and credentials
   - Check database permissions
   - Ensure tables are created

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
python start_service.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

### Code Standards

- Follow PEP 8 style guidelines
- Add type hints to all functions
- Include docstrings for public methods
- Write comprehensive tests
- Use async/await for I/O operations

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:

- Create an issue in the repository
- Check the troubleshooting section
- Review the API documentation
- Contact the development team

## 🗺️ Roadmap

- [ ] Frontend React application
- [ ] Real-time interview sessions
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] Integration with HR systems
- [ ] Mobile application
- [ ] Advanced AI models support

---

**Built with ❤️ by the TalentSync Team** 
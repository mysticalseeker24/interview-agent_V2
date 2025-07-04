# TalentSync Interview Service

The Interview Service is the core orchestration service for the TalentSync platform, responsible for managing interview modules, questions, sessions, and the complete RAG (Retrieval-Augmented Generation) pipeline for semantic question retrieval and follow-up generation.

## Features

### Core Functionality
- **Module Management**: Create and manage interview modules by domain (Software Engineering, ML, DSA, etc.)
- **Question Management**: CRUD operations for interview questions with difficulty levels and categories
- **Session Orchestration**: End-to-end interview session management
- **Vector Search**: Semantic question retrieval using Pinecone vector database
- **RAG Pipeline**: Context-aware follow-up question generation
- **Dataset Import**: Bulk import of domain-specific question datasets
- **Resume-Driven Questions**: Dynamic question generation based on candidate resumes

### Advanced Capabilities
- **Continuous Sync**: Real-time synchronization of questions to vector database
- **Semantic Similarity**: Find related questions using vector embeddings
- **Follow-up Intelligence**: AI-powered follow-up question recommendations
- **Multi-Domain Support**: Software Engineering, Machine Learning, Data Structures, Resume-based
- **Hybrid Storage**: PostgreSQL for relational data + Pinecone for vector search
- **Background Processing**: Non-blocking import and sync operations

## Architecture

### Technology Stack
- **Backend**: FastAPI with async support
- **Database**: PostgreSQL 13+ (hybrid relational/vector store)
- **Vector DB**: Pinecone for embeddings and semantic search
- **Embeddings**: OpenAI text-embedding-ada-002 model
- **Queue**: Background tasks for import/sync operations
- **API**: RESTful endpoints with OpenAPI documentation

### Service Integration
- **User Service**: Authentication and user management
- **Resume Service**: Resume parsing and skill extraction  
- **Transcription Service**: Interview recording and analysis
- **Frontend**: React-based interview interface

## API Endpoints

### Module Management
- `GET /api/v1/modules` - List all interview modules
- `POST /api/v1/modules` - Create new module
- `GET /api/v1/modules/{module_id}` - Get module details
- `PUT /api/v1/modules/{module_id}` - Update module
- `DELETE /api/v1/modules/{module_id}` - Delete module
- `GET /api/v1/modules/{module_id}/questions` - Get module questions

### Question Management
- `GET /api/v1/questions` - List questions with filtering
- `POST /api/v1/questions` - Create new question
- `GET /api/v1/questions/{question_id}` - Get question details
- `PUT /api/v1/questions/{question_id}` - Update question
- `DELETE /api/v1/questions/{question_id}` - Delete question

### Session Management
- `POST /api/v1/sessions` - Start new interview session
- `GET /api/v1/sessions/{session_id}` - Get session details
- `PUT /api/v1/sessions/{session_id}` - Update session
- `POST /api/v1/sessions/{session_id}/responses` - Submit question response
- `GET /api/v1/sessions/{session_id}/next-question` - Get next question

### Vector Operations
- `POST /api/v1/vectors/sync/question` - Sync single question to Pinecone
- `POST /api/v1/vectors/sync/questions/batch` - Batch sync questions
- `POST /api/v1/vectors/sync/questions/all` - Sync all questions
- `GET /api/v1/vectors/search` - Semantic search for questions
- `GET /api/v1/vectors/followups` - Get follow-up questions based on answer

### Dataset Management
- `POST /api/v1/datasets/import/file` - Import questions from uploaded file
- `POST /api/v1/datasets/import/json` - Import questions from JSON payload
- `POST /api/v1/datasets/import/path` - Import questions from file path
- `POST /api/v1/datasets/import/all` - Import all datasets from data directory

### Health & Monitoring
- `GET /api/v1/health` - Service health check
- `GET /api/v1/health/database` - Database connectivity check
- `GET /api/v1/health/vector` - Vector database health
- `GET /metrics` - Prometheus metrics

## Environment Variables

```bash
# Database Configuration
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/talentsync
ALEMBIC_DATABASE_URL=postgresql://user:password@localhost:5432/talentsync

# Vector Database
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_INDEX_NAME=questions-embeddings

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key
EMBEDDING_MODEL=text-embedding-ada-002

# Service Configuration
PORT=8002
DEBUG=false
LOG_LEVEL=INFO

# CORS & Security
ALLOWED_ORIGINS=["http://localhost:3000"]
ALLOWED_HOSTS=["localhost", "127.0.0.1"]

# Background Tasks
MAX_WORKERS=4
SYNC_BATCH_SIZE=100
```

## Database Schema

### Core Tables
- **`modules`**: Interview modules with categories and difficulty levels
- **`questions`**: Interview questions with metadata and embeddings info
- **`sessions`**: Interview session state and progress
- **`responses`**: Candidate responses to questions
- **`question_analytics`**: Performance metrics and usage statistics

### Vector Integration
- **`last_synced`**: Timestamp tracking for Pinecone synchronization
- **`domain`**: Domain classification for vector search
- **`embedding_version`**: Version tracking for embedding updates

## RAG Pipeline

### 1. Question Embedding Generation
```python
# Generate embeddings for new questions
embedding = openai.embeddings.create(
    input=question_text,
    model="text-embedding-ada-002"
)
```

### 2. Vector Storage
```python
# Store in Pinecone with metadata
pinecone_index.upsert([
    {
        "id": str(question_id),
        "values": embedding,
        "metadata": {
            "domain": domain,
            "difficulty": difficulty,
            "type": question_type
        }
    }
])
```

### 3. Semantic Search
```python
# Find similar questions
results = pinecone_index.query(
    vector=query_embedding,
    filter={"domain": domain},
    top_k=5,
    include_metadata=True
)
```

### 4. Follow-up Generation
```python
# Generate contextual follow-ups
follow_ups = generate_followups(
    candidate_answer=answer,
    original_question=question,
    similar_questions=search_results
)
```

## Dataset Integration

### Supported Dataset Formats
The service supports importing questions from JSON files with the following structure:

```json
[
  {
    "id": "unique-identifier",
    "text": "Question text",
    "type": "conceptual|behavioral|technical|coding",
    "difficulty": "easy|medium|hard",
    "follow_up_templates": [
      "Follow-up question template 1",
      "Follow-up question template 2"
    ],
    "ideal_answer_summary": "Description of ideal answer",
    "tags": ["tag1", "tag2"],
    "domain": "Software Engineering"
  }
]
```

### Available Datasets
- **SWE_dataset.json**: Software Engineering concepts and system design
- **ML_dataset.json**: Machine Learning algorithms and techniques
- **DSA_dataset.json**: Data Structures and Algorithms problems
- **Resume_dataset.json**: Resume-driven behavioral questions
- **Resumes_dataset.json**: Sample resumes for testing

### Import Process
1. **File Validation**: Verify JSON format and required fields
2. **Module Association**: Map questions to appropriate modules
3. **Data Transformation**: Convert to internal schema format
4. **Database Storage**: Persist questions with metadata
5. **Vector Sync**: Generate embeddings and sync to Pinecone
6. **Background Processing**: Handle large imports asynchronously

### Import Scripts & Methods

#### 1. Direct Import Script
```bash
# Import all datasets using SQLAlchemy directly
cd talentsync/services/interview-service
python app/scripts/import_datasets.py
```

#### 2. API-based Import Script  
```bash
# Import datasets via REST API endpoints
cd talentsync/services/interview-service
python import_datasets_via_api.py
```

#### 3. REST API Import Endpoints

**Import from File Upload:**
```http
POST /api/v1/datasets/import/file
Content-Type: multipart/form-data

# Upload JSON file with questions
```

**Import from JSON Payload:**
```http
POST /api/v1/datasets/import/json
Content-Type: application/json

{
  "questions": [...],
  "module_id": 1
}
```

**Import from File Path:**
```http
POST /api/v1/datasets/import/path?file_path=/path/to/dataset.json
```

**Import All Datasets:**
```http
POST /api/v1/datasets/import/all
```

### Dataset Validation & Processing

#### Validation Rules
- Required fields: `text` (question content)
- Optional fields: `difficulty`, `type`, `domain`, `tags`
- JSON array format validation
- File size limits (configurable)
- Encoding validation (UTF-8)

#### Processing Pipeline
1. **File Validation**: Check format and size
2. **JSON Parsing**: Validate structure and required fields  
3. **Data Transformation**: Convert to internal schema
4. **Module Association**: Map to appropriate interview modules
5. **Database Storage**: Persist with metadata
6. **Vector Sync**: Generate embeddings and sync to Pinecone
7. **Background Processing**: Handle large imports asynchronously

#### Error Handling
- Invalid JSON format errors
- Missing required fields warnings
- Duplicate question detection
- Import progress tracking
- Rollback on critical failures

### Sync Status Monitoring

#### Health Check Endpoints
```bash
# Service health
curl http://localhost:8002/api/v1/health

# Database connectivity
curl http://localhost:8002/api/v1/health/database

# Vector database status
curl http://localhost:8002/api/v1/health/vector
```

#### Sync Status Tracking
- Individual question sync timestamps
- Batch sync progress monitoring
- Error rate tracking and alerting
- Performance metrics collection

## Performance & Scalability

### Optimization Features
- **Async Operations**: Non-blocking database and API calls
- **Connection Pooling**: Efficient database connection management
- **Background Tasks**: Queue-based processing for heavy operations
- **Caching**: Redis-based caching for frequently accessed data
- **Batch Processing**: Efficient bulk operations for imports and sync

### Monitoring
- **Health Checks**: Comprehensive service and dependency monitoring
- **Metrics**: Prometheus metrics for performance tracking
- **Logging**: Structured logging with correlation IDs
- **Error Tracking**: Detailed error reporting and stack traces

## Getting Started

### Prerequisites
- Python 3.9+
- PostgreSQL 13+
- Pinecone account and API key
- OpenAI API key

### Installation
1. **Clone and Navigate**:
   ```bash
   cd talentsync/services/interview-service
   ```

2. **Install Dependencies**:
   ```bash
   pip install -e .
   ```

3. **Set Environment Variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run Database Migrations**:
   ```bash
   alembic upgrade head
   ```

5. **Import Datasets** (Optional):
   ```bash
   python app/scripts/import_datasets.py
   ```

6. **Start Service**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8002
   ```

### Docker Deployment
```bash
# Build image
docker build -t talentsync-interview-service .

# Run container
docker run -p 8002:8002 \
  -e DATABASE_URL=postgresql+asyncpg://... \
  -e PINECONE_API_KEY=... \
  -e OPENAI_API_KEY=... \
  talentsync-interview-service
```

## Development

### Project Structure
```
app/
├── core/           # Core configuration and utilities
├── models/         # SQLAlchemy database models
├── schemas/        # Pydantic request/response models
├── routers/        # FastAPI route handlers
├── services/       # Business logic and external integrations
├── db/            # Database migrations and utilities
└── scripts/       # Utility scripts for data management
```

### Code Quality
- **Type Hints**: Full typing support with mypy
- **Linting**: Black, isort, and flake8 for code formatting
- **Testing**: pytest with async support and fixtures
- **Documentation**: Comprehensive docstrings and API docs

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_vectors.py -v
```

## API Documentation

- **Swagger UI**: Available at `/docs` when service is running
- **ReDoc**: Available at `/redoc` for alternative documentation view
- **OpenAPI JSON**: Available at `/openapi.json` for API specifications

## Troubleshooting

### Common Issues
1. **Database Connection**: Verify PostgreSQL is running and accessible
2. **Pinecone Errors**: Check API key and index configuration
3. **OpenAI Limits**: Monitor API usage and rate limits
4. **Import Failures**: Validate JSON format and file permissions

### Debug Mode
Enable debug mode by setting `DEBUG=true` in environment variables for detailed logging and error traces.

### Health Checks
Use the health check endpoints to verify service status:
```bash
curl http://localhost:8002/api/v1/health
```

## Contributing

1. Follow the coding conventions documented in `docs/talent_sync_coding_conventions.md`
2. Add tests for new features
3. Update documentation for API changes
4. Use meaningful commit messages

## REST API Implementation Details

### Vector Sync Strategy

The service uses a REST API-based approach for vector synchronization instead of message queues for simplified deployment:

1. **Database Triggers**: PostgreSQL triggers mark questions needing synchronization
2. **REST Endpoints**: Dedicated endpoints for sync operations  
3. **Background Tasks**: FastAPI background tasks for non-blocking operations
4. **Periodic Sync**: Optional scheduled sync via endpoint calls

### Sync Endpoint Examples

#### 1. Single Question Sync
```http
POST /api/v1/vectors/sync/question
Content-Type: application/json

{
  "id": 123,
  "text": "Tell me about your experience with Python.",
  "domain": "Software Engineering", 
  "type": "technical",
  "difficulty": "medium"
}
```

Response:
```json
{
  "status": "success",
  "message": "Question 123 sync started in background"
}
```

#### 2. Batch Question Sync
```http
POST /api/v1/vectors/sync/questions/batch
Content-Type: application/json

{
  "questions": [
    {
      "id": 123,
      "text": "Tell me about your experience with Python.",
      "domain": "Software Engineering",
      "type": "technical", 
      "difficulty": "medium"
    },
    {
      "id": 124,
      "text": "How do you handle difficult team situations?",
      "domain": "Software Engineering",
      "type": "behavioral",
      "difficulty": "hard"
    }
  ]
}
```

#### 3. Semantic Search
```http
GET /api/v1/vectors/search?query=python%20programming&domain=Software%20Engineering&top_k=5
```

Response:
```json
{
  "results": [
    {
      "id": 123,
      "text": "Tell me about your experience with Python.",
      "similarity_score": 0.95,
      "metadata": {
        "domain": "Software Engineering",
        "difficulty": "medium"
      }
    }
  ]
}
```

#### 4. Follow-up Question Retrieval
```http
GET /api/v1/vectors/followups?answer=I%20have%20been%20using%20Python%20for%20five%20years&asked=1,2,3
```

### Implementation Architecture

#### Continuous Sync Pipeline
1. **Question Creation/Update**: Triggers background sync task
2. **Embedding Generation**: OpenAI text-embedding-ada-002 model
3. **Vector Upsert**: Store in Pinecone with metadata
4. **Status Tracking**: Update `last_synced` timestamp

#### Background Task Processing
```python
@router.post("/sync/question")
async def sync_question(question: QuestionSync, background_tasks: BackgroundTasks):
    background_tasks.add_task(
        embedding_service.sync_question_on_create,
        question_data=question.dict()
    )
    return {"status": "success", "message": "Sync started"}
```

#### Error Handling & Retry Logic
- Exponential backoff for failed sync operations
- Dead letter queue for persistent failures  
- Health checks for vector database connectivity
- Comprehensive logging for debugging

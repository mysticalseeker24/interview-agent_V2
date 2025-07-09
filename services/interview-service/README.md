# TalentSync Interview Service

The Interview Service is the core orchestration service for the TalentSync platform, responsible for managing interview modules, questions, sessions, dynamic follow-up generation, and the complete RAG (Retrieval-Augmented Generation) pipeline.

## Features

### Core Functionality
- **Module Management**: Create and manage interview modules by domain (Software Engineering, ML, DSA, etc.)
- **Question Management**: CRUD operations for interview questions with difficulty levels and categories
- **Session Orchestration**: End-to-end interview session management with response tracking
- **Vector Search**: Semantic question retrieval using Pinecone vector database
- **RAG Pipeline**: Context-aware follow-up question generation
- **Dataset Import**: Bulk import of domain-specific question datasets
- **Resume-Driven Questions**: Dynamic question generation based on candidate resumes

### Advanced AI-Powered Services

#### 🚀 **Dynamic Follow-Up Generation**
- **o4-mini Integration**: Advanced reasoning model for contextual follow-ups
- **Real-time Analysis**: Analyzes candidate responses for deeper exploration
- **Anti-hallucination**: Grounded responses using only actual candidate mentions
- **Multi-source Generation**: Combines LLM generation with RAG-based retrieval
- **Quality Assurance**: Automated validation and fallback mechanisms

### Technical Capabilities
- **Continuous Sync**: Real-time synchronization of questions to vector database
- **Semantic Similarity**: Find related questions using vector embeddings
- **Question Tracking**: Prevent duplicate questions within sessions
- **Multi-Domain Support**: Software Engineering, Machine Learning, Data Structures, Resume-based
- **Hybrid Storage**: SQLite for relational data + Pinecone for vector search
- **Background Processing**: Celery workers for non-blocking operations
- **Schema Management**: Alembic migrations for database versioning

## Architecture

### Technology Stack
- **Backend**: FastAPI with async support
- **Database**: SQLite (default and only supported for this service)
- **Vector DB**: Pinecone for embeddings and semantic search
- **Task Queue**: Celery with Redis broker for background processing
- **AI Models**: 
  - OpenAI text-embedding-ada-002 for embeddings
  - o4-mini for follow-up generation
  - sentence-transformers for semantic similarity analysis
- **API**: RESTful endpoints with OpenAPI documentation

### Service Integration
- **User Service**: Authentication and user management
- **Resume Service**: Resume parsing and skill extraction  
- **Transcription Service**: Interview recording and analysis
- **Media Service**: Audio/video processing for interviews
- **Feedback Service**: Handles all feedback and scoring operations
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

### Dynamic Follow-Up Generation
- `POST /api/v1/followup/generate` - Generate context-aware follow-up questions using o4-mini
- `GET /api/v1/followup/history/{session_id}` - Get follow-up question history for session
- `GET /api/v1/followup/health` - Follow-up service health check

### Post-Interview Feedback
- `POST /api/v1/feedback/generate` - Generate comprehensive feedback report (async)
- `GET /api/v1/feedback/status/{task_id}` - Check feedback generation progress
- `GET /api/v1/feedback/report/{session_id}` - Retrieve completed feedback report
- `GET /api/v1/feedback/scores/{session_id}` - Get detailed scoring breakdown
- `DELETE /api/v1/feedback/report/{session_id}` - Delete feedback report

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
DATABASE_URL=sqlite+aiosqlite:///./talentsync.db

# Vector Database
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_INDEX_NAME=questions-embeddings

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_CHAT_MODEL=o4-mini
OPENAI_MAX_TOKENS=1000
OPENAI_TEMPERATURE=0.1

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json

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
- **`responses`**: Candidate responses to questions with timestamps
- **`session_questions`**: Track questions asked per session (prevents duplicates)

### Feedback & Scoring System
- **`scores`**: Per-question scoring metrics (semantic similarity, fluency, depth)
- **`feedback_reports`**: Comprehensive AI-generated feedback with percentiles
- **`session_aggregates`**: Calculated session-level performance metrics

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

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- OpenAI API Key
- Pinecone API Key
- SQLite (default, no installation required)

### Setup Instructions

1. **Install Dependencies**
   ```powershell
   # From project root
   pip install -r requirements.txt
   
   # Download spaCy model
   python -m spacy download en_core_web_sm
   ```

2. **Test API Connections**
   ```powershell
   # Test Pinecone connection
   python -c "
   from pinecone import Pinecone
   import os
   from dotenv import load_dotenv
   
   load_dotenv('../../.env')
   pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
   print('✅ Pinecone connection successful!')
   print('Available indexes:', pc.list_indexes())
   "
   
   # Test OpenAI connection
   python -c "
   from openai import OpenAI
   import os
   from dotenv import load_dotenv
   
   load_dotenv('../../.env')
   client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
   print('✅ OpenAI connection successful!')
   "
   ```

3. **Start Interview Service**
   ```powershell
   # From interview-service directory
   cd services/interview-service
   uvicorn app.main:app --reload --port 8002
   ```

4. **Verify Service**
   - API Documentation: http://localhost:8002/docs
   - Health Check: http://localhost:8002/health

### Docker Deployment
```bash
# Build image
docker build -t talentsync-interview-service .

# Run container
docker run -p 8002:8002 \
  -e DATABASE_URL=sqlite+aiosqlite:///./talentsync.db \
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
1. **Database Connection**: Verify SQLite file permissions and path
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

1. **Database Triggers**: SQLite triggers mark questions needing synchronization
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

## Dynamic Follow-Up Generation Pipeline

### Overview
The Dynamic Follow-Up service combines RAG (Retrieval-Augmented Generation) with o4-mini to generate contextually relevant follow-up questions during interviews.

### Process Flow

#### 1. Candidate Answer Processing
```python
# Embed candidate's answer
answer_embedding = openai.embeddings.create(
    input=candidate_answer,
    model="text-embedding-ada-002"
)
```

#### 2. RAG-Based Question Retrieval
```python
# Search Pinecone for similar follow-up templates
similar_questions = pinecone_index.query(
    vector=answer_embedding.data[0].embedding,
    filter={"type": "follow-up", "domain": session_domain},
    top_k=5,
    include_metadata=True
)
```

#### 3. Duplicate Prevention
```python
# Exclude already asked questions
excluded_ids = session.get_asked_question_ids()
candidates = filter_out_asked_questions(similar_questions, excluded_ids)
```

#### 4. o4-mini Refinement (Optional)
```python
# Use o4-mini to generate dynamic follow-up
response = openai.chat.completions.create(
    model="o4-mini",
    messages=[
        {"role": "system", "content": "You are an expert interview assistant..."},
        {"role": "user", "content": f"Candidate answered: {answer}\nGenerate a precise follow-up..."}
    ]
)
```

#### 5. Question Tracking
```python
# Log the chosen question to prevent repeats
session_question = SessionQuestion(
    session_id=session_id,
    question_id=chosen_question_id,
    question_type="follow_up",
    source="llm" or "rag"
)
```

### When Dynamic Follow-Up Works with SQLite

The dynamic follow-up system requires the following database setup to function:

#### ✅ **Database Prerequisites**
1. **Questions Table**: Must contain follow-up type questions
2. **Session Questions Table**: Created and migrated (tracks asked questions)
3. **Sessions Table**: Active session with valid session_id
4. **Vector Sync**: Questions synced to Pinecone with embeddings

#### ✅ **Required Data Flow**
```sql
-- 1. Session must exist
SELECT * FROM sessions WHERE id = :session_id;

-- 2. Questions must be available
SELECT * FROM questions WHERE type = 'follow-up';

-- 3. Previous questions tracked
SELECT question_id FROM session_questions WHERE session_id = :session_id;

-- 4. Vector embeddings synced
-- (Verified via Pinecone index query)
```

#### ✅ **Operational Status**
The dynamic follow-up will work when:

- ✅ **SQLite is running** and accessible
- ✅ **Questions imported** into the database
- ✅ **Pinecone index exists** with question embeddings
- ✅ **Session is active** and session_id is valid
- ✅ **OpenAI API key** is configured for o4-mini
- ✅ **session_questions table** exists (for duplicate prevention)

#### 📋 **Testing Dynamic Follow-Up Readiness**
```bash
# Test database connectivity
python -c "from app.core.database import engine; print('DB OK')"

# Test Pinecone connectivity  
python -c "from app.services.pinecone_service import PineconeService; ps = PineconeService(); print('Pinecone OK')"

# Test OpenAI connectivity
python -c "from openai import OpenAI; client = OpenAI(); print('OpenAI OK')"

# Check if questions are synced
curl http://localhost:8002/api/v1/vectors/health
```

#### 🚀 **API Usage Example**
```bash
# Generate follow-up question
curl -X POST "http://localhost:8002/api/v1/followup/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": 123,
    "answer_text": "I have experience with React hooks and state management...",
    "use_llm": true,
    "max_candidates": 5
  }'

# Response
{
  "follow_up_question": "Can you walk me through how you would optimize a React component that re-renders frequently?",
  "source_ids": [456, 457, 458],
  "generation_method": "llm",
  "confidence_score": null
}
```

## Advanced AI Services

### 🚀 Dynamic Follow-Up Generation Service

The Dynamic Follow-Up Generation service leverages OpenAI's o4-mini model for intelligent, context-aware follow-up question generation during interviews.

#### Key Features
- **Real-time Analysis**: Analyzes candidate responses in real-time to identify areas for deeper exploration
- **Anti-hallucination**: Uses strict prompt engineering to ground responses in actual candidate mentions
- **Multi-source Generation**: Combines LLM-based generation with RAG-based retrieval
- **Quality Assurance**: Automated validation and fallback mechanisms for reliable questions

#### Technical Implementation

**Core Algorithm Flow:**
```python
async def generate_followup_question(session_id: int, answer_text: str, use_llm: bool = True):
    # 1. Extract key technical terms from candidate's answer
    key_terms = extract_key_terms(answer_text)
    
    # 2. Perform semantic search for related questions
    similar_questions = await vector_search(key_terms, domain=session.domain)
    
    # 3. Generate contextual follow-up using o4-mini
    if use_llm:
        prompt = create_reasoning_prompt(answer_text, similar_questions, key_terms)
        follow_up = await openai_client.chat.completions.create(
            model="o4-mini",
            messages=[{"role": "system", "content": system_prompt}, 
                     {"role": "user", "content": prompt}],
            temperature=0.1,  # Low for consistent reasoning
            max_tokens=300
        )
    
    # 4. Validate and clean the generated question
    validated_question = validate_and_clean_question(follow_up.content)
    
    # 5. Track in session to prevent duplicates
    await track_session_question(session_id, validated_question)
    
    return validated_question
```

**Anti-hallucination Strategy:**
- Explicit constraints in prompts: "Only reference concepts the candidate mentioned"
- Key term extraction limits model to grounded concepts
- Post-processing validation ensures question quality
- Fallback to RAG-based questions if LLM response is invalid

#### API Usage Examples

**Generate Follow-up Question:**
```bash
curl -X POST "http://localhost:8002/api/v1/followup/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": 123,
    "answer_text": "I implemented React hooks for state management and used useEffect for side effects...",
    "use_llm": true,
    "max_candidates": 5
  }'

# Response:
{
  "follow_up_question": "You mentioned using useEffect for side effects. Can you walk me through a specific scenario where you had to clean up resources in a useEffect hook?",
  "source_ids": [456, 457],
  "generation_method": "llm",
  "confidence_score": null
}
```

### 📊 Post-Interview Feedback System

The Feedback System provides comprehensive analysis and scoring of interview sessions using advanced NLP techniques and AI-generated narratives.

#### Key Features
- **Semantic Similarity Analysis**: Uses sentence-transformers to compare responses with ideal answers
- **Fluency Assessment**: Advanced NLP metrics for communication evaluation
- **Percentile Ranking**: Historical comparison with database of past performance
- **Comprehensive Scoring**: Per-question detailed metrics and session aggregates
- **AI Narrative Generation**: o4-mini powered detailed feedback reports

#### Scoring Methodology

**Per-Question Metrics:**
```python
class QuestionScore:
    semantic_similarity: float    # 0.0-1.0 (cosine similarity with ideal answer)
    fluency_score: float         # 0.0-1.0 (readability and coherence)
    depth_score: float           # 0.0-1.0 (technical depth and detail)
    confidence_level: float      # 0.0-1.0 (certainty in response)
    response_time: int           # Seconds taken to respond
```

**Session Aggregates:**
```python
class SessionMetrics:
    overall_score: float         # Weighted average of all question scores
    semantic_percentile: float   # Historical ranking (0-100)
    fluency_percentile: float    # Communication ranking (0-100)
    depth_percentile: float      # Technical depth ranking (0-100)
    consistency_score: float     # Variance across questions
    total_questions: int         # Number of questions answered
    total_duration: int          # Session duration in minutes
```

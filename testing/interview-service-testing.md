# Interview Service Testing Guide

## Overview
The Interview Service provides dynamic question generation, follow-up question creation, and RAG-based interview management using OpenAI and Pinecone for enhanced candidate evaluation.

## Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis 6+
- Valid API keys for OpenAI, Pinecone, and AssemblyAI

## Environment Setup

### 1. Environment Configuration

Create `.env` file in `services/interview-service/`:
```bash
# API Keys (Required)
OPENAI_API_KEY=your-openai-api-key-here
PINECONE_API_KEY=your-pinecone-api-key-here

# Database Configuration
DATABASE_URL=postgresql+asyncpg://talentsync:secret@localhost:5432/talentsync
REDIS_URL=redis://localhost:6379

# Service Configuration
INTERVIEW_SERVICE_PORT=8006
```

### 2. Dependencies Installation

```bash
# Navigate to interview service
cd services/interview-service

# Install dependencies
pip install -r requirements.txt

# Install spaCy English model for NLP
python -m spacy download en_core_web_sm
```

## Infrastructure Setup

### 1. Start PostgreSQL
```bash
# Start PostgreSQL with Docker
docker run --name talentsync-postgres -e POSTGRES_USER=talentsync -e POSTGRES_PASSWORD=secret -e POSTGRES_DB=talentsync -p 5432:5432 -d postgres:14

# Test PostgreSQL connection
docker exec -it talentsync-postgres psql -U talentsync -d talentsync -c "SELECT version();"
```

### 2. Start Redis
```bash
# Start Redis with Docker
docker run --name talentsync-redis -p 6379:6379 -d redis:6-alpine

# Test Redis connection
docker exec -it talentsync-redis redis-cli ping
```

### 3. Create Pinecone Index
```bash
python -c "
from pinecone import Pinecone, ServerlessSpec
import os
from dotenv import load_dotenv

load_dotenv()
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))

index_name = 'questions-embeddings'
if index_name not in [idx.name for idx in pc.list_indexes()]:
    pc.create_index(
        name=index_name,
        dimension=1536,  # OpenAI embedding dimension
        metric='cosine',
        spec=ServerlessSpec(cloud='aws', region='us-east-1')
    )
    print(f'Created Pinecone index: {index_name}')
else:
    print(f'Index {index_name} already exists')
"
```

## API Testing

### Start Interview Service
```bash
# Navigate to interview service directory
cd services/interview-service

# Start the service
uvicorn app.main:app --reload --port 8006
```

### Test Service Health
```bash
# Test health endpoint
curl http://localhost:8006/health

# Expected response:
# {"status": "healthy", "service": "interview-service", "timestamp": "..."}
```

### Test Dynamic Follow-Up Generation

```bash
# Test follow-up generation with RAG mode
curl -X POST "http://localhost:8006/api/v1/followup/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": 1,
    "answer_text": "I have experience with React hooks and Redux for state management",
    "use_llm": false,
    "max_candidates": 5
  }'

# Test follow-up generation with o4-mini refinement
curl -X POST "http://localhost:8006/api/v1/followup/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": 1, 
    "answer_text": "I implemented microservices using Node.js and Docker",
    "use_llm": true,
    "max_candidates": 3
  }'

# Get follow-up question history for a session
curl http://localhost:8006/api/v1/followup/history/1

# Check follow-up service health
curl http://localhost:8006/api/v1/followup/health
```

### Expected Dynamic Follow-Up Response
```json
{
  "follow_up_question": "Can you walk me through how you handled state management across multiple React components in a complex application?",
  "source_ids": [45, 67, 89],
  "generation_method": "llm",
  "confidence_score": null
}
```

## Dataset Loading

### Load Question Datasets
```bash
# Load datasets into PostgreSQL and sync to Pinecone
python import_datasets_via_api.py

# Test hybrid search functionality
python test_pinecone.py

# Test question retrieval
python test_dataset_import.py
```

## Testing Scripts

### Available Test Scripts
- `test_codebase.py` - Complete codebase validation
- `test_dataset_import.py` - Dataset loading and retrieval
- `test_dynamic_followup.py` - Follow-up question generation
- `test_feedback_integration.py` - Feedback system testing
- `test_pinecone.py` - Vector database operations

### Run All Tests
```bash
# Run comprehensive tests
python test_codebase.py
python test_dynamic_followup.py
python test_feedback_integration.py
```

## Service Status Verification

✅ **Dependencies**: Installed and working  
✅ **API Keys**: OpenAI and Pinecone tested successfully  
✅ **PostgreSQL**: Running and accessible  
✅ **Redis**: Running and accessible  
✅ **Pinecone Index**: Created successfully (`questions-embeddings`)  
✅ **Interview Service**: Successfully started on port 8006  
✅ **RAG Pipeline**: Service running with dataset loading  
✅ **Dynamic Follow-Up Generation**: Working with o4-mini  

## Troubleshooting

### Common Issues

1. **Pinecone Import Error**: 
   ```bash
   pip uninstall pinecone-client -y
   pip install pinecone
   ```

2. **Database Connection Error**: 
   - Ensure PostgreSQL is running
   - Verify credentials in `.env` file

3. **API Key Error**: 
   - Check API keys are set in `.env`
   - Verify keys are valid and active

4. **Port Already in Use**:
   ```bash
   # Kill existing process
   lsof -ti:8006 | xargs kill -9
   ```

## Performance Metrics

- **Startup Time**: ~3-5 seconds
- **Question Generation**: ~1-2 seconds
- **Follow-up Generation**: ~2-4 seconds (with LLM)
- **Database Query**: ~100-500ms
- **Vector Search**: ~200-800ms

## Next Steps

1. ✅ Load question datasets into PostgreSQL
2. ✅ Generate embeddings and sync to Pinecone
3. ✅ Verify hybrid search functionality
4. ✅ Test question retrieval and semantic search
5. ✅ Test dynamic follow-up generation with o4-mini
6. 🔄 Integrate with other services (user, resume, transcription)
7. 🔄 Test complete end-to-end interview flow

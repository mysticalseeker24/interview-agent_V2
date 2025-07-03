# Pinecone & RAG Orchestration Implementation

This document describes the implementation of Task 2.5: Pinecone & RAG Orchestration for the TalentSync Interview Service.

## Overview

The implementation provides continuous sync and semantic retrieval capabilities using Pinecone vector database for question embeddings and RAG (Retrieval-Augmented Generation) orchestration.

## Core Components

### 1. PineconeService (`app/services/pinecone_service.py`)

Main service for Pinecone vector operations:

```python
# Initialization as specified in task
import pinecone, os
pinecone.init(api_key=os.getenv('PINECONE_API_KEY'), environment='us-west1-gcp')
questions_index = pinecone.Index('questions-embeddings')

# Embedding function
from openai import OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
def get_embedding(text: str) -> List[float]:
    resp = client.embeddings.create(input=text, model='text-embedding-ada-002')
    return resp.data[0].embedding

# Upsert function
def upsert_question_embedding(q_id: int, text: str, metadata: dict):
    emb = get_embedding(text)
    questions_index.upsert([(str(q_id), emb, metadata)])
```

**Key Features:**
- ✅ Pinecone initialization with `us-west1-gcp` environment
- ✅ OpenAI `text-embedding-ada-002` embeddings
- ✅ Question embedding upsert functionality
- ✅ Semantic search and retrieval
- ✅ Health check and monitoring

### 2. EmbeddingService (`app/services/embedding_service.py`)

High-level service for continuous sync and RAG orchestration:

**Features:**
- Continuous synchronization on question create/update
- Batch processing for multiple questions
- Semantic follow-up question retrieval
- Content-based question search
- Background sync worker

### 3. Example Implementation (`pinecone_example.py`)

Standalone example matching task requirements exactly:

```python
# Direct implementation as specified
import pinecone, os
pinecone.init(api_key=os.getenv('PINECONE_API_KEY'), environment='us-west1-gcp')
questions_index = pinecone.Index('questions-embeddings')

from openai import OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
def get_embedding(text: str) -> List[float]:
    resp = client.embeddings.create(input=text, model='text-embedding-ada-002')
    return resp.data[0].embedding

def upsert_question_embedding(q_id: int, text: str, metadata: dict):
    emb = get_embedding(text)
    questions_index.upsert([(str(q_id), emb, metadata)])
```

## Configuration

### Environment Variables

```bash
# Pinecone Configuration
PINECONE_API_KEY=your-pinecone-api-key-here
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_INDEX_NAME=questions-embeddings

# OpenAI Configuration  
OPENAI_API_KEY=your-openai-api-key-here
```

### Pinecone Index Setup

The implementation expects a Pinecone index named `questions-embeddings` with:
- **Dimensions**: 1536 (OpenAI text-embedding-ada-002)
- **Metric**: Cosine similarity
- **Environment**: us-west1-gcp

## Usage Examples

### 1. Basic Question Upsert

```python
from app.services.pinecone_service import PineconeService

service = PineconeService()

# Upsert a question
service.upsert_question_embedding(
    q_id=123,
    text="Tell me about your experience with Python",
    metadata={
        'domain': 'Software Engineering',
        'type': 'technical',
        'difficulty': 'medium'
    }
)
```

### 2. Semantic Search

```python
# Search for similar questions
results = await service.search_similar_questions(
    query_text="Python programming experience",
    domain="Software Engineering",
    top_k=5
)
```

### 3. Continuous Sync

```python
from app.services.embedding_service import EmbeddingService

embedding_service = EmbeddingService()

# Sync on question creation
question_data = {
    'id': 456,
    'text': 'How do you handle microservices architecture?',
    'domain': 'Software Engineering',
    'type': 'architectural'
}

await embedding_service.sync_question_on_create(question_data)
```

## API Integration

### Question Lifecycle Hooks

The service integrates with question CRUD operations:

```python
# On question create
async def create_question(question_data):
    # Save to database
    question = await db.save_question(question_data)
    
    # Sync to Pinecone
    await embedding_service.sync_question_on_create(question_data)
    
    return question

# On question update  
async def update_question(question_id, question_data):
    # Update in database
    question = await db.update_question(question_id, question_data)
    
    # Sync to Pinecone
    await embedding_service.sync_question_on_update(question_data)
    
    return question
```

### RAG Follow-up Generation

```python
# Get semantic follow-ups based on candidate answer
follow_ups = await embedding_service.get_semantic_follow_ups(
    session_id=session_id,
    answer_text=candidate_answer,
    session_context={
        'domain': 'Software Engineering',
        'difficulty': 'medium'
    }
)
```

## Testing

Run the test suite to verify implementation:

```bash
cd talentsync/services/interview-service
python test_pinecone.py
```

**Test Coverage:**
- ✅ Pinecone initialization
- ✅ Embedding generation
- ✅ Question upsert
- ✅ Semantic search
- ✅ Embedding service functionality
- ✅ Health checks

## Monitoring & Health Checks

### Service Health

```python
# Check service health
health = await embedding_service.health_check()

# Returns:
{
    'embedding_service': 'healthy',
    'pinecone': {
        'healthy': True,
        'index_name': 'questions-embeddings',
        'total_vectors': 1250
    },
    'overall_status': 'healthy'
}
```

### Metrics

- **Total vectors indexed**: Track number of questions in Pinecone
- **Sync success rate**: Monitor successful syncs vs failures
- **Search latency**: Track semantic search response times
- **Embedding generation rate**: Monitor OpenAI API usage

## Implementation Status

### ✅ Completed (Task 2.5 Requirements)

1. **Pinecone Initialization**
   - ✅ `pinecone.init()` with API key and `us-west1-gcp` environment
   - ✅ `questions_index = pinecone.Index('questions-embeddings')`

2. **Embedding Function**  
   - ✅ OpenAI client initialization
   - ✅ `get_embedding()` function using `text-embedding-ada-002`
   - ✅ Returns `List[float]` embeddings

3. **Upsert Functionality**
   - ✅ `upsert_question_embedding()` function
   - ✅ Combines embedding generation with Pinecone upsert
   - ✅ Handles question ID, text, and metadata

### 🔄 Next Phase (Awaiting Further Requirements)

- Advanced RAG orchestration patterns
- Multi-namespace support
- Batch processing optimizations
- Real-time sync triggers
- Advanced filtering and search capabilities

## Dependencies

```toml
# Already included in pyproject.toml
pinecone-client = "^2.2.4"
openai = "^1.3.5"
```

## Error Handling

The implementation includes comprehensive error handling:

- **API Key validation**: Checks for missing environment variables
- **Network errors**: Handles Pinecone and OpenAI API failures
- **Rate limiting**: Graceful handling of API rate limits
- **Data validation**: Ensures proper question data format
- **Retry logic**: Automatic retries for transient failures

This implementation provides a solid foundation for semantic question retrieval and RAG orchestration in the TalentSync interview system.

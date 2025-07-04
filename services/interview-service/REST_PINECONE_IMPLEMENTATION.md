# Pinecone & RAG Implementation with REST APIs

This document outlines the implementation of Task 2.5: Pinecone & RAG Orchestration for the TalentSync Interview Service using REST APIs.

## Overview

The implementation provides continuous sync and semantic retrieval capabilities using Pinecone vector database for question embeddings and RAG (Retrieval-Augmented Generation) orchestration through REST API endpoints.

## Implementation Strategy

Instead of using RabbitMQ as a message broker, this implementation uses a REST API-based approach for more straightforward deployment and maintenance:

1. **Database Triggers**: PostgreSQL triggers are used to mark questions that need synchronization
2. **REST API Endpoints**: Dedicated endpoints for question sync operations
3. **Background Tasks**: FastAPI background tasks for non-blocking sync operations
4. **Periodic Sync**: Optional scheduled sync via endpoint call for data consistency

## REST API Endpoints

### 1. Sync a Single Question

```http
POST /api/v1/vectors/sync/question
```

**Request body:**
```json
{
  "id": 123,
  "text": "Tell me about your experience with Python.",
  "domain": "Software Engineering",
  "type": "technical",
  "difficulty": "medium"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Question 123 sync started in background"
}
```

### 2. Batch Sync Multiple Questions

```http
POST /api/v1/vectors/sync/questions/batch
```

**Request body:**
```json
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

**Response:**
```json
{
  "status": "success",
  "message": "Batch sync of 2 questions started in background"
}
```

### 3. Sync All Questions

```http
POST /api/v1/vectors/sync/questions/all
```

**Response:**
```json
{
  "status": "success",
  "message": "Full sync of all questions started in background"
}
```

### 4. Get Follow-up Questions

```http
GET /api/v1/vectors/followups?answer=I%20have%20been%20using%20Python%20for%20five%20years...&asked=1,2,3
```

**Parameters:**
- `answer`: The candidate's answer text (URL encoded)
- `asked`: Comma-separated list of already asked question IDs

**Response:**
```json
[4, 7, 12, 15]
```

### 5. Search Questions Semantically

```http
GET /api/v1/vectors/search?query=python%20programming&domain=Software%20Engineering&limit=5
```

**Parameters:**
- `query`: Search query text (URL encoded)
- `domain` (optional): Filter by domain
- `question_type` (optional): Filter by question type
- `limit` (optional): Maximum number of results (default: 10)

**Response:**
```json
[
  {
    "id": 123,
    "text": "Tell me about your experience with Python.",
    "domain": "Software Engineering",
    "type": "technical",
    "difficulty": "medium",
    "similarity_score": 0.92
  },
  {
    "id": 456,
    "text": "Have you used Python for data analysis projects?",
    "domain": "Software Engineering",
    "type": "technical",
    "difficulty": "medium",
    "similarity_score": 0.87
  }
]
```

### 6. Health Check

```http
GET /api/v1/vectors/health
```

**Response:**
```json
{
  "embedding_service": "healthy",
  "pinecone": {
    "healthy": true,
    "index_name": "questions-embeddings",
    "total_vectors": 1250,
    "namespaces": 1,
    "message": "Pinecone service is healthy"
  },
  "overall_status": "healthy"
}
```

## Database Schema Updates

The following columns were added to the `questions` table to support continuous sync:

- `last_synced`: Timestamp when the question was last synced to Pinecone
- `domain`: Domain category for vector search filtering (e.g., "Software Engineering")

## Automatic Sync

Questions are automatically synchronized with Pinecone when they are created or updated through:

1. SQL triggers that update the `updated_at` timestamp
2. Event listeners that call the sync API endpoint
3. Background tasks that perform the actual sync

## Advantages of REST API Approach

1. **Simplicity**: No need for additional message broker infrastructure
2. **Direct Integration**: Easy to call from any service or admin interface
3. **Visibility**: Sync operations can be monitored and traced through HTTP logs
4. **Flexibility**: Easy to extend with authentication, rate limiting, etc.
5. **Portability**: Works across different environments without broker configuration

## Implementation Files

The implementation consists of the following key files:

1. `app/routers/vectors.py`: API endpoints for vector operations
2. `app/services/pinecone_service.py`: Core Pinecone integration service
3. `app/services/embedding_service.py`: Service for embedding and retrieval operations
4. `app/services/sync_trigger.py`: Database event listeners for automatic sync
5. `app/schemas/vector.py`: Pydantic schemas for request/response validation
6. `app/models/question.py`: Updated Question model with sync-related columns
7. `app/db/migrations/versions/20250703001_add_question_sync_columns.py`: Migration script

## Production Deployment Considerations

1. **Authentication**: Secure endpoints with proper authentication
2. **Rate Limiting**: Implement rate limiting for public-facing endpoints
3. **Monitoring**: Add metrics collection for sync operations
4. **Scaling**: Use connection pooling and concurrency controls for high-volume operations
5. **Fallbacks**: Implement retry logic for transient failures
6. **Maintenance**: Schedule periodic full syncs to ensure consistency

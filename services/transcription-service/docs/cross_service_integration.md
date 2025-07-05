# Cross-Service Integration: How Other Services Leverage Transcription Records

## Overview

The transcription service serves as a foundational data layer for the TalentSync platform. Multiple services depend on transcription records stored in PostgreSQL to provide intelligent interview experiences, follow-up question generation, performance feedback, and analytics insights.

## Data Flow Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Audio Input   │───▶│ Transcription    │───▶│   PostgreSQL    │
│   (User Speech) │    │   Service        │    │   Database      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Consuming Services                               │
├─────────────────┬─────────────────┬─────────────────┬───────────────┤
│ Interview       │ Follow-Up       │ Feedback        │ Analytics     │
│ Service         │ Service         │ Service         │ Service       │
└─────────────────┴─────────────────┴─────────────────┴───────────────┘
```

## Service Integration Details

### 1. Interview Service Integration

**Purpose**: Links transcription results to specific interview questions and maintains session context.

**Database Usage**:
- Stores transcription data in `responses.transcription_data` (JSONB column)
- Links responses to `session_id` and `question_id`
- Maintains audit trail with timestamps and metadata

**Key Operations**:
```sql
-- Store transcription result for a specific question
INSERT INTO responses (session_id, question_id, transcription_data, created_at)
VALUES ($1, $2, $3, NOW());

-- Retrieve all responses for a session
SELECT r.*, q.question_text, q.ideal_answer_summary
FROM responses r
JOIN questions q ON r.question_id = q.id
WHERE r.session_id = $1
ORDER BY r.created_at;
```

**Data Structure**:
```json
{
  "transcript_text": "I have experience with React and Node.js...",
  "confidence_score": 0.92,
  "provider": "openai",
  "segments": [...],
  "processing_time": 1.2,
  "fallback_used": false
}
```

### 2. Follow-Up Service Integration

**Purpose**: Generates intelligent follow-up questions based on previous responses and avoids question repetition.

**Database Usage**:
- Queries `responses` table to identify already-asked questions
- Extracts transcript text for RAG (Retrieval-Augmented Generation) embedding
- Uses historical context to determine next optimal question

**Key Operations**:
```sql
-- Find already asked questions to avoid repeats
SELECT DISTINCT question_id 
FROM responses 
WHERE session_id = $1;

-- Get transcript text for RAG embedding
SELECT r.transcription_data->>'transcript_text' as transcript,
       q.question_text,
       q.category
FROM responses r
JOIN questions q ON r.question_id = q.id
WHERE r.session_id = $1
ORDER BY r.created_at;
```

**Integration Flow**:
1. Receive request for next follow-up question
2. Query existing responses to avoid duplicates
3. Extract transcript text from all previous responses
4. Embed transcript content for semantic similarity search
5. Generate contextually relevant follow-up question
6. Return question with confidence score

### 3. Feedback Service Integration

**Purpose**: Provides comprehensive performance evaluation based on all interview responses.

**Database Usage**:
- Reads all session responses at interview completion
- Joins with ideal answers from questions table
- Stores detailed scoring in separate `scores` table
- Maintains scoring history and analytics

**Key Operations**:
```sql
-- Get all responses for feedback analysis
SELECT r.id as response_id,
       r.transcription_data->>'transcript_text' as answer_text,
       r.transcription_data->>'confidence_score' as transcription_confidence,
       q.question_text,
       q.ideal_answer_summary,
       q.category,
       q.difficulty_level
FROM responses r
JOIN questions q ON r.question_id = q.id
WHERE r.session_id = $1
ORDER BY r.created_at;

-- Store per-response scores
INSERT INTO scores (response_id, session_id, content_score, clarity_score, 
                   completeness_score, overall_score, feedback_text, created_at)
VALUES ($1, $2, $3, $4, $5, $6, $7, NOW());
```

**Scoring Dimensions**:
- **Content Score**: Relevance and accuracy of answer
- **Clarity Score**: Communication effectiveness
- **Completeness Score**: Thoroughness of response
- **Overall Score**: Weighted composite score

### 4. Analytics & Admin Dashboard Integration

**Purpose**: Provides operational insights and performance metrics across the platform.

**Database Usage**:
- Aggregates transcription volume and performance metrics
- Tracks STT provider usage and fallback rates
- Monitors system throughput and reliability

**Key Analytics Queries**:
```sql
-- Daily transcription volume
SELECT DATE(created_at) as date,
       COUNT(*) as transcription_count,
       AVG(CAST(transcription_data->>'confidence_score' AS FLOAT)) as avg_confidence
FROM responses
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date;

-- Provider fallback analysis
SELECT transcription_data->>'provider' as provider,
       COUNT(*) as usage_count,
       COUNT(CASE WHEN transcription_data->>'fallback_used' = 'true' THEN 1 END) as fallback_count
FROM responses
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY transcription_data->>'provider';

-- Session completion rates
SELECT s.status,
       COUNT(*) as session_count,
       AVG(response_count) as avg_responses_per_session
FROM sessions s
LEFT JOIN (
    SELECT session_id, COUNT(*) as response_count
    FROM responses
    GROUP BY session_id
) r ON s.id = r.session_id
WHERE s.created_at >= NOW() - INTERVAL '30 days'
GROUP BY s.status;
```

## Data Consistency and Reliability

### Transaction Management
- All transcription writes use database transactions
- Cross-service operations maintain ACID properties
- Rollback capabilities for failed processing chains

### Error Handling
- Graceful degradation when transcription quality is low
- Retry mechanisms for failed database operations
- Monitoring and alerting for service dependencies

### Performance Optimization
- Database indexes on frequently queried columns (`session_id`, `created_at`)
- Connection pooling for high-throughput scenarios
- Async processing for non-blocking operations

## Monitoring and Observability

### Key Metrics
- **Transcription Success Rate**: Percentage of successful transcriptions
- **Average Processing Time**: Time from audio upload to stored transcript
- **Provider Distribution**: Usage across OpenAI, AssemblyAI, fallback
- **Cross-Service Latency**: Time between transcription and downstream processing

### Health Checks
- Database connectivity validation
- Provider API availability
- Storage system accessibility
- Cross-service communication status

## Future Enhancements

### Planned Improvements
1. **Real-time Streaming**: Live transcription during interviews
2. **Multi-language Support**: Expanded language detection and processing
3. **Advanced Analytics**: ML-based insights from transcription patterns
4. **Data Archival**: Long-term storage and retrieval strategies

### Scaling Considerations
- Horizontal scaling of transcription workers
- Database sharding strategies for high volume
- Caching layers for frequently accessed transcripts
- CDN integration for audio file distribution

## Security and Compliance

### Data Protection
- Encryption at rest for all transcription data
- PII detection and redaction capabilities
- Audit logging for all data access
- GDPR compliance for data retention and deletion

### Access Control
- Service-to-service authentication
- Role-based access to transcription records
- API rate limiting and quota management
- Secure data transmission protocols

---

*This document provides a comprehensive overview of how transcription records flow through the TalentSync platform ecosystem, enabling intelligent interview experiences and data-driven insights.*

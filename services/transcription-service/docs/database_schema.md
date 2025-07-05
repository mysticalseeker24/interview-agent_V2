# Database Schema: Cross-Service Data Model

## Overview

This document details the PostgreSQL database schema used across TalentSync services, with a focus on how transcription data flows through the system and supports other microservices.

## Core Tables

### 1. Transcriptions Table (Transcription Service)

```sql
CREATE TABLE transcriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    session_id UUID,
    file_name VARCHAR(255) NOT NULL,
    file_size BIGINT NOT NULL,
    original_audio_path TEXT,
    transcript_text TEXT,
    confidence_score FLOAT,
    provider VARCHAR(50) NOT NULL, -- 'openai', 'assemblyai', 'fallback'
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    segments JSONB, -- Detailed segment information
    processing_time FLOAT,
    error_message TEXT,
    fallback_used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes for efficient querying
    INDEX idx_transcriptions_user_id (user_id),
    INDEX idx_transcriptions_session_id (session_id),
    INDEX idx_transcriptions_status (status),
    INDEX idx_transcriptions_created_at (created_at),
    INDEX idx_transcriptions_provider (provider)
);
```

**Sample Data**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "session_id": "789e0123-e45b-67c8-d901-234567890abc",
  "file_name": "interview_response_001.wav",
  "file_size": 2048576,
  "original_audio_path": "/uploads/audio/interview_response_001.wav",
  "transcript_text": "I have five years of experience in software development, primarily working with Python and JavaScript frameworks like React and Django.",
  "confidence_score": 0.92,
  "provider": "openai",
  "status": "completed",
  "segments": [
    {
      "start": 0.0,
      "end": 2.5,
      "text": "I have five years of experience",
      "confidence": 0.95
    },
    {
      "start": 2.5,
      "end": 6.8,
      "text": "in software development, primarily working",
      "confidence": 0.89
    }
  ],
  "processing_time": 1.23,
  "error_message": null,
  "fallback_used": false,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:01Z"
}
```

### 2. Responses Table (Interview Service)

```sql
CREATE TABLE responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL,
    question_id UUID NOT NULL,
    transcription_data JSONB NOT NULL, -- Embedded transcription result
    user_audio_path TEXT,
    processing_status VARCHAR(20) DEFAULT 'completed',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Foreign key relationships
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
    
    -- Indexes for efficient cross-service queries
    INDEX idx_responses_session_id (session_id),
    INDEX idx_responses_question_id (question_id),
    INDEX idx_responses_created_at (created_at),
    
    -- GIN index for JSONB transcription_data queries
    INDEX idx_responses_transcription_gin USING GIN (transcription_data)
);
```

**Transcription Data Structure in Responses**:
```json
{
  "transcript_text": "I have five years of experience in software development...",
  "confidence_score": 0.92,
  "provider": "openai",
  "segments": [
    {
      "start": 0.0,
      "end": 2.5,
      "text": "I have five years of experience",
      "confidence": 0.95
    }
  ],
  "processing_time": 1.23,
  "fallback_used": false,
  "transcription_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 3. Sessions Table (Interview Service)

```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    job_position VARCHAR(255) NOT NULL,
    difficulty_level VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(20) NOT NULL DEFAULT 'active', -- 'active', 'completed', 'paused', 'cancelled'
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    total_questions INTEGER DEFAULT 0,
    answered_questions INTEGER DEFAULT 0,
    
    -- Indexes
    INDEX idx_sessions_user_id (user_id),
    INDEX idx_sessions_status (status),
    INDEX idx_sessions_started_at (started_at)
);
```

### 4. Questions Table (Interview Service)

```sql
CREATE TABLE questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_text TEXT NOT NULL,
    category VARCHAR(100) NOT NULL, -- 'technical', 'behavioral', 'situational'
    difficulty_level VARCHAR(20) NOT NULL, -- 'easy', 'medium', 'hard'
    job_position VARCHAR(255),
    ideal_answer_summary TEXT,
    keywords TEXT[], -- Array of expected keywords
    estimated_time INTEGER, -- Expected answer time in seconds
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_questions_category (category),
    INDEX idx_questions_difficulty (difficulty_level),
    INDEX idx_questions_position (job_position)
);
```

### 5. Scores Table (Feedback Service)

```sql
CREATE TABLE scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    response_id UUID NOT NULL,
    session_id UUID NOT NULL,
    content_score FLOAT NOT NULL, -- 0.0 to 1.0
    clarity_score FLOAT NOT NULL, -- 0.0 to 1.0
    completeness_score FLOAT NOT NULL, -- 0.0 to 1.0
    overall_score FLOAT NOT NULL, -- 0.0 to 1.0
    feedback_text TEXT,
    scoring_model VARCHAR(50), -- 'gpt-4', 'custom', etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Foreign keys
    FOREIGN KEY (response_id) REFERENCES responses(id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    
    -- Indexes
    INDEX idx_scores_response_id (response_id),
    INDEX idx_scores_session_id (session_id),
    INDEX idx_scores_overall_score (overall_score)
);
```

## Cross-Service Query Patterns

### 1. Interview Service: Store Transcription Result

```sql
-- Insert response with embedded transcription data
INSERT INTO responses (session_id, question_id, transcription_data, user_audio_path)
VALUES (
    $1, -- session_id
    $2, -- question_id
    $3, -- transcription_data JSONB
    $4  -- user_audio_path
);
```

### 2. Follow-Up Service: Get Session Context

```sql
-- Retrieve all previous responses for intelligent follow-up generation
SELECT 
    r.id,
    r.transcription_data->>'transcript_text' as transcript,
    r.transcription_data->>'confidence_score' as confidence,
    q.question_text,
    q.category,
    q.difficulty_level,
    r.created_at
FROM responses r
JOIN questions q ON r.question_id = q.id
WHERE r.session_id = $1
ORDER BY r.created_at;
```

### 3. Follow-Up Service: Avoid Question Repeats

```sql
-- Find already asked questions to prevent duplicates
SELECT DISTINCT question_id
FROM responses
WHERE session_id = $1;
```

### 4. Feedback Service: Comprehensive Session Analysis

```sql
-- Get all responses with question context for scoring
SELECT 
    r.id as response_id,
    r.session_id,
    r.transcription_data->>'transcript_text' as answer_text,
    CAST(r.transcription_data->>'confidence_score' AS FLOAT) as transcription_confidence,
    r.transcription_data->>'provider' as transcription_provider,
    q.question_text,
    q.ideal_answer_summary,
    q.category,
    q.difficulty_level,
    q.keywords,
    q.estimated_time,
    r.created_at as answered_at
FROM responses r
JOIN questions q ON r.question_id = q.id
WHERE r.session_id = $1
ORDER BY r.created_at;
```

### 5. Analytics Service: Performance Metrics

```sql
-- Daily transcription success rates
SELECT 
    DATE(r.created_at) as date,
    COUNT(*) as total_responses,
    AVG(CAST(r.transcription_data->>'confidence_score' AS FLOAT)) as avg_confidence,
    COUNT(CASE WHEN r.transcription_data->>'fallback_used' = 'true' THEN 1 END) as fallback_count,
    COUNT(DISTINCT r.session_id) as unique_sessions
FROM responses r
WHERE r.created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(r.created_at)
ORDER BY date;
```

```sql
-- Provider usage distribution
SELECT 
    r.transcription_data->>'provider' as provider,
    COUNT(*) as usage_count,
    AVG(CAST(r.transcription_data->>'processing_time' AS FLOAT)) as avg_processing_time,
    AVG(CAST(r.transcription_data->>'confidence_score' AS FLOAT)) as avg_confidence
FROM responses r
WHERE r.created_at >= NOW() - INTERVAL '7 days'
GROUP BY r.transcription_data->>'provider'
ORDER BY usage_count DESC;
```

## Data Relationships and Constraints

### Primary Relationships

1. **Users → Sessions**: One user can have multiple interview sessions
2. **Sessions → Responses**: One session contains multiple question responses
3. **Questions → Responses**: One question can be answered in multiple sessions
4. **Responses → Scores**: Each response gets detailed scoring
5. **Transcriptions → Responses**: Transcription data is embedded in responses

### Data Flow Sequence

```
1. User uploads audio → Transcriptions table (transcription-service)
2. Transcription processed → Update transcriptions.status
3. Result passed to interview-service → Insert into responses.transcription_data
4. Follow-up service queries responses → Generate next question
5. Feedback service analyzes all responses → Insert scores
6. Analytics service aggregates data → Generate insights
```

## Performance Considerations

### Indexing Strategy

```sql
-- Critical indexes for cross-service performance
CREATE INDEX CONCURRENTLY idx_responses_session_transcription 
ON responses USING GIN ((transcription_data->>'transcript_text') gin_trgm_ops);

CREATE INDEX CONCURRENTLY idx_responses_confidence 
ON responses ((CAST(transcription_data->>'confidence_score' AS FLOAT)));

CREATE INDEX CONCURRENTLY idx_responses_provider_date 
ON responses ((transcription_data->>'provider'), created_at);
```

### Connection Pooling Configuration

```python
# Example for each service
DATABASE_POOL_CONFIG = {
    "min_connections": 5,
    "max_connections": 20,
    "connection_timeout": 30,
    "command_timeout": 60
}
```

## Migration Scripts

### Adding New Transcription Fields

```sql
-- Example migration for adding new transcription metadata
ALTER TABLE responses 
ADD COLUMN IF NOT EXISTS transcription_version VARCHAR(10) DEFAULT '1.0';

-- Update existing records
UPDATE responses 
SET transcription_data = transcription_data || '{"version": "1.0"}'::jsonb
WHERE transcription_data ? 'transcript_text' 
AND NOT transcription_data ? 'version';
```

## Monitoring and Alerting

### Key Metrics to Monitor

1. **Cross-service query performance**
2. **JSONB field access patterns**
3. **Index utilization rates**
4. **Connection pool saturation**
5. **Transaction rollback rates**

### Health Check Queries

```sql
-- Check recent transcription processing
SELECT COUNT(*) as recent_transcriptions
FROM responses
WHERE created_at > NOW() - INTERVAL '5 minutes'
AND transcription_data ? 'transcript_text';

-- Verify cross-service data consistency
SELECT 
    COUNT(DISTINCT session_id) as active_sessions,
    COUNT(*) as total_responses,
    AVG(CAST(transcription_data->>'confidence_score' AS FLOAT)) as avg_confidence
FROM responses r
JOIN sessions s ON r.session_id = s.id
WHERE s.status = 'active';
```

---

*This schema documentation serves as the foundation for understanding how transcription data flows through the TalentSync platform and enables intelligent cross-service interactions.*

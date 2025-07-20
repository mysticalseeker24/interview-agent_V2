"""Pydantic schemas for TalentSync Interview Service API."""
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field


# Module Schemas
class Module(BaseModel):
    """Interview module schema."""
    id: str
    title: str
    description: str
    category: str
    difficulty: str = Field(..., pattern="^(easy|medium|hard)$")
    duration_minutes: int = Field(..., ge=5, le=120)
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ModuleCreate(BaseModel):
    """Module creation schema."""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10, max_length=1000)
    category: str = Field(..., min_length=1, max_length=100)
    difficulty: str = Field(..., pattern="^(easy|medium|hard)$")
    duration_minutes: int = Field(..., ge=5, le=120)


# Question Schemas
class Question(BaseModel):
    """Question schema."""
    id: str
    text: str
    difficulty: str = Field(..., pattern="^(easy|medium|hard)$")
    question_type: str = Field(..., pattern="^(conceptual|behavioral|technical|coding|follow-up)$")
    expected_duration_seconds: int = Field(..., ge=30, le=300)
    tags: List[str] = []
    domain: str
    ideal_answer_summary: Optional[str] = None
    follow_up_templates: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class QuestionCreate(BaseModel):
    """Question creation schema."""
    text: str = Field(..., min_length=10, max_length=1000)
    difficulty: str = Field(..., pattern="^(easy|medium|hard)$")
    question_type: str = Field(..., pattern="^(conceptual|behavioral|technical|coding|follow-up)$")
    expected_duration_seconds: int = Field(..., ge=30, le=300)
    tags: List[str] = []
    domain: str = Field(..., min_length=1, max_length=100)
    ideal_answer_summary: Optional[str] = None
    follow_up_templates: Optional[List[str]] = None


# Session Schemas
class SessionCreate(BaseModel):
    """Session creation schema."""
    module_id: str = Field(..., description="Module ID to start session for")
    mode: str = Field(default="practice", pattern="^(practice|formal|invite-only)$")
    parsed_resume_data: Optional[Dict[str, Any]] = None


class Session(BaseModel):
    """Session schema."""
    id: UUID
    user_id: UUID
    module_id: str
    mode: str
    status: str = Field(..., pattern="^(pending|active|completed|cancelled)$")
    current_question_index: int = Field(default=0, ge=0)
    estimated_duration_minutes: int = Field(..., ge=5, le=120)
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    queue_length: int = Field(..., ge=0)
    asked_questions: List[str] = []


class SessionUpdate(BaseModel):
    """Session update schema."""
    status: Optional[str] = Field(None, pattern="^(pending|active|completed|cancelled)$")
    current_question_index: Optional[int] = Field(None, ge=0)


# Answer Schemas
class AnswerIn(BaseModel):
    """Answer submission schema."""
    answer_text: str = Field(..., min_length=1, max_length=10000)
    audio_file_path: Optional[str] = None
    started_at: datetime
    duration_seconds: Optional[float] = Field(None, ge=0, le=300)
    confidence_score: Optional[float] = Field(None, ge=0, le=1)


class AnswerOut(BaseModel):
    """Answer response schema."""
    answer_id: UUID
    session_id: UUID
    question_id: str
    answer_text: str
    confidence_score: Optional[float]
    duration_seconds: Optional[float]
    created_at: datetime


# Follow-up Schemas
class FollowUpOut(BaseModel):
    """Follow-up question response schema."""
    question_id: str
    question_text: str
    difficulty: str
    question_type: str
    domain: str
    generation_method: str = Field(..., pattern="^(rag|llm|hybrid)$")
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    remaining_questions: int = Field(..., ge=0)
    is_complete: bool = False


class FollowUpRequest(BaseModel):
    """Follow-up generation request schema."""
    answer_text: str = Field(..., min_length=1, max_length=10000)
    domain: str = Field(..., min_length=1, max_length=100)
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$")
    use_llm: bool = True
    max_candidates: int = Field(default=5, ge=1, le=10)


# Next Question Schemas
class NextQuestionResponse(BaseModel):
    """Next question response schema."""
    question: Optional[Question] = None
    session: Session
    is_complete: bool = False
    remaining_questions: int = Field(..., ge=0)
    estimated_time_remaining_minutes: Optional[int] = None


# Resume Integration Schemas
class ResumeData(BaseModel):
    """Resume data schema."""
    skills: List[str] = []
    experience: List[Dict[str, Any]] = []
    education: List[Dict[str, Any]] = []
    projects: List[Dict[str, Any]] = []
    languages: List[str] = []
    certifications: List[str] = []


class ResumeQuestionRequest(BaseModel):
    """Resume question generation request."""
    resume_data: ResumeData
    domain: str
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$")
    max_questions: int = Field(default=5, ge=1, le=10)


# Vector Search Schemas
class VectorSearchRequest(BaseModel):
    """Vector search request schema."""
    query_text: str = Field(..., min_length=1, max_length=1000)
    domain: Optional[str] = None
    question_type: Optional[str] = None
    difficulty: Optional[str] = Field(None, pattern="^(easy|medium|hard)$")
    top_k: int = Field(default=5, ge=1, le=20)
    exclude_ids: Optional[List[str]] = None


class VectorSearchResult(BaseModel):
    """Vector search result schema."""
    question_id: str
    text: str
    domain: str
    difficulty: str
    question_type: str
    similarity_score: float = Field(..., ge=0, le=1)
    metadata: Optional[Dict[str, Any]] = None


class VectorSearchResponse(BaseModel):
    """Vector search response schema."""
    results: List[VectorSearchResult]
    total_found: int
    query_time_ms: float


# Health Check Schemas
class HealthCheck(BaseModel):
    """Health check response schema."""
    status: str
    service: str
    version: str
    timestamp: datetime
    uptime_seconds: float
    dependencies: Dict[str, str]


class ServiceHealth(BaseModel):
    """Individual service health status."""
    service: str
    status: str
    response_time_ms: float
    last_check: datetime
    error_message: Optional[str] = None


# Error Response Schemas
class ErrorResponse(BaseModel):
    """Standard error response schema."""
    error: str
    detail: str
    timestamp: datetime
    request_id: Optional[str] = None


# Performance Metrics Schemas
class PerformanceMetrics(BaseModel):
    """Performance metrics schema."""
    endpoint: str
    method: str
    avg_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    request_count: int
    error_count: int
    success_rate: float
    timestamp: datetime


# Dataset Import Schemas
class DatasetImportRequest(BaseModel):
    """Dataset import request schema."""
    file_path: Optional[str] = None
    questions: Optional[List[QuestionCreate]] = None
    module_id: Optional[str] = None
    overwrite_existing: bool = False


class DatasetImportResponse(BaseModel):
    """Dataset import response schema."""
    imported_count: int
    skipped_count: int
    error_count: int
    errors: List[str] = []
    processing_time_ms: float
    status: str = Field(..., pattern="^(success|partial|failed)$")


# Event Schemas
class ChunkUploadEvent(BaseModel):
    """Chunk upload event from media service."""
    session_id: str
    chunk_id: int
    sequence_index: int
    file_path: str
    file_size_bytes: int
    overlap_seconds: float
    question_id: Optional[str] = None
    total_chunks: Optional[int] = None
    is_final_chunk: bool = False


class SessionCompleteEvent(BaseModel):
    """Session completion event."""
    session_id: str
    user_id: str
    module_id: str
    total_questions: int
    completed_questions: int
    total_duration_seconds: float
    completion_reason: str = Field(..., pattern="^(completed|cancelled|timeout)$")
    metadata: Optional[Dict[str, Any]] = None 
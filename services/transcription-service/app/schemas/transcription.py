from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class TranscriptionBase(BaseModel):
    """Base schema for transcription data."""
    chunk_id: str = Field(..., description="Chunk identifier")
    transcript_text: str = Field(..., description="Transcribed text")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score")


class TranscriptionCreate(TranscriptionBase):
    """Schema for creating a transcription."""
    session_id: Optional[str] = Field(None, description="Session identifier")
    sequence_index: Optional[int] = Field(None, ge=0, description="Sequence index")
    segments: Optional[str] = Field(None, description="JSON string for detailed segments")
    language: Optional[str] = Field(None, description="Detected language")
    duration_seconds: Optional[float] = Field(None, ge=0, description="Audio duration")


class TranscriptionUpdate(BaseModel):
    """Schema for updating a transcription."""
    transcript_text: Optional[str] = Field(None, description="Transcribed text")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score")
    segments: Optional[str] = Field(None, description="JSON string for detailed segments")
    language: Optional[str] = Field(None, description="Detected language")
    duration_seconds: Optional[float] = Field(None, ge=0, description="Audio duration")


class Transcription(TranscriptionBase):
    """Complete transcription schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    session_id: Optional[str] = None
    sequence_index: Optional[int] = None
    segments: Optional[str] = None
    language: Optional[str] = None
    duration_seconds: Optional[float] = None
    created_at: datetime
    updated_at: datetime


class TranscriptionResponse(BaseModel):
    """Response schema for transcription endpoint."""
    transcript: str = Field(..., description="Transcribed text")
    segments: Optional[List[Dict[str, Any]]] = Field(None, description="Detailed segments")
    confidence: Optional[float] = Field(None, description="Confidence score")
    language: Optional[str] = Field(None, description="Detected language")
    duration_seconds: Optional[float] = Field(None, description="Audio duration")


class TTSRequest(BaseModel):
    """Schema for TTS generation request."""
    text: str = Field(..., min_length=1, max_length=10000, description="Text to synthesize")
    voice: str = Field(default="Briggs-PlayAI", description="Voice to use")
    format: str = Field(default="wav", description="Audio format (only wav supported)")


class TTSResponse(BaseModel):
    """Schema for TTS generation response."""
    file_url: str = Field(..., description="URL to generated audio file")
    file_path: str = Field(..., description="Path to cached file")
    file_size_bytes: Optional[int] = Field(None, description="File size in bytes")
    duration_seconds: Optional[float] = Field(None, description="Audio duration")
    is_cached: bool = Field(..., description="Whether result was from cache")


class TTSCacheInfo(BaseModel):
    """Schema for TTS cache information."""
    total_requests: int = Field(..., description="Total TTS requests")
    cache_hits: int = Field(..., description="Number of cache hits")
    cache_misses: int = Field(..., description="Number of cache misses")
    total_file_size: int = Field(..., description="Total cache size in bytes")
    average_duration: Optional[float] = Field(None, description="Average audio duration")


class ChunkUploadRequest(BaseModel):
    """Schema for chunk upload request."""
    session_id: str = Field(..., description="Session identifier")
    chunk_id: str = Field(..., description="Chunk identifier")
    sequence_index: int = Field(..., ge=0, description="Sequence index")
    audio_data: str = Field(..., description="Base64 encoded audio data")
    overlap_seconds: float = Field(default=2.0, ge=0, description="Overlap duration")


class ChunkUploadResponse(BaseModel):
    """Schema for chunk upload response."""
    chunk_id: str = Field(..., description="Chunk identifier")
    session_id: str = Field(..., description="Session identifier")
    sequence_index: int = Field(..., description="Sequence index")
    transcription_id: Optional[int] = Field(None, description="Transcription ID")
    status: str = Field(..., description="Processing status")
    message: str = Field(..., description="Response message")


class SessionCompleteRequest(BaseModel):
    """Schema for session completion request."""
    session_id: str = Field(..., description="Session identifier")
    total_chunks: int = Field(..., ge=1, description="Total number of chunks")


class SessionCompleteResponse(BaseModel):
    """Schema for session completion response."""
    session_id: str = Field(..., description="Session identifier")
    full_transcript: str = Field(..., description="Complete session transcript")
    total_chunks: int = Field(..., description="Total number of chunks")
    confidence_score: Optional[float] = Field(None, description="Overall confidence")
    duration_seconds: Optional[float] = Field(None, description="Total session duration")


class HealthCheckResponse(BaseModel):
    """Schema for health check response."""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Check timestamp")
    version: str = Field(..., description="Service version")
    components: Dict[str, str] = Field(..., description="Component statuses")


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow) 
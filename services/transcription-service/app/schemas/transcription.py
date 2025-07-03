"""Transcription schema definitions."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class TranscriptionSegment(BaseModel):
    """Transcription segment schema."""
    start: float
    end: float
    text: str
    confidence: Optional[float] = None


class TranscriptionRequest(BaseModel):
    """Transcription request schema."""
    session_id: Optional[int] = None
    language: Optional[str] = "en"
    enable_fallback: bool = True


class TranscriptionResponse(BaseModel):
    """Transcription response schema."""
    transcript: str
    segments: List[TranscriptionSegment] = []
    confidence_score: Optional[float] = None
    provider: str = "openai"
    fallback_used: bool = False
    duration_seconds: Optional[float] = None
    
    class Config:
        from_attributes = True


class TranscriptionListResponse(BaseModel):
    """Transcription list response schema."""
    transcriptions: List[TranscriptionResponse]
    total: int
    skip: int
    limit: int


class TranscriptionStatus(BaseModel):
    """Transcription status schema."""
    id: int
    status: str
    transcript: Optional[str] = None
    confidence_score: Optional[float] = None
    provider: Optional[str] = None
    fallback_used: bool = False
    created_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class TranscriptionRead(BaseModel):
    """Transcription read schema."""
    id: int
    user_id: int
    session_id: Optional[int] = None
    filename: str
    file_size: int
    file_type: str
    duration_seconds: Optional[float] = None
    transcript_text: Optional[str] = None
    segments: Optional[List[Dict[str, Any]]] = None
    provider: Optional[str] = None
    model_used: Optional[str] = None
    confidence_score: Optional[float] = None
    fallback_used: bool = False
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
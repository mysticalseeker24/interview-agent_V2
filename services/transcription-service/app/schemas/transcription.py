from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class TranscriptionBase(BaseModel):
    session_id: str
    question_id: Optional[str] = None
    transcript_text: str

class TranscriptionCreate(TranscriptionBase):
    pass

class Transcription(TranscriptionBase):
    id: int
    media_chunk_id: Optional[str] = None
    sequence_index: Optional[int] = None
    segments: Optional[List[Dict[str, Any]]] = None
    confidence_score: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True

class TranscriptionChunkRequest(BaseModel):
    session_id: str
    media_chunk_id: str
    sequence_index: int
    audio_data: str  # Base64 encoded audio data
    question_id: Optional[str] = None

class CompleteSessionRequest(BaseModel):
    session_id: str

class TranscriptionChunkResponse(BaseModel):
    id: int
    session_id: str
    media_chunk_id: str
    sequence_index: int
    transcript_text: str
    segments: Optional[List[Dict[str, Any]]] = None
    confidence_score: Optional[float] = None
    created_at: datetime
    
    # Optional integration fields
    follow_up_triggered: Optional[bool] = None
    follow_up_question: Optional[str] = None

class SessionCompleteResponse(BaseModel):
    session_id: str
    full_transcript: str
    total_chunks: int
    confidence_score: Optional[float] = None
    segments: Optional[List[Dict[str, Any]]] = None
    
    # Optional integration fields
    feedback_triggered: Optional[bool] = None
    feedback_task_id: Optional[str] = None

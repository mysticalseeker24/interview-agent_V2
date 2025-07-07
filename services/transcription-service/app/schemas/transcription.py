from pydantic import BaseModel, Field, validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class VoiceType(str, Enum):
    """Available OpenAI TTS voices."""
    ALLOY = "alloy"
    ECHO = "echo"
    FABLE = "fable"
    ONYX = "onyx"
    NOVA = "nova"
    SHIMMER = "shimmer"

class AudioFormat(str, Enum):
    """Supported audio formats."""
    MP3 = "mp3"
    WAV = "wav"
    FLAC = "flac"
    AAC = "aac"

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


# TTS Schemas
class TTSRequestIn(BaseModel):
    """Input schema for TTS generation requests."""
    text: str = Field(..., min_length=1, max_length=4000, description="Text to convert to speech")
    voice: Optional[str] = Field(default="alloy", description="OpenAI TTS voice (alloy, echo, fable, onyx, nova, shimmer)")
    format: Optional[str] = Field(default="mp3", description="Audio format (mp3, wav, opus)")
    speed: Optional[float] = Field(default=1.0, ge=0.25, le=4.0, description="Speech speed multiplier")

class TTSRequestOut(BaseModel):
    """Output schema for TTS generation response."""
    tts_id: int
    file_path: str
    url: str
    file_size: Optional[int] = None
    duration: Optional[float] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class TTSCacheStats(BaseModel):
    """Statistics for TTS cache."""
    total_requests: int
    cache_hits: int
    cache_miss: int
    total_file_size: int
    average_duration: Optional[float] = None

class TTSCacheInfo(BaseModel):
    """Cache information for TTS requests."""
    cache_key: str
    is_cached: bool
    cache_age_hours: Optional[float] = None
    file_exists: bool

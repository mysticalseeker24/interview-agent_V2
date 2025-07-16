from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class InterviewRoundRequest(BaseModel):
    """Schema for interview round request."""
    agent_question: str = Field(..., description="Question the agent is asking")
    session_id: str = Field(..., description="Interview session ID")
    round_number: int = Field(default=1, ge=1, description="Current round number")


class UserResponse(BaseModel):
    """Schema for user response data."""
    raw_text: str = Field(..., description="Raw transcribed text")
    structured_json: Dict[str, Any] = Field(..., description="Structured JSON response")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Transcription confidence")
    segments: List[Dict[str, Any]] = Field(default=[], description="Detailed segments")
    language: str = Field(default="en", description="Detected language")


class InterviewRoundResponse(BaseModel):
    """Schema for interview round response."""
    session_id: str = Field(..., description="Interview session ID")
    round_number: int = Field(..., description="Round number")
    agent_question: str = Field(..., description="Question the agent asked")
    agent_question_audio_url: str = Field(..., description="URL to agent question audio")
    user_response: UserResponse = Field(..., description="User's response data")
    agent_reply: str = Field(..., description="Agent's reply text")
    agent_reply_audio_url: str = Field(..., description="URL to agent reply audio")
    timestamp: str = Field(..., description="Timestamp of the round")


class PipelineStatusResponse(BaseModel):
    """Schema for pipeline status response."""
    status: str = Field(..., description="Overall pipeline status")
    components: Dict[str, Any] = Field(..., description="Component health status")
    models: Dict[str, str] = Field(..., description="Model configuration")
    error: Optional[str] = Field(None, description="Error message if unhealthy")


class StructuredResponse(BaseModel):
    """Schema for structured user response."""
    raw_text: str = Field(..., description="Raw transcribed text")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Transcription confidence")
    segments: List[Dict[str, Any]] = Field(default=[], description="Detailed segments")
    extracted_info: Dict[str, Any] = Field(..., description="Extracted information")
    interview_metrics: Dict[str, Any] = Field(..., description="Interview metrics")


class InterviewMetrics(BaseModel):
    """Schema for interview metrics."""
    response_time: float = Field(..., ge=0.0, description="Response time in seconds")
    clarity_score: float = Field(..., ge=0.0, le=1.0, description="Clarity score")
    completeness_score: float = Field(..., ge=0.0, le=1.0, description="Completeness score")


class ExtractedInfo(BaseModel):
    """Schema for extracted information from user response."""
    answer_length: int = Field(..., ge=0, description="Length of the answer")
    has_technical_terms: bool = Field(..., description="Whether response contains technical terms")
    sentiment: str = Field(..., description="Sentiment analysis result")
    key_topics: List[str] = Field(default=[], description="Key topics identified")


class TTSOnlyRequest(BaseModel):
    """Schema for TTS-only request."""
    text: str = Field(..., min_length=1, max_length=10000, description="Text to synthesize")
    voice: str = Field(default="Briggs-PlayAI", description="Voice to use")


class TTSOnlyResponse(BaseModel):
    """Schema for TTS-only response."""
    text: str = Field(..., description="Original text")
    voice: str = Field(..., description="Voice used")
    audio_url: str = Field(..., description="URL to generated audio")
    file_size_bytes: Optional[int] = Field(None, description="File size in bytes")
    duration_seconds: Optional[float] = Field(None, description="Audio duration")


class STTOnlyResponse(BaseModel):
    """Schema for STT-only response."""
    text: str = Field(..., description="Transcribed text")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Transcription confidence")
    segments: List[Dict[str, Any]] = Field(default=[], description="Detailed segments")
    language: str = Field(default="en", description="Detected language")
    duration_seconds: Optional[float] = Field(None, description="Audio duration") 
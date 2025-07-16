"""
Pydantic schemas for Media Service.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

from pydantic import BaseModel, Field, ConfigDict, validator


class MediaChunkBase(BaseModel):
    """Base schema for MediaChunk."""
    session_id: str = Field(..., description="Session identifier")
    question_id: Optional[str] = Field(None, description="Question identifier")
    sequence_index: int = Field(..., ge=0, description="Chunk sequence index")
    overlap_seconds: float = Field(default=2.0, ge=0, description="Overlap duration in seconds")
    file_name: str = Field(..., description="Original file name")
    file_extension: Optional[str] = Field(None, description="File extension")
    duration_seconds: Optional[float] = Field(None, ge=0, description="Audio duration")
    sample_rate: Optional[int] = Field(None, gt=0, description="Audio sample rate")
    bit_rate: Optional[int] = Field(None, gt=0, description="Audio bit rate")
    channels: Optional[int] = Field(None, gt=0, description="Audio channels")


class MediaChunkCreate(MediaChunkBase):
    """Schema for creating a MediaChunk."""
    pass


class MediaChunkUpdate(BaseModel):
    """Schema for updating a MediaChunk."""
    upload_status: Optional[str] = Field(None, description="Upload status")
    transcription_status: Optional[str] = Field(None, description="Transcription status")
    duration_seconds: Optional[float] = Field(None, ge=0, description="Audio duration")
    sample_rate: Optional[int] = Field(None, gt=0, description="Audio sample rate")
    bit_rate: Optional[int] = Field(None, gt=0, description="Audio bit rate")
    channels: Optional[int] = Field(None, gt=0, description="Audio channels")
    audio_quality_score: Optional[float] = Field(None, ge=0, le=1, description="Quality score")
    noise_level: Optional[float] = Field(None, ge=0, description="Noise level")
    silence_percentage: Optional[float] = Field(None, ge=0, le=100, description="Silence percentage")
    is_valid: Optional[bool] = Field(None, description="Validation status")
    validation_errors: Optional[str] = Field(None, description="Validation errors")


class MediaChunk(MediaChunkBase):
    """Complete MediaChunk schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    file_path: str
    file_size_bytes: Optional[int] = None
    upload_status: str = "pending"
    transcription_status: str = "pending"
    audio_quality_score: Optional[float] = None
    noise_level: Optional[float] = None
    silence_percentage: Optional[float] = None
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    is_valid: bool = True
    validation_errors: Optional[str] = None


class MediaSessionBase(BaseModel):
    """Base schema for MediaSession."""
    session_id: str = Field(..., description="Session identifier")
    interview_id: Optional[str] = Field(None, description="Interview identifier")
    user_id: Optional[str] = Field(None, description="User identifier")
    session_status: str = Field(default="active", description="Session status")
    extra_data: Optional[str] = Field(None, description="Additional metadata as JSON")


class MediaSessionCreate(MediaSessionBase):
    """Schema for creating a MediaSession."""
    pass


class MediaSessionUpdate(BaseModel):
    """Schema for updating a MediaSession."""
    session_status: Optional[str] = Field(None, description="Session status")
    total_chunks: Optional[int] = Field(None, ge=0, description="Total chunks")
    total_duration_seconds: Optional[float] = Field(None, ge=0, description="Total duration")
    extra_data: Optional[str] = Field(None, description="Additional metadata as JSON")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")


class MediaSession(MediaSessionBase):
    """Complete MediaSession schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    total_chunks: int = 0
    total_duration_seconds: float = 0.0
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None


class ChunkUploadRequest(BaseModel):
    """Schema for chunk upload request."""
    session_id: str = Field(..., description="Session identifier")
    sequence_index: int = Field(..., ge=0, description="Chunk sequence index")
    total_chunks: Optional[int] = Field(None, ge=1, description="Expected total chunks")
    question_id: Optional[str] = Field(None, description="Question identifier")
    overlap_seconds: float = Field(default=2.0, ge=0, description="Overlap duration")


class ChunkUploadResponse(BaseModel):
    """Schema for chunk upload response."""
    chunk_id: int = Field(..., description="Created chunk ID")
    sequence_index: int = Field(..., description="Chunk sequence index")
    file_path: str = Field(..., description="Stored file path")
    session_id: str = Field(..., description="Session identifier")
    upload_status: str = Field(..., description="Upload status")
    message: str = Field(..., description="Response message")


class MediaValidationResponse(BaseModel):
    """Schema for media validation response."""
    is_valid: bool = Field(..., description="Validation result")
    errors: List[str] = Field(default=[], description="Validation errors")
    warnings: List[str] = Field(default=[], description="Validation warnings")
    file_info: Dict[str, Any] = Field(default={}, description="File information")


class SessionSummaryResponse(BaseModel):
    """Schema for session summary response."""
    session_id: str
    total_chunks: int
    uploaded_chunks: int
    processed_chunks: int
    failed_chunks: int
    total_duration_seconds: float
    session_status: str
    created_at: datetime
    updated_at: datetime
    chunks: List[MediaChunk] = Field(default=[], description="Session chunks")


class MediaProcessingTaskBase(BaseModel):
    """Base schema for MediaProcessingTask."""
    task_type: str = Field(..., description="Type of processing task")
    chunk_id: int = Field(..., description="Associated chunk ID")
    session_id: str = Field(..., description="Session identifier")
    priority: int = Field(default=0, description="Task priority")


class MediaProcessingTaskCreate(MediaProcessingTaskBase):
    """Schema for creating a MediaProcessingTask."""
    pass


class MediaProcessingTask(MediaProcessingTaskBase):
    """Complete MediaProcessingTask schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    task_id: str
    task_status: str = "pending"
    progress_percentage: float = 0.0
    current_step: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result_data: Optional[str] = None


class HealthCheckResponse(BaseModel):
    """Schema for health check response."""
    status: str = Field(..., description="Service status")
    timestamp: str = Field(..., description="Check timestamp")
    version: str = Field(..., description="Service version")
    uptime_seconds: float = Field(..., description="Service uptime")
    components: Dict[str, str] = Field(..., description="Component statuses")
    metrics: Dict[str, Any] = Field(default={}, description="Service metrics")


class MetricsResponse(BaseModel):
    """Schema for metrics response."""
    total_sessions: int
    active_sessions: int
    total_chunks: int
    pending_chunks: int
    processed_chunks: int
    failed_chunks: int
    storage_used_bytes: int
    average_chunk_size_bytes: float
    processing_queue_size: int


# Error response schemas
class ErrorDetail(BaseModel):
    """Error detail schema."""
    type: str
    message: str
    field: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response schema."""
    error: str
    message: str
    details: Optional[List[ErrorDetail]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DeviceResolution(BaseModel):
    """Schema for device resolution."""
    width: int = Field(..., gt=0, description="Resolution width")
    height: int = Field(..., gt=0, description="Resolution height")
    fps: List[int] = Field(..., description="Supported frame rates")


class MediaDevice(BaseModel):
    """Schema for a media device."""
    device_id: str = Field(..., description="Unique device identifier")
    name: str = Field(..., description="Human-readable device name")
    type: str = Field(..., description="Device type")
    is_default: bool = Field(default=False, description="Whether this is the default device")
    sample_rates: Optional[List[int]] = Field(None, description="Supported sample rates for audio devices")
    channels: Optional[List[int]] = Field(None, description="Supported channel counts for audio devices")
    resolutions: Optional[List[DeviceResolution]] = Field(None, description="Supported resolutions for video devices")
    formats: Optional[List[str]] = Field(None, description="Supported formats")


class DeviceEnumerationResponse(BaseModel):
    """Schema for device enumeration response."""
    audio_inputs: List[MediaDevice] = Field(default=[], description="Available audio input devices")
    audio_outputs: List[MediaDevice] = Field(default=[], description="Available audio output devices") 
    video_inputs: List[MediaDevice] = Field(default=[], description="Available video input devices")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Enumeration timestamp")
    platform: str = Field(..., description="Platform information")


class ChunkUploadEvent(BaseModel):
    """Schema for chunk upload event."""
    event_type: str = Field(default="chunk_uploaded", description="Event type")
    session_id: str = Field(..., description="Session identifier")
    chunk_id: int = Field(..., description="Chunk ID")
    sequence_index: int = Field(..., description="Chunk sequence index")
    file_path: str = Field(..., description="File path")
    file_size_bytes: int = Field(..., description="File size")
    overlap_seconds: float = Field(..., description="Overlap duration")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    question_id: Optional[str] = Field(None, description="Question identifier")
    total_chunks: Optional[int] = Field(None, description="Expected total chunks")
    is_final_chunk: bool = Field(default=False, description="Whether this is the final chunk")


class SessionCompleteEvent(BaseModel):
    """Schema for session completion event."""
    event_type: str = Field(default="session_completed", description="Event type")
    session_id: str = Field(..., description="Session identifier")
    total_chunks: int = Field(..., description="Total chunks uploaded")
    total_duration_seconds: float = Field(..., description="Total session duration")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp") 
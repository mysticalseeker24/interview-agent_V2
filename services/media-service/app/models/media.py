"""
Media Service Database Models
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, Boolean, Index
from sqlalchemy.sql import func

from app.core.database import Base


class MediaSession(Base):
    """
    Media session model to track complete interview sessions.
    """
    __tablename__ = "media_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, index=True, nullable=False)
    interview_id = Column(String(255), index=True, nullable=True)
    user_id = Column(String(255), index=True, nullable=True)
    
    # Session metadata
    total_chunks = Column(Integer, default=0)
    total_duration_seconds = Column(Float, default=0.0)
    session_status = Column(String(50), default="active")  # active, completed, failed, abandoned
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Session metadata
    extra_data = Column(Text, nullable=True)  # JSON string for additional data
    
    def __repr__(self) -> str:
        return f"<MediaSession(session_id='{self.session_id}', status='{self.session_status}')>"


class MediaChunk(Base):
    """
    Media chunk model for storing individual audio chunks.
    """
    __tablename__ = "media_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), index=True, nullable=False)
    question_id = Column(String(255), nullable=True, index=True)
    
    # Chunk ordering and overlap
    sequence_index = Column(Integer, nullable=False)  # 0, 1, 2, ...
    overlap_seconds = Column(Float, default=2.0)
    
    # File information
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size_bytes = Column(Integer, nullable=True)
    file_extension = Column(String(10), nullable=True)
    
    # Audio metadata
    duration_seconds = Column(Float, nullable=True)
    sample_rate = Column(Integer, nullable=True)
    bit_rate = Column(Integer, nullable=True)
    channels = Column(Integer, nullable=True)
    
    # Processing status
    upload_status = Column(String(50), default="pending")  # pending, uploaded, processed, failed
    transcription_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    
    # Quality metrics
    audio_quality_score = Column(Float, nullable=True)  # 0.0 to 1.0
    noise_level = Column(Float, nullable=True)
    silence_percentage = Column(Float, nullable=True)
    
    # Timestamps
    uploaded_at = Column(DateTime, default=func.now(), nullable=False)
    processed_at = Column(DateTime, nullable=True)
    
    # Validation flags
    is_valid = Column(Boolean, default=True)
    validation_errors = Column(Text, nullable=True)  # JSON string for validation errors
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_media_chunks_session_sequence', 'session_id', 'sequence_index'),
        Index('ix_media_chunks_status', 'upload_status', 'transcription_status'),
        Index('ix_media_chunks_uploaded_at', 'uploaded_at'),
    )
    
    def __repr__(self) -> str:
        return (
            f"<MediaChunk(session_id='{self.session_id}', "
            f"sequence_index={self.sequence_index}, "
            f"status='{self.upload_status}')>"
        )


class MediaProcessingTask(Base):
    """
    Model to track background processing tasks for media files.
    """
    __tablename__ = "media_processing_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(255), unique=True, index=True, nullable=False)
    chunk_id = Column(Integer, index=True, nullable=False)
    session_id = Column(String(255), index=True, nullable=False)
    
    # Task information
    task_type = Column(String(50), nullable=False)  # transcription, validation, cleanup
    task_status = Column(String(50), default="pending")  # pending, running, completed, failed, retrying
    priority = Column(Integer, default=0)  # Higher numbers = higher priority
    
    # Progress tracking
    progress_percentage = Column(Float, default=0.0)
    current_step = Column(String(100), nullable=True)
    
    # Error handling
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Result data
    result_data = Column(Text, nullable=True)  # JSON string for task results
    
    def __repr__(self) -> str:
        return (
            f"<MediaProcessingTask(task_id='{self.task_id}', "
            f"type='{self.task_type}', "
            f"status='{self.task_status}')>"
        )

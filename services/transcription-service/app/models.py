from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class Transcription(Base):
    """Model for storing transcription data."""
    __tablename__ = "transcriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    chunk_id = Column(String(255), index=True, nullable=False)
    transcript_text = Column(Text, nullable=False)
    confidence = Column(Float, nullable=True)  # Confidence score from Groq
    
    # Additional fields for enhanced functionality
    session_id = Column(String(255), index=True, nullable=True)
    sequence_index = Column(Integer, nullable=True)  # Order within session
    segments = Column(Text, nullable=True)  # JSON string for detailed segments
    language = Column(String(10), nullable=True)  # Detected language
    duration_seconds = Column(Float, nullable=True)  # Audio duration
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self) -> str:
        return f"<Transcription(id={self.id}, chunk_id='{self.chunk_id}', confidence={self.confidence})>"


class TTSCache(Base):
    """Model for caching TTS generated audio files."""
    __tablename__ = "tts_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)  # Input text
    voice = Column(String(50), nullable=False)  # Voice used
    format = Column(String(10), nullable=False)  # Audio format (mp3, wav, etc.)
    file_path = Column(String(500), nullable=False)  # Path to cached file
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Additional metadata
    file_size_bytes = Column(Integer, nullable=True)  # File size in bytes
    duration_seconds = Column(Float, nullable=True)  # Audio duration
    cache_hit_count = Column(Integer, default=0)  # Number of times accessed
    
    def __repr__(self) -> str:
        return f"<TTSCache(id={self.id}, voice='{self.voice}', format='{self.format}')>"


class MediaChunk(Base):
    """Model for tracking media chunks from the media service."""
    __tablename__ = "media_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), index=True, nullable=False)
    chunk_id = Column(String(255), unique=True, index=True, nullable=False)
    sequence_index = Column(Integer, nullable=False)
    
    # File information
    file_path = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Processing status
    transcription_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    transcription_id = Column(Integer, nullable=True)  # Reference to Transcription
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    processed_at = Column(DateTime, nullable=True)
    
    def __repr__(self) -> str:
        return f"<MediaChunk(id={self.id}, session_id='{self.session_id}', sequence_index={self.sequence_index})>"


class ProcessingTask(Base):
    """Model for tracking background processing tasks."""
    __tablename__ = "processing_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(255), unique=True, index=True, nullable=False)
    task_type = Column(String(50), nullable=False)  # transcription, tts, cleanup
    
    # Task status
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    progress_percentage = Column(Float, default=0.0)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Task data
    input_data = Column(Text, nullable=True)  # JSON string for input
    output_data = Column(Text, nullable=True)  # JSON string for output
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    def __repr__(self) -> str:
        return f"<ProcessingTask(id={self.id}, task_id='{self.task_id}', status='{self.status}')>" 
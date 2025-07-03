"""Transcription model definition."""
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, JSON, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Transcription(Base):
    """Transcription model for storing audio transcription data."""
    __tablename__ = "transcriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)  # Reference to User service
    session_id = Column(Integer, nullable=True)  # Reference to Interview session
    
    # File information
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(50), nullable=False)  # mp3, mp4, wav, etc.
    duration_seconds = Column(Float, nullable=True)
    
    # Transcription data
    transcript_text = Column(Text, nullable=True)
    segments = Column(JSON, nullable=True)  # [{start, end, text, confidence}]
    
    # Processing details
    provider = Column(String(20), nullable=True)  # openai, assemblyai
    model_used = Column(String(50), nullable=True)  # whisper-1, etc.
    confidence_score = Column(Float, nullable=True)
    fallback_used = Column(Integer, default=0)  # Boolean: was fallback used
    
    # Processing status
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    processing_error = Column(Text, nullable=True)
    
    # External IDs
    openai_request_id = Column(String(100), nullable=True)
    assemblyai_transcript_id = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Transcription(id={self.id}, user_id={self.user_id}, status={self.status})>"

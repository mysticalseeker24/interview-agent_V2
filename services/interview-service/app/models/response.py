"""Response model definition."""
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, JSON, Float
from sqlalchemy.orm import relationship

from app.models.base import Base


class Response(Base):
    """User response to interview question model."""
    __tablename__ = "responses"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    
    # Response content
    answer_text = Column(Text, nullable=False)
    audio_file_path = Column(String(500), nullable=True)  # Path to recorded audio
    transcription_data = Column(JSON, nullable=True)  # Transcription metadata
    
    # Timing
    started_at = Column(DateTime, nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    duration_seconds = Column(Float, nullable=True)
    
    # Analysis (populated by Feedback Service)
    keywords_extracted = Column(JSON, default=list)
    sentiment_score = Column(Float, nullable=True)
    fluency_metrics = Column(JSON, nullable=True)  # WPM, filler words, etc.
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    session = relationship("Session", back_populates="responses")
    question = relationship("Question", back_populates="responses")
    
    def __repr__(self):
        return f"<Response(id={self.id}, session_id={self.session_id}, question_id={self.question_id})>"

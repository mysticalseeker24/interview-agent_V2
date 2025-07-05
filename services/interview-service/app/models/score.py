"""Score model for storing per-question performance metrics."""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.models.base import Base


class Score(Base):
    """Model for storing individual question performance scores."""
    
    __tablename__ = "scores"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False, index=True)
    response_id = Column(Integer, ForeignKey("responses.id"), nullable=True, index=True)  # Optional link to specific response
    
    # Performance metrics (0-100 scale)
    correctness = Column(Float, nullable=False, comment="Semantic similarity to ideal answer (0-100)")
    fluency = Column(Float, nullable=False, comment="Speaking fluency score (0-100)")
    depth = Column(Float, nullable=False, comment="Answer depth and detail score (0-100)")
    
    # Additional metrics
    word_count = Column(Integer, nullable=True, comment="Total words in response")
    duration_seconds = Column(Float, nullable=True, comment="Response duration in seconds")
    words_per_minute = Column(Float, nullable=True, comment="Speaking rate (WPM)")
    
    # Metadata
    computed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    computation_version = Column(String(50), default="1.0", comment="Algorithm version for recomputation")
    
    # Relationships
    session = relationship("Session", back_populates="scores")
    question = relationship("Question", back_populates="scores")
    response = relationship("Response", back_populates="scores")
    
    def __repr__(self):
        return f"<Score(session_id={self.session_id}, question_id={self.question_id}, correctness={self.correctness:.1f})>"

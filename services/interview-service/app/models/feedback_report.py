"""Feedback report model for storing generated interview feedback."""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.models.base import Base


class FeedbackReport(Base):
    """Model for storing AI-generated interview feedback reports."""
    
    __tablename__ = "feedback_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False, unique=True, index=True)
    
    # Aggregated metrics
    avg_correctness = Column(Float, nullable=False, comment="Average correctness score (0-100)")
    avg_fluency = Column(Float, nullable=False, comment="Average fluency score (0-100)")
    avg_depth = Column(Float, nullable=False, comment="Average depth score (0-100)")
    overall_score = Column(Float, nullable=False, comment="Weighted overall score (0-100)")
    
    # Percentile rankings
    correctness_percentile = Column(Float, nullable=True, comment="Correctness percentile vs historical data")
    fluency_percentile = Column(Float, nullable=True, comment="Fluency percentile vs historical data")
    depth_percentile = Column(Float, nullable=True, comment="Depth percentile vs historical data")
    overall_percentile = Column(Float, nullable=True, comment="Overall percentile vs historical data")
    
    # AI-generated narrative feedback
    report_text = Column(Text, nullable=False, comment="AI-generated feedback narrative")
    strengths = Column(JSON, nullable=True, comment="List of identified strengths")
    areas_for_improvement = Column(JSON, nullable=True, comment="List of improvement areas")
    recommendations = Column(JSON, nullable=True, comment="Specific recommendations")
    
    # Metadata
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    model_used = Column(String(50), default="o4-mini", comment="AI model used for generation")
    generation_version = Column(String(50), default="1.0", comment="Generation algorithm version")
    
    # Processing metadata
    total_questions = Column(Integer, nullable=False, comment="Number of questions processed")
    processing_time_seconds = Column(Float, nullable=True, comment="Total processing time")
    
    # Relationships
    session = relationship("Session", back_populates="feedback_report")
    
    def __repr__(self):
        return f"<FeedbackReport(session_id={self.session_id}, overall_score={self.overall_score:.1f})>"

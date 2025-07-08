from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from app.models.base import Base

class FeedbackReport(Base):
    __tablename__ = "feedback_reports"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, nullable=False, unique=True, index=True)
    avg_correctness = Column(Float, nullable=False)
    avg_fluency = Column(Float, nullable=False)
    avg_depth = Column(Float, nullable=False)
    overall_score = Column(Float, nullable=False)
    correctness_percentile = Column(Float, nullable=True)
    fluency_percentile = Column(Float, nullable=True)
    depth_percentile = Column(Float, nullable=True)
    overall_percentile = Column(Float, nullable=True)
    report_text = Column(Text, nullable=False)
    strengths = Column(JSON, nullable=True)
    areas_for_improvement = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)
    generated_at = Column(DateTime, nullable=False)
    model_used = Column(String(50), default="o4-mini")
    generation_version = Column(String(50), default="1.0")
    total_questions = Column(Integer, nullable=False)
    processing_time_seconds = Column(Float, nullable=True)

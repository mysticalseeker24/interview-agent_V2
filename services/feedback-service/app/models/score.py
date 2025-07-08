from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class Score(Base):
    __tablename__ = "scores"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, nullable=False, index=True)
    question_id = Column(Integer, nullable=False, index=True)
    response_id = Column(Integer, nullable=True, index=True)
    correctness = Column(Float, nullable=False)
    fluency = Column(Float, nullable=False)
    depth = Column(Float, nullable=False)
    word_count = Column(Integer, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    words_per_minute = Column(Float, nullable=True)
    computed_at = Column(DateTime, nullable=False)
    computation_version = Column(String(50), default="1.0")

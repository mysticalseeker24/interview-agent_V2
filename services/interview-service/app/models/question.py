"""Question model definition."""
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Question(Base):
    """Interview question model."""
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("modules.id"), nullable=False)
    text = Column(Text, nullable=False)
    difficulty = Column(String(20), nullable=False)  # easy, medium, hard
    question_type = Column(String(50), default="open_ended")  # open_ended, coding, scenario
    type = Column(String(50), default="general")  # For vector search (technical, behavioral, etc)
    expected_duration_seconds = Column(Integer, default=300)  # 5 minutes default
    tags = Column(JSON, default=list)  # List of skill tags
    ideal_answer = Column(Text, nullable=True)
    scoring_criteria = Column(JSON, default=dict)  # Scoring rubric
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_synced = Column(DateTime, nullable=True)  # Timestamp when last synced to Pinecone
    domain = Column(String(100), default="general")  # Question domain for vector search
    
    # Relationships
    module = relationship("Module", back_populates="questions")
    responses = relationship("Response", back_populates="question")
    
    def __repr__(self):
        return f"<Question(id={self.id}, module_id={self.module_id}, type={self.question_type})>"

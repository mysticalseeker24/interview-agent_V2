"""Session question tracking model definition."""
from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship

from app.models.base import Base


class SessionQuestion(Base):
    """Track questions asked in each session to avoid repeats."""
    __tablename__ = "session_questions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('sessions.id'), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey('questions.id'), nullable=False)
    question_type = Column(String(50), nullable=False)  # 'main', 'follow_up'
    asked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    source = Column(String(100))  # 'rag', 'llm', 'template'
    
    # Relationships
    session = relationship("Session", back_populates="asked_questions")
    question = relationship("Question")

    def __repr__(self):
        return (f"<SessionQuestion(id={self.id}, session_id={self.session_id}, "
                f"question_id={self.question_id}, type={self.question_type})>")

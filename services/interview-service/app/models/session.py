"""Session model definition."""
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.models.base import Base


class SessionStatus(str, enum.Enum):
    """Session status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class SessionMode(str, enum.Enum):
    """Session mode enumeration."""
    PRACTICE = "practice"
    GENERAL = "general"
    INVITE_ONLY = "invite_only"


class Session(Base):
    """Interview session model."""
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)  # Reference to user from User Service
    module_id = Column(Integer, ForeignKey("modules.id"), nullable=False)
    status = Column(SQLEnum(SessionStatus), default=SessionStatus.PENDING)
    mode = Column(SQLEnum(SessionMode), default=SessionMode.PRACTICE)
    
    # Session data
    queue = Column(JSON, default=list)  # Question IDs in order
    current_question_index = Column(Integer, default=0)
    parsed_resume_data = Column(JSON, nullable=True)  # Resume analysis results
    
    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    estimated_duration_minutes = Column(Integer, default=30)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    module = relationship("Module", back_populates="sessions")
    responses = relationship("Response", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Session(id={self.id}, user_id={self.user_id}, status={self.status})>"

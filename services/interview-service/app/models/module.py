"""Module model definition."""
from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()


class DifficultyLevel(str, enum.Enum):
    """Difficulty levels for interview modules."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class ModuleCategory(str, enum.Enum):
    """Categories for interview modules."""
    SOFTWARE_ENGINEERING = "software_engineering"
    DEVOPS = "devops"
    KUBERNETES = "kubernetes"
    DATA_STRUCTURES = "data_structures"
    MACHINE_LEARNING = "machine_learning"
    AI_ENGINEERING = "ai_engineering"
    LLMS = "llms"
    RESUME_DRIVEN = "resume_driven"


class Module(Base):
    """Interview module model."""
    __tablename__ = "modules"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(SQLEnum(ModuleCategory), nullable=False)
    difficulty = Column(SQLEnum(DifficultyLevel), nullable=False)
    duration_minutes = Column(Integer, default=30)
    is_active = Column(Integer, default=1)  # Using Integer for SQLite compatibility
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    questions = relationship("Question", back_populates="module")
    sessions = relationship("Session", back_populates="module")
    
    def __repr__(self):
        return f"<Module(id={self.id}, title={self.title}, category={self.category})>"

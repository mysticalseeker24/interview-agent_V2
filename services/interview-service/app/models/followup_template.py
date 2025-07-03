"""Follow-up template model definition."""
from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class FollowUpTemplate(Base):
    """Template for generating follow-up questions."""
    __tablename__ = "followup_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    template_text = Column(Text, nullable=False)
    trigger_keywords = Column(JSON, default=list)  # Keywords that trigger this template
    category = Column(String(100), nullable=False)  # clarification, deep_dive, scenario, etc.
    difficulty_modifier = Column(String(20), default="same")  # easier, same, harder
    embedding_vector = Column(JSON, nullable=True)  # For RAG similarity search
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<FollowUpTemplate(id={self.id}, name={self.name}, category={self.category})>"

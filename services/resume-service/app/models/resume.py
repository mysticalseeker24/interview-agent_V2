"""Resume model definition."""
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Resume(Base):
    """Resume model for storing parsed resume data."""
    __tablename__ = "resumes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)  # Reference to User service
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, docx, doc, txt
    
    # Parsed content
    raw_text = Column(Text, nullable=True)
    parsed_data = Column(JSON, nullable=True)  # {skills: [], projects: [], ...}
    
    # Processing status
    processing_status = Column(String(20), default="pending")  # pending, processing, completed, failed
    processing_error = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Resume(id={self.id}, user_id={self.user_id}, filename={self.filename})>"

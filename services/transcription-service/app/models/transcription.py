from sqlalchemy import Column, Integer, String, Text, DateTime, func, JSON, Float
from app.core.database import Base
from datetime import datetime

class Transcription(Base):
    __tablename__ = "transcriptions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(50), index=True, nullable=False)
    question_id = Column(String(50), index=True, nullable=True)
    media_chunk_id = Column(String(50), index=True, nullable=True)  # For chunked transcription
    sequence_index = Column(Integer, nullable=True)  # Order of chunks within session
    transcript_text = Column(Text, nullable=False)
    segments = Column(JSON, nullable=True)  # Detailed timing and word-level info from Whisper
    confidence_score = Column(Float, nullable=True)  # Overall confidence from Whisper
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TTSRequest(Base):
    """Model for Text-to-Speech requests and caching."""
    __tablename__ = "tts_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    voice = Column(String(50), default="alloy")
    format = Column(String(10), default="mp3")
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)  # File size in bytes
    duration = Column(Float)     # Audio duration in seconds
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<TTSRequest(id={self.id}, voice='{self.voice}', created_at='{self.created_at}')>"

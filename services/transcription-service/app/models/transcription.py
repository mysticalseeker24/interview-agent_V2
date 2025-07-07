from sqlalchemy import Column, Integer, String, Text, DateTime, func, JSON, Float
from app.core.database import Base

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

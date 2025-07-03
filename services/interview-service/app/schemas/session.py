"""Session schema definitions."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from app.models.session import SessionStatus, SessionMode


class SessionCreate(BaseModel):
    """Session creation schema."""
    module_id: int
    mode: SessionMode = SessionMode.PRACTICE
    parsed_resume_data: Optional[Dict[str, Any]] = None


class SessionUpdate(BaseModel):
    """Session update schema."""
    status: Optional[SessionStatus] = None
    current_question_index: Optional[int] = None


class QuestionRead(BaseModel):
    """Question response schema for session."""
    id: int
    text: str
    difficulty: str
    question_type: str
    expected_duration_seconds: int
    tags: List[str] = []
    
    class Config:
        from_attributes = True


class SessionResponse(BaseModel):
    """Session response schema."""
    id: int
    user_id: int
    module_id: int
    mode: SessionMode
    status: SessionStatus
    current_question_index: int
    estimated_duration_minutes: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    queue_length: int


class SessionRead(BaseModel):
    """Session response schema."""
    id: int
    user_id: int
    module_id: int
    status: SessionStatus
    mode: SessionMode
    current_question_index: int
    estimated_duration_minutes: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SessionWithModule(SessionRead):
    """Session with module information."""
    module: Dict[str, Any]  # Module data


class NextQuestionResponse(BaseModel):
    """Next question response schema."""
    question: Optional[QuestionRead] = None
    session: SessionRead
    is_complete: bool = False
    remaining_questions: int = 0


class AnswerSubmit(BaseModel):
    """Answer submission schema."""
    answer_text: str
    audio_file_path: Optional[str] = None
    started_at: datetime
    duration_seconds: Optional[float] = None


class AnswerResponse(BaseModel):
    """Answer submission response schema."""
    response_id: int
    session: SessionRead
    next_question: Optional[QuestionRead] = None
    is_complete: bool = False

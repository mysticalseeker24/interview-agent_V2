"""Question schema definitions."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class QuestionBase(BaseModel):
    """Base question schema."""
    text: str
    difficulty: str
    question_type: str = "open_ended"
    expected_duration_seconds: int = 300
    tags: List[str] = []
    ideal_answer: Optional[str] = None
    scoring_criteria: Dict[str, Any] = {}


class QuestionCreate(QuestionBase):
    """Question creation schema."""
    module_id: int


class QuestionUpdate(BaseModel):
    """Question update schema."""
    text: Optional[str] = None
    difficulty: Optional[str] = None
    question_type: Optional[str] = None
    expected_duration_seconds: Optional[int] = None
    tags: Optional[List[str]] = None
    ideal_answer: Optional[str] = None
    scoring_criteria: Optional[Dict[str, Any]] = None


class QuestionResponse(QuestionBase):
    """Question response schema."""
    id: int
    module_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class QuestionRead(QuestionBase):
    """Question response schema."""
    id: int
    module_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class QuestionList(BaseModel):
    """Question list response schema."""
    questions: List[QuestionRead]
    total: int
    page: int
    size: int

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


class QuestionImport(BaseModel):
    """Schema for importing a single question."""
    text: str
    difficulty: str = "medium"
    domain: str = "general"
    type: str = "general"
    question_type: str = "open_ended"
    tags: List[str] = []
    module_id: Optional[int] = None
    ideal_answer: Optional[str] = None
    expected_duration_seconds: int = 300
    scoring_criteria: Dict[str, Any] = {}

    class Config:
        schema_extra = {
            "example": {
                "text": "Tell me about your experience with Python.",
                "difficulty": "medium",
                "domain": "Software Engineering",
                "type": "technical",
                "question_type": "open_ended",
                "tags": ["python", "programming"],
                "module_id": 1,
                "ideal_answer": "A good answer would discuss Python experience...",
                "expected_duration_seconds": 300
            }
        }


class QuestionBatchImport(BaseModel):
    """Schema for importing multiple questions in a batch."""
    questions: List[QuestionImport]
    module_id: Optional[int] = None

    class Config:
        schema_extra = {
            "example": {
                "module_id": 1,
                "questions": [
                    {
                        "text": "Tell me about your experience with Python.",
                        "difficulty": "medium",
                        "domain": "Software Engineering",
                        "type": "technical",
                        "question_type": "open_ended",
                        "tags": ["python", "programming"]
                    },
                    {
                        "text": "How do you handle difficult team situations?",
                        "difficulty": "hard",
                        "domain": "Software Engineering",
                        "type": "behavioral",
                        "question_type": "open_ended",
                        "tags": ["teamwork", "conflict-resolution"]
                    }
                ]
            }
        }


class QuestionSync(BaseModel):
    """Schema for question sync operation."""
    id: int
    text: str
    domain: str = "general"
    type: str = "general"
    difficulty: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "id": 123,
                "text": "Tell me about your experience with Python.",
                "domain": "Software Engineering",
                "type": "technical",
                "difficulty": "medium"
            }
        }


class QuestionSyncBatch(BaseModel):
    """Schema for batch question sync operation."""
    questions: List[QuestionSync]

    class Config:
        schema_extra = {
            "example": {
                "questions": [
                    {
                        "id": 123,
                        "text": "Tell me about your experience with Python.",
                        "domain": "Software Engineering",
                        "type": "technical",
                        "difficulty": "medium"
                    },
                    {
                        "id": 124,
                        "text": "How do you handle difficult team situations?",
                        "domain": "Software Engineering",
                        "type": "behavioral",
                        "difficulty": "hard"
                    }
                ]
            }
        }

"""
Schema definitions for question sync operations.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


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


class QuestionResponse(BaseModel):
    """Schema for question response."""
    id: int
    text: str
    domain: str
    type: str
    difficulty: Optional[str] = None
    similarity_score: Optional[float] = None

    class Config:
        orm_mode = True

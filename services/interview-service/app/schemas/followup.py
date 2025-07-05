"""Follow-up question request/response schemas."""
from typing import List, Optional
from pydantic import BaseModel, Field


class FollowUpRequest(BaseModel):
    """Request schema for follow-up question generation."""
    session_id: int = Field(..., description="Session ID")
    answer_text: str = Field(..., description="Candidate's answer text")
    use_llm: bool = Field(default=False, description="Use GPT-4.1 for refinement")
    max_candidates: int = Field(default=5, description="Maximum candidate questions to consider")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": 123,
                "answer_text": "I have experience with React and Node.js...",
                "use_llm": True,
                "max_candidates": 5
            }
        }


class FollowUpResponse(BaseModel):
    """Response schema for follow-up question generation."""
    follow_up_question: str = Field(..., description="Generated follow-up question")
    source_ids: List[int] = Field(..., description="Source question IDs used")
    generation_method: str = Field(..., description="Method used: 'rag', 'llm', 'template'")
    confidence_score: Optional[float] = Field(None, description="Confidence score if available")

    class Config:
        json_schema_extra = {
            "example": {
                "follow_up_question": "Can you describe a specific challenge you faced while working with React?",
                "source_ids": [45, 67, 89],
                "generation_method": "llm",
                "confidence_score": 0.87
            }
        }


class SessionQuestionCreate(BaseModel):
    """Schema for creating session question records."""
    session_id: int
    question_id: int
    question_type: str = Field(default="follow_up")
    source: str = Field(default="rag")


class SessionQuestionResponse(BaseModel):
    """Response schema for session question records."""
    id: int
    session_id: int
    question_id: int
    question_type: str
    asked_at: str
    source: str

    class Config:
        from_attributes = True

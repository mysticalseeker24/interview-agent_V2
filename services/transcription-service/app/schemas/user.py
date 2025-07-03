"""User schema definitions for Transcription Service."""
from typing import List
from pydantic import BaseModel
from datetime import datetime


class UserRead(BaseModel):
    """User response schema."""
    id: int
    email: str
    first_name: str
    last_name: str
    is_active: bool
    created_at: datetime
    roles: List[str] = []
    
    class Config:
        from_attributes = True

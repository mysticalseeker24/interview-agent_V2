"""User schema definitions for Interview Service."""
from typing import List, Optional
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


class UserProfile(BaseModel):
    """User profile schema."""
    id: int
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    company: Optional[str] = None
    position: Optional[str] = None
    is_active: bool
    created_at: datetime
    roles: List[str] = []

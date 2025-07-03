"""Module schema definitions."""
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.models.module import DifficultyLevel, ModuleCategory


class ModuleBase(BaseModel):
    """Base module schema."""
    title: str
    description: Optional[str] = None
    category: ModuleCategory
    difficulty: DifficultyLevel
    duration_minutes: int = 30


class ModuleCreate(ModuleBase):
    """Module creation schema."""
    pass


class ModuleUpdate(BaseModel):
    """Module update schema."""
    title: Optional[str] = None
    description: Optional[str] = None
    difficulty: Optional[DifficultyLevel] = None
    duration_minutes: Optional[int] = None
    is_active: Optional[bool] = None


class ModuleResponse(ModuleBase):
    """Module response schema."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ModuleRead(ModuleBase):
    """Module response schema."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ModuleList(BaseModel):
    """Module list response schema."""
    modules: List[ModuleRead]
    total: int
    page: int
    size: int

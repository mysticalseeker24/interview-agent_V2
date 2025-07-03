"""Resume schema definitions."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class ResumeParseResult(BaseModel):
    """Resume parsing result schema."""
    skills: List[str]
    projects: List[str]
    experience_years: Optional[int] = None
    education: List[str] = []
    certifications: List[str] = []
    languages: List[str] = []


class ResumeUploadResponse(BaseModel):
    """Resume upload response schema."""
    id: int
    filename: str
    file_size: int
    file_type: str
    processing_status: str
    parsed_data: Optional[ResumeParseResult] = None
    created_at: datetime
    message: str


class ResumeRead(BaseModel):
    """Resume read schema."""
    id: int
    user_id: int
    filename: str
    file_size: int
    file_type: str
    processing_status: str
    parsed_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ResumeList(BaseModel):
    """Resume list response schema."""
    resumes: List[ResumeRead]
    total: int
    page: int
    size: int


class SkillExtraction(BaseModel):
    """Skill extraction result."""
    skill: str
    confidence: float
    category: Optional[str] = None


class ProjectExtraction(BaseModel):
    """Project extraction result."""
    project: str
    description: Optional[str] = None
    technologies: List[str] = []

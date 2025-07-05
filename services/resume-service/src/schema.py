"""
Unified Resume JSON Schema
Single source of truth for all resume data structures.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class ContactInfo(BaseModel):
    """Contact information extracted from resume."""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None


class ExperienceEntry(BaseModel):
    """Work experience entry with enhanced bullet and metrics extraction."""
    position: Optional[str] = None
    company: Optional[str] = None
    start_date: Optional[str] = None  # ISO-8601 format
    end_date: Optional[str] = None    # ISO-8601 or "Present"
    location: Optional[str] = None
    bullets: List[str] = []           # Individual achievement bullets
    metrics: List[str] = []           # Extracted metrics (70%, 10ms, etc.)
    technologies: List[str] = []      # Tech stack mentioned
    raw_text: Optional[str] = None    # Original text for debugging


class ProjectEntry(BaseModel):
    """Project entry with structured data extraction."""
    name: Optional[str] = None
    description: Optional[str] = None
    technologies: List[str] = []
    url: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    bullets: List[str] = []
    metrics: List[str] = []
    raw_text: Optional[str] = None


class EducationEntry(BaseModel):
    """Education entry with comprehensive field extraction."""
    institution: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    gpa: Optional[str] = None
    honors: Optional[str] = None
    raw_text: Optional[str] = None


class SkillCategory(BaseModel):
    """Skills organized by category (Programming, Cloud, etc.)."""
    category: str
    skills: List[str]


class CertificationEntry(BaseModel):
    """Certification with issuer and date information."""
    name: str
    issuer: Optional[str] = None
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    credential_id: Optional[str] = None


class ResumeJSON(BaseModel):
    """
    Unified Resume JSON Schema
    Output format for the text-to-JSON pipeline.
    """
    # Core Information
    contact: ContactInfo = ContactInfo()
    summary: Optional[str] = None
    
    # Main Sections
    experience: List[ExperienceEntry] = []
    projects: List[ProjectEntry] = []
    education: List[EducationEntry] = []
    skills: List[SkillCategory] = []
    certifications: List[CertificationEntry] = []
    achievements: List[str] = []
    
    # Domain Analysis
    domains: List[str] = []           # ["DevOps", "AI Engineering", "Full-Stack"]
    
    # Pipeline Metadata
    raw_text_length: int = 0
    parsing_confidence: float = 0.0   # 0.0 to 1.0
    sections_detected: List[str] = [] # ["experience", "education", "skills"]
    extraction_timestamp: datetime = Field(default_factory=datetime.now)
    
    # Processing Details
    text_extraction_method: str = "pypdf"  # pypdf, tika, docx, etc.
    llm_enhanced: bool = False             # Whether LLM was used for extraction


class ProcessingResult(BaseModel):
    """Result container for the entire pipeline."""
    success: bool
    data: Optional[ResumeJSON] = None  # Changed from resume_json to data
    error_message: Optional[str] = None
    processing_time: float = 0.0  # Changed from processing_time_seconds
    stages_completed: List[str] = []
    
    # File paths for the pipeline workflow
    text_file_path: Optional[str] = None   # Path to extracted .txt file
    json_file_path: Optional[str] = None   # Path to final .json output

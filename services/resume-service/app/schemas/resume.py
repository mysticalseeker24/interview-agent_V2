"""Resume schema definitions."""
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, date


class ContactInfo(BaseModel):
    """Contact information extraction schema."""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    website: Optional[str] = None


class EducationEntry(BaseModel):
    """Education entry schema."""
    institution: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    gpa: Optional[str] = None
    honors: Optional[str] = None


class ExperienceEntry(BaseModel):
    """Work experience entry schema."""
    company: Optional[str] = None
    position: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    technologies: List[str] = []
    achievements: List[str] = []


class ProjectEntry(BaseModel):
    """Project entry schema."""
    name: Optional[str] = None
    description: Optional[str] = None
    technologies: List[str] = []
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    url: Optional[str] = None
    role: Optional[str] = None


class SkillCategory(BaseModel):
    """Skill category schema."""
    category: str
    skills: List[str]
    proficiency_level: Optional[str] = None


class CertificationEntry(BaseModel):
    """Certification entry schema."""
    name: str
    issuer: Optional[str] = None
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    credential_id: Optional[str] = None
    url: Optional[str] = None


class LanguageEntry(BaseModel):
    """Language proficiency schema."""
    language: str
    proficiency: Optional[str] = None  # e.g., "Native", "Fluent", "Conversational"


class ResumeParseResult(BaseModel):
    """Enhanced resume parsing result schema."""
    # Contact Information
    contact_info: ContactInfo = ContactInfo()
    
    # Professional Summary
    summary: Optional[str] = None
    
    # Skills (categorized)
    skills: List[SkillCategory] = []
    
    # Work Experience
    experience: List[ExperienceEntry] = []
    total_experience_years: Optional[float] = None
    
    # Education
    education: List[EducationEntry] = []
    
    # Projects
    projects: List[ProjectEntry] = []
    
    # Certifications
    certifications: List[CertificationEntry] = []
    
    # Languages
    languages: List[LanguageEntry] = []
    
    # Additional Information
    awards: List[str] = []
    publications: List[str] = []
    patents: List[str] = []
    volunteer_experience: List[str] = []
    
    # Domain Analysis
    domains_supported: List[str] = []
    domain_confidence: Dict[str, float] = {}
    
    # Parsing Metadata
    parsing_confidence: Optional[float] = None
    sections_found: List[str] = []
    raw_text_length: Optional[int] = None
    
    # Legacy fields for backward compatibility
    @property
    def skills_list(self) -> List[str]:
        """Backward compatibility: return flat list of skills."""
        all_skills = []
        for category in self.skills:
            all_skills.extend(category.skills)
        return all_skills
    
    @property
    def projects_list(self) -> List[str]:
        """Backward compatibility: return list of project names."""
        return [p.name for p in self.projects if p.name]


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

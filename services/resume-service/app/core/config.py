"""Configuration management for Resume Service."""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database settings
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost/talentsync_resumes"
    
    # File storage settings
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".doc", ".txt"]
    
    # NLP settings
    SPACY_MODEL: str = "en_core_web_lg"
    SKILL_PATTERNS_FILE: str = "patterns/skills.json"
    PROJECT_PATTERNS_FILE: str = "patterns/projects.json"
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8010"]
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    
    # Application settings
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # External service URLs
    USER_SERVICE_URL: str = "http://localhost:8001"
    INTERVIEW_SERVICE_URL: str = "http://localhost:8003"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

"""Configuration management for Transcription Service."""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database settings
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost/talentsync_transcriptions"
    
    # File storage settings
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS: List[str] = [".mp3", ".mp4", ".wav", ".m4a", ".webm", ".ogg"]
    
    # OpenAI settings
    OPENAI_API_KEY: str = "your-openai-api-key-here"
    WHISPER_MODEL: str = "whisper-1"
    CONFIDENCE_THRESHOLD: float = 0.85
    
    # AssemblyAI settings
    ASSEMBLYAI_API_KEY: str = "your-assemblyai-api-key-here"
    ASSEMBLYAI_BASE_URL: str = "https://api.assemblyai.com/v2"
    
    # Media device settings
    ENABLE_DEVICE_ENUMERATION: bool = True
    
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

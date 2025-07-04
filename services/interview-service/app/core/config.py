"""Configuration management for Interview Service."""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database settings
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost/talentsync_interviews"
    
    # Redis settings
    REDIS_URL: str = "redis://localhost:6379/1"
    
    # Pinecone settings
    PINECONE_API_KEY: str = "your-pinecone-api-key-here"
    PINECONE_ENVIRONMENT: str = "us-west1-gcp"
    PINECONE_INDEX_NAME: str = "questions-embeddings"
    
    # OpenAI settings
    OPENAI_API_KEY: str = "your-openai-api-key-here"
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8010"]
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    
    # Application settings
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    PORT: int = 8002
    
    # External service URLs
    USER_SERVICE_URL: str = "http://localhost:8001"
    RESUME_SERVICE_URL: str = "http://localhost:8002"
    TRANSCRIPTION_SERVICE_URL: str = "http://localhost:8005"
    FEEDBACK_SERVICE_URL: str = "http://localhost:8006"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Create global settings instance
settings = get_settings()

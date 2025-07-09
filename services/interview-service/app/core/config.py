"""Configuration management for Interview Service."""
import os
from functools import lru_cache
from typing import List
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Pinecone settings (vector DB only, no relational DB)
    PINECONE_API_KEY: str = "your-pinecone-api-key-here"
    PINECONE_ENVIRONMENT: str = "us-west1-gcp"
    PINECONE_INDEX_NAME: str = "questions-embeddings"
    
    # OpenAI settings for o4-mini (optimized for cost-efficient reasoning)
    OPENAI_API_KEY: str = "your-openai-api-key-here"
    OPENAI_CHAT_MODEL: str = "o4-mini"  # Latest cost-efficient reasoning model
    OPENAI_MAX_TOKENS: int = 300  # Increased for o4-mini's improved context handling
    OPENAI_TEMPERATURE: float = 0.1  # Lower temperature for better reasoning accuracy
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8010"]
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    
    # Application settings
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    PORT: int = 8006
    
    # External service URLs
    USER_SERVICE_URL: str = "http://localhost:8001"
    MEDIA_SERVICE_URL: str = "http://localhost:8002"
    RESUME_SERVICE_URL: str = "http://localhost:8004"
    TRANSCRIPTION_SERVICE_URL: str = "http://localhost:8005"
    FEEDBACK_SERVICE_URL: str = "http://localhost:8006"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"  # Allow extra fields from environment variables
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Create global settings instance
settings = get_settings()

"""Core settings configuration for TalentSync Interview Service."""
import os
from functools import lru_cache
from typing import List, Optional
from urllib.parse import urlparse

from pydantic import HttpUrl, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables with performance optimizations."""
    
    # Service Configuration
    APP_NAME: str = "TalentSync Interview Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    PORT: int = 8006
    
    # Performance & Latency Configuration
    REQUEST_TIMEOUT: float = 5.0  # 5 seconds timeout for external API calls
    FOLLOWUP_GENERATION_TIMEOUT: float = 3.0  # 3 seconds for follow-up generation
    MAX_FOLLOWUP_GENERATION_TIME: float = 5.0  # 5 seconds max
    CACHE_TTL: int = 600  # 10 minutes cache TTL
    SESSION_TTL: int = 3600  # 1 hour session TTL
    
    # Confidence-Based System Configuration
    CONFIDENCE_HIGH_THRESHOLD: float = 0.7  # High confidence threshold for LLM refinement
    CONFIDENCE_MEDIUM_THRESHOLD: float = 0.4  # Medium confidence threshold for contextual generation
    CONFIDENCE_LOW_THRESHOLD: float = 0.2  # Low confidence threshold for RAG fallback
    MAX_CACHE_SIZE: int = 500  # Maximum cache entries
    CACHE_CLEANUP_INTERVAL: int = 300  # Cache cleanup interval in seconds
    
    # Pinecone Vector Database Configuration
    PINECONE_API_KEY: str
    PINECONE_ENV: str = "us-west1-gcp"
    PINECONE_INDEX_NAME: str = "questions-embeddings"
    
    # OpenAI Configuration for o4-mini
    OPENAI_API_KEY: str
    OPENAI_CHAT_MODEL: str = "o4-mini"
    OPENAI_MAX_TOKENS: int = 300
    OPENAI_TEMPERATURE: float = 0.1
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-ada-002"
    
    # Supabase Configuration (Cloud)
    SUPABASE_URL: HttpUrl
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_ANON_KEY: str
    
    # External Service URLs
    RESUME_SERVICE_URL: str = "http://localhost:8004"
    MEDIA_SERVICE_URL: str = "http://localhost:8002"
    TRANSCRIPTION_SERVICE_URL: str = "http://localhost:8005"
    FEEDBACK_SERVICE_URL: str = "http://localhost:8010"
    
    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Circuit Breaker Configuration
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = 60
    CIRCUIT_BREAKER_EXPECTED_EXCEPTION: List[str] = ["HTTPException", "TimeoutError"]
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 1000  # requests per minute
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    # Health Check Configuration
    HEALTH_CHECK_TIMEOUT: float = 1.0  # 1 second health check timeout
    
    # Dataset Configuration
    DATASET_PATH: str = "../../data"
    SUPPORTED_DOMAINS: List[str] = [
        "dsa", "devops", "ai-engineering", "machine-learning", 
        "data-science", "software-engineering", "resume-based"
    ]
    
    @field_validator("PINECONE_API_KEY")
    @classmethod
    def validate_pinecone_key(cls, v):
        """Validate Pinecone API key is provided."""
        if not v or v == "your-pinecone-api-key-here":
            raise ValueError("PINECONE_API_KEY must be provided")
        return v
    
    @field_validator("OPENAI_API_KEY")
    @classmethod
    def validate_openai_key(cls, v):
        """Validate OpenAI API key is provided."""
        if not v or v == "your-openai-api-key-here":
            raise ValueError("OPENAI_API_KEY must be provided")
        return v
    
    @field_validator("SUPABASE_URL")
    @classmethod
    def validate_supabase_url(cls, v):
        """Validate Supabase URL format."""
        if not v or str(v) == "your-supabase-url-here":
            raise ValueError("SUPABASE_URL must be provided")
        return v
    
    @field_validator("SUPABASE_ANON_KEY")
    @classmethod
    def validate_supabase_anon_key(cls, v):
        """Validate Supabase anonymous key is provided."""
        if not v or v == "your-supabase-anon-key-here":
            raise ValueError("SUPABASE_ANON_KEY must be provided")
        return v
    
    @field_validator("SUPABASE_SERVICE_ROLE_KEY")
    @classmethod
    def validate_supabase_service_role_key(cls, v):
        """Validate Supabase service role key is provided."""
        if not v or v == "your-supabase-service-role-key-here":
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY must be provided")
        return v
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance for performance."""
    return Settings()


# Global settings instance
settings = get_settings() 
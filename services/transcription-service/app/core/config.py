import os
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings for TalentSync Transcription Service."""
    
    # App Configuration
    app_name: str = "TalentSync Transcription Service"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, description="Debug mode")
    environment: str = Field(default="development", description="Environment")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8005, description="Server port")
    workers: int = Field(default=1, description="Number of workers")
    
    # Database Configuration
    database_url: str = Field(
        default="sqlite+aiosqlite:///./transcription_service.db",
        description="Database URL"
    )
    database_echo: bool = Field(default=False, description="SQLAlchemy echo")
    
    # Groq API Configuration (for both STT and TTS)
    groq_api_key: str = Field(..., description="Groq API key for STT and TTS")
    groq_base_url: str = Field(
        default="https://api.groq.com/openai/v1",
        description="Groq API base URL"
    )
    groq_stt_model: str = Field(
        default="whisper-large-v3",
        description="Groq Whisper model for Speech-to-Text"
    )
    groq_tts_model: str = Field(
        default="playai-tts",
        description="Groq Play.ai TTS model for Text-to-Speech"
    )
    groq_default_voice: str = Field(
        default="Briggs-PlayAI",
        description="Default TTS voice"
    )
    
    # File Storage Configuration
    upload_dir: Path = Field(
        default=Path("./uploads"),
        description="Directory for uploaded files"
    )
    tts_cache_dir: Path = Field(
        default=Path("./tts_cache"),
        description="Directory for TTS cache files"
    )
    max_file_size: int = Field(
        default=100 * 1024 * 1024,  # 100MB
        description="Maximum file size in bytes"
    )
    allowed_extensions_str: str = Field(
        default="webm,mp3,wav,m4a,ogg",
        description="Allowed file extensions as comma-separated string"
    )
    
    # Chunk Configuration
    default_overlap_seconds: float = Field(
        default=2.0,
        description="Default overlap seconds for chunks"
    )
    max_chunk_duration: int = Field(
        default=300,  # 5 minutes
        description="Maximum chunk duration in seconds"
    )
    
    # Security
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for JWT tokens"
    )
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30,
        description="Access token expiration time"
    )
    
    # Integration URLs
    media_service_url: str = Field(
        default="http://localhost:8003",
        description="Media service URL"
    )
    interview_service_url: str = Field(
        default="http://localhost:8002",
        description="Interview service URL"
    )
    feedback_service_url: str = Field(
        default="http://localhost:8006",
        description="Feedback service URL"
    )
    
    # Monitoring
    enable_metrics: bool = Field(default=True, description="Enable Prometheus metrics")
    metrics_port: int = Field(default=9005, description="Metrics server port")
    
    # Logging
    log_level: str = Field(default="INFO", description="Log level")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format"
    )
    
    # Cleanup Configuration
    cleanup_interval_hours: int = Field(
        default=24,
        description="Interval for cleanup tasks in hours"
    )
    max_file_age_days: int = Field(
        default=7,
        description="Maximum age of files before cleanup"
    )
    
    # Rate Limiting
    max_requests_per_minute: int = Field(
        default=100,
        description="Maximum requests per minute"
    )
    
    # CORS
    cors_origins: str = Field(
        default="*",
        description="CORS origins (comma-separated)"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure directories exist
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.tts_cache_dir.mkdir(parents=True, exist_ok=True)
    
    @property
    def allowed_extensions(self) -> list[str]:
        """Get allowed file extensions as a list."""
        return [ext.strip() for ext in self.allowed_extensions_str.split(",")]
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()


# Global settings instance
settings = get_settings() 
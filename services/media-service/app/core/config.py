"""
TalentSync Media Service Configuration
"""
import os
from pathlib import Path
from typing import Optional, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # App Configuration
    app_name: str = "TalentSync Media Service"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, description="Debug mode")
    environment: str = Field(default="development", description="Environment")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8002, description="Server port")
    workers: int = Field(default=1, description="Number of workers")
    
    # Database Configuration
    database_url: str = Field(
        default="sqlite+aiosqlite:///./media_service.db",
        description="Database URL"
    )
    database_echo: bool = Field(default=False, description="SQLAlchemy echo")
    
    # File Storage Configuration
    upload_dir: Path = Field(
        default=Path("./uploads"),
        description="Directory for uploaded files"
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
    
    # Redis Configuration (for Celery)
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis URL for Celery broker"
    )
    
    # Celery Configuration
    celery_broker_url: str = Field(
        default="redis://localhost:6379/0",
        description="Celery broker URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/0",
        description="Celery result backend URL"
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
    transcription_service_url: str = Field(
        default="http://localhost:8002",
        description="Transcription service URL"
    )
    interview_service_url: str = Field(
        default="http://localhost:8001",
        description="Interview service URL"
    )
    
    # Monitoring
    enable_metrics: bool = Field(default=True, description="Enable Prometheus metrics")
    metrics_port: int = Field(default=9003, description="Metrics server port")
    
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
        default=30,
        description="Maximum file age before cleanup in days"
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure upload directory exists
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    @property
    def allowed_extensions(self) -> list[str]:
        """Get allowed extensions as a list."""
        return [ext.strip() for ext in self.allowed_extensions_str.split(',')]


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings

"""
Configuration management for TalentSync Auth Gateway Service.

This module defines all application settings using Pydantic BaseSettings
for type-safe configuration management with environment variable support.
"""
import os
from functools import lru_cache
from typing import List

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Provides type-safe configuration for the Auth Gateway service
    with validation and default values optimized for high-performance operation.
    """
    
    # Service Configuration
    SERVICE_NAME: str = "talentsync-user-service"
    VERSION: str = "0.1.0"
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    PORT: int = Field(default=8001, description="Service port")
    HOST: str = Field(default="0.0.0.0", description="Service host")
    
    # Supabase Configuration
    SUPABASE_URL: str = Field(..., description="Supabase project URL")
    SUPABASE_ANON_KEY: str = Field(..., description="Supabase anonymous key")
    SUPABASE_SERVICE_ROLE_KEY: str = Field(..., description="Supabase service role key")
    
    # JWT Configuration
    JWT_ALGORITHM: str = Field(default="RS256", description="JWT signing algorithm")
    JWT_EXPIRY_HOURS: int = Field(default=24, description="JWT token expiry in hours")
    
    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Allowed CORS origins"
    )
    ALLOWED_HOSTS: List[str] = Field(
        default=["localhost", "127.0.0.1"],
        description="Allowed hosts for TrustedHostMiddleware"
    )
    
    # Performance Configuration
    MAX_CONNECTIONS: int = Field(default=1000, description="Maximum concurrent connections")
    REQUEST_TIMEOUT: int = Field(default=30, description="Request timeout in seconds")
    RATE_LIMIT_PER_MINUTE: int = Field(default=100, description="Rate limit per minute per user")
    
    # Redis Configuration (for caching and rate limiting)
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    REDIS_MAX_CONNECTIONS: int = Field(default=20, description="Redis connection pool size")
    
    # Health Check Configuration
    HEALTH_CHECK_INTERVAL: int = Field(default=30, description="Health check interval in seconds")
    HEALTH_CHECK_TIMEOUT: int = Field(default=10, description="Health check timeout in seconds")
    
    # Security Configuration
    SECRET_KEY: str = Field(..., description="Application secret key")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Access token expiry in minutes")
    
    @validator("SUPABASE_URL")
    def validate_supabase_url(cls, v: str) -> str:
        """Validate Supabase URL format."""
        if not v.startswith(("https://", "http://")):
            raise ValueError("SUPABASE_URL must be a valid URL")
        return v
    
    @validator("SUPABASE_ANON_KEY")
    def validate_supabase_anon_key(cls, v: str) -> str:
        """Validate Supabase anonymous key format."""
        if not v or len(v) < 10:
            raise ValueError("SUPABASE_ANON_KEY must be a valid key")
        return v
    
    @validator("SUPABASE_SERVICE_ROLE_KEY")
    def validate_supabase_service_role_key(cls, v: str) -> str:
        """Validate Supabase service role key format."""
        if not v or len(v) < 10:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY must be a valid key")
        return v
    
    @validator("SECRET_KEY")
    def validate_secret_key(cls, v: str) -> str:
        """Validate secret key length."""
        if not v or len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.
    
    Returns:
        Settings: Application configuration object
        
    Note:
        Uses lru_cache for performance optimization in high-throughput scenarios.
    """
    return Settings()


# Global settings instance for easy access
settings = get_settings() 
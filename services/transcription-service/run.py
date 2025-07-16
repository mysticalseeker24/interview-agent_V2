#!/usr/bin/env python3
"""
TalentSync Transcription Service Runner

This script runs the transcription service with proper configuration.
"""

import uvicorn
from app.core.config import settings


def main():
    """Run the transcription service."""
    print(f"Starting {settings.app_name} v{settings.app_version}")
    print(f"Environment: {settings.environment}")
    print(f"Debug mode: {settings.debug}")
    print(f"Port: {settings.port}")
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    main() 
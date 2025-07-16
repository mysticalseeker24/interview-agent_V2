#!/usr/bin/env python3
"""
Simple startup script for TalentSync Media Service
"""
import os
import sys
import uvicorn
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import get_settings

settings = get_settings()


def main():
    """Start the media service."""
    print(f"Starting {settings.app_name} v{settings.app_version}")
    print(f"Environment: {settings.environment}")
    print(f"Debug mode: {settings.debug}")
    print(f"Host: {settings.host}")
    print(f"Port: {settings.port}")
    print(f"Database: {settings.database_url}")
    print(f"Upload directory: {settings.upload_dir}")
    print("-" * 50)
    
    # Create upload directory if it doesn't exist
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Start the server
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=True
    )


if __name__ == "__main__":
    main() 
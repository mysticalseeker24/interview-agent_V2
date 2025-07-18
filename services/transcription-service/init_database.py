#!/usr/bin/env python3
"""
Database initialization script for the transcription service.
This script creates all required database tables.
"""

import asyncio
import logging
from pathlib import Path
import sys

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from dotenv import load_dotenv
from app.core.database import init_db, close_db
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Initialize the database."""
    try:
        # Load environment variables
        load_dotenv()
        
        logger.info("Starting database initialization...")
        logger.info(f"Database URL: {settings.database_url}")
        
        # Create engine and drop all tables first to ensure clean state
        from sqlalchemy.ext.asyncio import create_async_engine
        from app.models import Base, Transcription, TTSCache, MediaChunk, ProcessingTask
        
        engine = create_async_engine(
            settings.database_url,
            echo=settings.database_echo,
        )
        
        async with engine.begin() as conn:
            # Drop all tables first
            logger.info("Dropping all existing tables...")
            await conn.run_sync(Base.metadata.drop_all)
            
            # Create all tables
            logger.info("Creating all tables...")
            await conn.run_sync(Base.metadata.create_all)
            
        logger.info("✅ Database initialized successfully!")
        
        # Create required directories
        settings.upload_dir.mkdir(parents=True, exist_ok=True)
        settings.tts_cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ Directories created: {settings.upload_dir}, {settings.tts_cache_dir}")
        
        # Close engine
        await engine.dispose()
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {str(e)}")
        raise
    finally:
        # Close database connections
        await close_db()
        logger.info("Database connections closed")

if __name__ == "__main__":
    asyncio.run(main()) 
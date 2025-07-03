"""
TalentSync Transcription Service - Main FastAPI Application

This service handles hybrid audio transcription using OpenAI Whisper and AssemblyAI,
plus media device enumeration for the frontend.
"""
import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from prometheus_client import make_asgi_app

from app.core.config import get_settings
from app.core.database import engine, create_tables
from app.core.logging import setup_logging
from app.routers import transcription, media, health

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup/shutdown tasks."""
    logger.info("Starting Transcription Service...")
    
    # Create database tables
    await create_tables()
    
    # Create upload directory
    upload_dir = settings.UPLOAD_DIR
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir, exist_ok=True)
        logger.info(f"Created upload directory: {upload_dir}")
    
    logger.info("Transcription Service started successfully")
    yield
    
    logger.info("Shutting down Transcription Service...")
    await engine.dispose()
    logger.info("Transcription Service shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="TalentSync Transcription Service",
    description="Hybrid STT service with OpenAI Whisper and AssemblyAI fallback, plus media device enumeration",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Include routers
app.include_router(health.router)
app.include_router(transcription.router)
app.include_router(media.router)

# Add Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "TalentSync Transcription Service",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8005,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )

"""
TalentSync Interview Service - Main FastAPI Application

This service handles interview modules, session management, and question orchestration.
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
from app.routers import modules, sessions, health, vectors, datasets, followup, feedback

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup/shutdown tasks."""
    logger.info("Starting Interview Service...")
    
    # Create database tables
    await create_tables()
    
    logger.info("Interview Service started successfully")
    yield
    
    logger.info("Shutting down Interview Service...")
    await engine.dispose()
    logger.info("Interview Service shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="TalentSync Interview Service",
    description="Module management and session orchestration service",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)

# Add Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(modules.router, prefix="/api/v1", tags=["modules"])
app.include_router(sessions.router, prefix="/api/v1", tags=["sessions"])
app.include_router(vectors.router, prefix="/api/v1/vectors", tags=["vectors"])
app.include_router(datasets.router, prefix="/api/v1/datasets", tags=["datasets"])
app.include_router(followup.router, tags=["followup"])
app.include_router(feedback.router, tags=["feedback"])


@app.get("/")
async def root():
    """Root endpoint providing service information."""
    return {
        "service": "TalentSync Interview Service",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8002))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.DEBUG,
        log_level="info",
    )

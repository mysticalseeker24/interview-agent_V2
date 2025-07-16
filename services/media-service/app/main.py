"""
TalentSync Media Service - Main Application
"""
import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.database import init_db, close_db
from app.core.logging import setup_logging
from app.routers import media, monitoring

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting TalentSync Media Service...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Database URL: {settings.database_url}")
    logger.info(f"Upload directory: {settings.upload_dir}")
    
    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized successfully")
        
        # Create upload directory if it doesn't exist
        settings.upload_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Upload directory ready: {settings.upload_dir}")
        
        # Initialize services
        logger.info("Services initialized successfully")
        
        logger.info(f"TalentSync Media Service started successfully on {settings.host}:{settings.port}")
        
    except Exception as e:
        logger.error(f"Failed to start service: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down TalentSync Media Service...")
    try:
        await close_db()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="TalentSync Media Service for handling chunked audio uploads and processing",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url}")
    
    # Process request
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} - {process_time:.3f}s")
    
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.debug else "An unexpected error occurred",
            "timestamp": time.time()
        }
    )


# Root endpoint
@app.get("/")
async def root() -> dict:
    """
    Root endpoint.
    
    Returns basic service information.
    """
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "timestamp": time.time(),
        "docs": "/docs" if settings.debug else None,
        "health": "/monitoring/health",
        "metrics": "/monitoring/metrics"
    }


# Health check endpoint
@app.get("/api/v1/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns basic health status.
    """
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "timestamp": time.time()
    }


# Include routers
app.include_router(media.router, prefix="/api/v1")
app.include_router(monitoring.router, prefix="/api/v1")


# Additional endpoints for backward compatibility
@app.get("/health")
async def health_check_legacy():
    """Legacy health check endpoint."""
    return await health_check()


@app.get("/metrics")
async def metrics_legacy():
    """Legacy metrics endpoint."""
    from app.services.monitoring import metrics_service
    return metrics_service.get_prometheus_metrics()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    ) 
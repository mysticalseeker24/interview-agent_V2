"""
FastAPI main application for Media Service.
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
from app.routers import media_router, monitoring_router

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Media Service...")
    
    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized successfully")
        
        # Additional startup tasks could go here
        # - Connect to external services
        # - Start background tasks
        # - Warm up caches
        
        logger.info("Media Service startup completed")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Media Service...")
    
    try:
        # Close database connections
        await close_db()
        logger.info("Database connections closed")
        
        # Additional cleanup tasks could go here
        # - Close external connections
        # - Stop background tasks
        # - Clean up resources
        
        logger.info("Media Service shutdown completed")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    TalentSync Media Service for chunked audio recording and management.
    
    ## Features
    
    * **Chunked Upload**: Support for uploading audio in chunks with overlap
    * **Session Management**: Track complete interview sessions
    * **Background Processing**: Async processing with Celery workers
    * **Quality Validation**: Audio quality checks and validation
    * **Monitoring**: Health checks and Prometheus metrics
    * **Storage Management**: Efficient file storage and cleanup
    
    ## Usage
    
    1. Create a session with `POST /media/session`
    2. Upload chunks with `POST /media/chunk-upload`
    3. Monitor progress with `GET /media/session/{session_id}/summary`
    4. Check for gaps with `GET /media/session/{session_id}/gaps`
    
    ## Integration
    
    The service integrates with:
    - **Transcription Service**: Triggers transcription after upload
    - **Interview Service**: Receives session completion events
    - **Redis**: For background task queuing
    - **Prometheus**: For monitoring and metrics
    """,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(media_router)
app.include_router(monitoring_router)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception on {request.method} {request.url}: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "detail": str(exc) if settings.debug else "Contact support for assistance"
        }
    )


# Root endpoint
@app.get("/")
async def root() -> dict:
    """Root endpoint with service information."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "environment": settings.environment,
        "docs_url": "/docs" if settings.debug else None,
        "health_url": "/health",
        "metrics_url": "/metrics"
    }


# Additional middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests."""
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url}")
    
    # Process request
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(
        f"Response: {response.status_code} "
        f"({process_time:.3f}s) "
        f"{request.method} {request.url}"
    )
    
    # Add custom headers
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Service"] = settings.app_name
    
    return response


if __name__ == "__main__":
    import uvicorn
    import time
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=1 if settings.debug else settings.workers,
        log_level=settings.log_level.lower(),
        access_log=True
    )

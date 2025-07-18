import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from .core.config import settings
from .core.database import init_db, close_db
from .routers import transcribe, tts, interview, personas
from .services.playai_tts import GroqTTSClient
groq_tts_client = GroqTTSClient()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format=settings.log_format
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    
    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise
    
    # Create directories
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.tts_cache_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Directories created: {settings.upload_dir}, {settings.tts_cache_dir}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down transcription service...")
    try:
        await close_db()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {str(e)}")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="TalentSync Transcription Service with Groq STT and TTS",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests and their processing time."""
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url}")
    
    # Process request
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} - {process_time:.3f}s")
    
    # Add processing time to response headers
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "timestamp": time.time()
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """HTTP exception handler."""
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP error",
            "message": exc.detail,
            "status_code": exc.status_code,
            "timestamp": time.time()
        }
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "status": "running",
        "docs": "/docs" if settings.debug else None,
        "health": "/health"
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Basic health checks
        health_status = {
            "status": "healthy",
            "timestamp": time.time(),
            "version": settings.app_version,
            "components": {
                "database": "healthy",  # Would check actual DB connection
                "groq_stt_api": "unknown",  # Would check Groq STT API
                "groq_tts_api": "unknown"  # Would check Groq TTS API
            }
        }
        
        # Check Groq STT API health
        try:
            from .services.groq_stt import GroqSTTClient
            groq_client = GroqSTTClient()
            groq_health = await groq_client.health_check()
            health_status["components"]["groq_stt_api"] = groq_health["status"]
        except Exception as e:
            logger.warning(f"Groq STT API health check failed: {str(e)}")
            health_status["components"]["groq_stt_api"] = "unhealthy"
        
        # Check Groq TTS API health
        try:
            groq_tts_health = await groq_tts_client.health_check()
            health_status["components"]["groq_tts_api"] = groq_tts_health["status"]
        except Exception as e:
            logger.warning(f"Groq TTS API health check failed: {str(e)}")
            health_status["components"]["groq_tts_api"] = "unhealthy"
        
        # Overall status
        if any(status == "unhealthy" for status in health_status["components"].values()):
            health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": time.time(),
            "version": settings.app_version,
            "error": str(e)
        }


# Include routers
app.include_router(transcribe.router)
app.include_router(tts.router)
app.include_router(interview.router)
app.include_router(personas.router)

# Mount static files for TTS cache
app.mount("/tts/files", StaticFiles(directory=str(settings.tts_cache_dir)), name="tts_files")

# Legacy endpoints for backward compatibility
@app.get("/api/v1/health")
async def health_check_legacy():
    """Legacy health check endpoint."""
    return await health_check()


@app.get("/metrics")
async def metrics_legacy():
    """Legacy metrics endpoint."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "uptime": time.time(),  # Would calculate actual uptime
        "endpoints": {
            "transcription": "/api/v1/transcribe",
            "tts": "/api/v1/tts",
            "interview": "/api/v1/interview",
            "health": "/health"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    ) 
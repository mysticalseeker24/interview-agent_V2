"""Main application for Resume Service using JSON file storage."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.routers import resume, health

settings = get_settings()

# Setup logging
setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Resume Service with JSON file storage...")
    logger.info("No database initialization required for JSON storage")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Resume Service...")


# Create FastAPI app
app = FastAPI(
    title="TalentSync Resume Service",
    description="Resume parsing and skill extraction service with JSON file storage",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle ValueError exceptions."""
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )


@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 exceptions."""
    return JSONResponse(
        status_code=404,
        content={"detail": "Resource not found"}
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle internal server errors."""
    logger.error(f"Internal server error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Include routers
app.include_router(resume.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "TalentSync Resume Service",
        "version": "1.0.0",
        "storage": "JSON files",
        "status": "healthy"
    }


@app.get("/api/v1/info")
async def service_info():
    """Service information endpoint."""
    return {
        "service": "resume-service",
        "version": "1.0.0",
        "storage_type": "json_files",
        "supported_formats": ["pdf", "docx", "doc", "txt"],
        "max_file_size_mb": settings.MAX_FILE_SIZE // (1024 * 1024),
        "endpoints": {
            "upload": "/api/v1/resume/parse",
            "list": "/api/v1/resume/",
            "get": "/api/v1/resume/{resume_id}",
            "delete": "/api/v1/resume/{resume_id}",
            "data": "/api/v1/resume/{resume_id}/data",
            "internal": "/api/v1/resume/internal/{resume_id}/data",
            "stats": "/api/v1/resume/admin/stats"
        }
    }

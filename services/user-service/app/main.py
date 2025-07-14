"""
Main FastAPI application for TalentSync Auth Gateway Service.

High-performance authentication and user management service optimized
for 1000+ RPS with proper middleware, CORS, and error handling.
"""
import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from app.core.settings import settings
from app.core.logging import setup_logging
from app.routers import auth, users

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Prometheus metrics for monitoring
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"]
)

# Global variables for application state
app_start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    
    Handles initialization and cleanup of application resources
    for high-performance operation.
    """
    # Startup
    logger.info(f"Starting {settings.SERVICE_NAME} v{settings.VERSION}")
    logger.info(f"Service will run on {settings.HOST}:{settings.PORT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Log level: {settings.LOG_LEVEL}")
    
    # Initialize Supabase service
    try:
        from app.services.supabase_service import supabase_service
        logger.info("Supabase service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase service: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.SERVICE_NAME}")
    # Add any cleanup logic here if needed


# Create FastAPI application with performance optimizations
app = FastAPI(
    title=settings.SERVICE_NAME,
    description="High-performance authentication and user management service for TalentSync",
    version=settings.VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Add TrustedHost middleware for security
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Add processing time header and collect metrics.
    
    Measures request latency and collects Prometheus metrics
    for monitoring high-performance operation.
    """
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Add custom header
    response.headers["X-Process-Time"] = str(process_time)
    
    # Record metrics
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(process_time)
    
    # Log slow requests
    if process_time > 1.0:  # Log requests taking more than 1 second
        logger.warning(
            f"Slow request: {request.method} {request.url.path} "
            f"took {process_time:.3f}s"
        )
    
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled errors.
    
    Provides consistent error responses and logging for
    high-performance error handling.
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "code": "INTERNAL_ERROR",
            "details": {"message": "An unexpected error occurred"}
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    HTTP exception handler for consistent error responses.
    
    Provides standardized error responses for HTTP exceptions
    with proper logging and monitoring.
    """
    logger.warning(
        f"HTTP exception: {exc.status_code} - {exc.detail} "
        f"for {request.method} {request.url.path}"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "code": f"HTTP_{exc.status_code}",
            "details": {"method": request.method, "path": request.url.path}
        }
    )


# Include routers
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(users.router, prefix="/users", tags=["users"])


@app.get(
    "/",
    summary="Service information",
    description="Get service information and health status",
    responses={
        200: {
            "description": "Service information",
            "content": {
                "application/json": {
                    "example": {
                        "service": "talentsync-user-service",
                        "version": "0.1.0",
                        "status": "running",
                        "uptime": 123.45
                    }
                }
            }
        }
    }
)
async def root() -> Dict[str, Any]:
    """
    Get service information and health status.
    
    Returns:
        Dict[str, Any]: Service information including uptime
    """
    uptime = time.time() - app_start_time
    return {
        "service": settings.SERVICE_NAME,
        "version": settings.VERSION,
        "status": "running",
        "uptime": round(uptime, 2),
        "debug": settings.DEBUG,
    }


@app.get(
    "/health",
    summary="Health check",
    description="Health check endpoint for load balancers and monitoring",
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "service": "talentsync-user-service",
                        "timestamp": "2024-01-01T00:00:00Z"
                    }
                }
            }
        }
    }
)
async def health() -> Dict[str, Any]:
    """
    Health check endpoint for monitoring and load balancers.
    
    Returns:
        Dict[str, Any]: Health status information
    """
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": settings.VERSION,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


@app.get(
    "/metrics",
    summary="Prometheus metrics",
    description="Prometheus metrics endpoint for monitoring",
    responses={
        200: {
            "description": "Prometheus metrics",
            "content": {
                "text/plain": {
                    "example": "# HELP http_requests_total Total HTTP requests\n# TYPE http_requests_total counter"
                }
            }
        }
    }
)
async def metrics():
    """
    Prometheus metrics endpoint for monitoring.
    
    Returns:
        Response: Prometheus metrics in text format
    """
    from fastapi.responses import Response
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.get(
    "/ready",
    summary="Readiness check",
    description="Readiness check for Kubernetes deployments",
    responses={
        200: {"description": "Service is ready to accept traffic"},
        503: {"description": "Service is not ready"},
    }
)
async def ready() -> Dict[str, str]:
    """
    Readiness check for Kubernetes deployments.
    
    Returns:
        Dict[str, str]: Readiness status
    """
    # Add any readiness checks here (database connectivity, etc.)
    try:
        # Test Supabase connectivity
        from app.services.supabase_service import supabase_service
        # This is a simple check - in production you might want to test actual queries
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
        workers=1,  # For development - use multiple workers in production
    ) 
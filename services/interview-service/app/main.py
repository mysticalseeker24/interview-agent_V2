"""Main FastAPI application for TalentSync Interview Service with performance optimizations."""
import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.core.settings import settings
from app.dependencies.auth import get_current_user
from app.routers import health, modules, sessions, followup, vector_search
from app.services.pinecone_service import PineconeService
from app.services.followup_service import DynamicFollowUpService
from app.services.session_service import SessionService

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("interview_service.log")
    ]
)

logger = logging.getLogger(__name__)

# Global service instances
pinecone_service: PineconeService = None
followup_service: DynamicFollowUpService = None
session_service: SessionService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown."""
    global pinecone_service, followup_service, session_service
    
    # Startup
    logger.info("Starting TalentSync Interview Service...")
    
    try:
        # Initialize services
        pinecone_service = PineconeService()
        followup_service = DynamicFollowUpService()
        session_service = SessionService()
        
        # Try to connect to Redis (optional for development)
        try:
            await session_service.connect()
            logger.info("Redis connection established successfully")
        except Exception as redis_error:
            logger.warning(f"Redis connection failed: {str(redis_error)}")
            logger.warning("Session management will be limited. Service will continue without Redis.")
        
        logger.info("All services initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down TalentSync Interview Service...")
    
    try:
        # Disconnect from Redis if connected
        if session_service and session_service.redis_client:
            await session_service.disconnect()
        
        logger.info("All services shut down successfully")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")


# Create FastAPI application with performance optimizations
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="High-performance AI-powered interview simulation service",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add Gzip compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Performance monitoring middleware
@app.middleware("http")
async def performance_middleware(request: Request, call_next):
    """Middleware to track request performance."""
    start_time = time.time()
    
    # Add request ID for tracing
    request_id = f"{int(start_time * 1000)}"
    request.state.request_id = request_id
    
    try:
        response = await call_next(request)
        
        # Calculate processing time
        process_time = (time.time() - start_time) * 1000
        
        # Add performance headers
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = request_id
        
        # Log slow requests
        if process_time > 1000:  # Log requests taking more than 1 second
            logger.warning(
                f"Slow request: {request.method} {request.url.path} "
                f"took {process_time:.2f}ms"
            )
        
        return response
        
    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        logger.error(
            f"Request failed: {request.method} {request.url.path} "
            f"took {process_time:.2f}ms - {str(e)}"
        )
        raise


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    logger.error(
        f"Unhandled exception in request {request_id}: {str(exc)}",
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred",
            "request_id": request_id,
            "timestamp": time.time()
        }
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, Any]:
    """Comprehensive health check for all services."""
    start_time = time.time()
    
    health_status = {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": time.time(),
        "uptime_seconds": time.time() - start_time,
        "dependencies": {}
    }
    
    try:
        # Check Pinecone service
        if pinecone_service:
            pinecone_health = await pinecone_service.health_check()
            health_status["dependencies"]["pinecone"] = pinecone_health["status"]
        
        # Check follow-up service
        if followup_service:
            followup_health = await followup_service.health_check()
            health_status["dependencies"]["followup_service"] = followup_health["status"]
        
        # Check session service
        if session_service:
            session_health = await session_service.health_check()
            health_status["dependencies"]["session_service"] = session_health["status"]
        
        # Overall health status
        all_healthy = all(
            status == "healthy" 
            for status in health_status["dependencies"].values()
        )
        
        if not all_healthy:
            health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        health_status["status"] = "unhealthy"
        health_status["error"] = str(e)
        return health_status


# Performance metrics endpoint
@app.get("/metrics", tags=["Monitoring"])
async def get_metrics() -> Dict[str, Any]:
    """Get performance metrics for all services including confidence-based system."""
    metrics = {
        "service": settings.APP_NAME,
        "timestamp": time.time(),
        "services": {},
        "confidence_system": {}
    }
    
    try:
        # Pinecone metrics
        if pinecone_service:
            pinecone_stats = await pinecone_service.get_index_stats()
            metrics["services"]["pinecone"] = {
                "index_stats": pinecone_stats,
                "health": await pinecone_service.health_check()
            }
        
        # Follow-up service metrics with confidence analysis
        if followup_service:
            followup_metrics = followup_service.get_performance_metrics()
            
            # Add confidence-based system metrics
            confidence_metrics = {
                "cache_performance": {
                    "hit_rate": followup_metrics.get("cache_hit_rate", 0),
                    "total_requests": followup_metrics.get("total_requests", 0),
                    "cache_hits": followup_metrics.get("cache_hits", 0),
                    "cache_misses": followup_metrics.get("cache_misses", 0)
                },
                "generation_performance": {
                    "avg_generation_time_ms": followup_metrics.get("avg_generation_time_ms", 0),
                    "p95_generation_time_ms": followup_metrics.get("p95_generation_time_ms", 0),
                    "p99_generation_time_ms": followup_metrics.get("p99_generation_time_ms", 0)
                },
                "confidence_thresholds": {
                    "high_threshold": settings.CONFIDENCE_HIGH_THRESHOLD,
                    "medium_threshold": settings.CONFIDENCE_MEDIUM_THRESHOLD,
                    "low_threshold": settings.CONFIDENCE_LOW_THRESHOLD
                }
            }
            
            metrics["services"]["followup_service"] = {
                "performance": followup_metrics,
                "health": await followup_service.health_check(),
                "confidence_system": confidence_metrics
            }
            
            # Add confidence system metrics to top level
            metrics["confidence_system"] = confidence_metrics
        
        # Session service metrics
        if session_service:
            metrics["services"]["session_service"] = {
                "performance": session_service.get_performance_metrics(),
                "health": await session_service.health_check()
            }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")


# Include routers
app.include_router(
    health.router,
    prefix="/api/v1/health",
    tags=["Health"]
)

app.include_router(
    modules.router,
    prefix="/api/v1/modules",
    tags=["Modules"]
)

app.include_router(
    sessions.router,
    prefix="/api/v1/sessions",
    tags=["Sessions"]
)

app.include_router(
    followup.router,
    prefix="/api/v1/followup",
    tags=["Follow-up Questions"]
)

app.include_router(
    vector_search.router,
    prefix="/api/v1/search",
    tags=["Vector Search"]
)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with service information."""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics"
    }


# Dependency injection for services
def get_pinecone_service() -> PineconeService:
    """Get Pinecone service instance."""
    if not pinecone_service:
        raise HTTPException(status_code=503, detail="Pinecone service not available")
    return pinecone_service


def get_followup_service() -> DynamicFollowUpService:
    """Get follow-up service instance."""
    if not followup_service:
        raise HTTPException(status_code=503, detail="Follow-up service not available")
    return followup_service


def get_session_service() -> SessionService:
    """Get session service instance."""
    if not session_service:
        raise HTTPException(status_code=503, detail="Session service not available")
    return session_service


# Export services for use in routers
app.state.pinecone_service = get_pinecone_service
app.state.followup_service = get_followup_service
app.state.session_service = get_session_service


if __name__ == "__main__":
    # Run with performance optimizations
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=4,  # Multiple workers for high throughput
        worker_class="uvicorn.workers.UvicornWorker",
        access_log=True,
        log_level=settings.LOG_LEVEL.lower(),
        timeout_keep_alive=30,
        timeout_graceful_shutdown=30
    ) 
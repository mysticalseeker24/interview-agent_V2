"""
Health check endpoints for the Transcription Service.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
from datetime import datetime

from ..core.database import get_db
from ..core.config import get_settings
from ..schemas.health import HealthResponse, HealthStatus
from ..services.transcription_service import TranscriptionService
from ..services.media_device_service import MediaDeviceService

router = APIRouter(
    prefix="/health",
    tags=["health"],
    responses={200: {"description": "Service is healthy"}},
)

logger = logging.getLogger(__name__)


@router.get("/", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """
    Comprehensive health check for the Transcription Service.
    
    Checks:
    - Database connectivity
    - External API availability (OpenAI, AssemblyAI)
    - Media device enumeration
    - Service configuration
    """
    try:
        health_status = HealthStatus.HEALTHY
        checks = {}
        
        # Check database connectivity
        try:
            db.execute(text("SELECT 1"))
            checks["database"] = {"status": "healthy", "message": "Database connection successful"}
        except Exception as e:
            checks["database"] = {"status": "unhealthy", "message": f"Database connection failed: {str(e)}"}
            health_status = HealthStatus.UNHEALTHY
        
        # Check external APIs
        try:
            transcription_service = TranscriptionService()
            api_check = await transcription_service.health_check()
            checks["external_apis"] = api_check
            if not api_check.get("healthy", False):
                health_status = HealthStatus.DEGRADED
        except Exception as e:
            checks["external_apis"] = {"status": "unhealthy", "message": f"External API check failed: {str(e)}"}
            health_status = HealthStatus.UNHEALTHY
        
        # Check media device service
        try:
            media_service = MediaDeviceService()
            device_check = await media_service.health_check()
            checks["media_devices"] = device_check
            if not device_check.get("healthy", False):
                health_status = HealthStatus.DEGRADED
        except Exception as e:
            checks["media_devices"] = {"status": "unhealthy", "message": f"Media device check failed: {str(e)}"}
            health_status = HealthStatus.DEGRADED
        
        # Check configuration
        settings = get_settings()
        config_healthy = all([
            settings.DATABASE_URL,
            settings.OPENAI_API_KEY,
            settings.ASSEMBLYAI_API_KEY,
        ])
        
        if config_healthy:
            checks["configuration"] = {"status": "healthy", "message": "All required configuration present"}
        else:
            checks["configuration"] = {"status": "unhealthy", "message": "Missing required configuration"}
            health_status = HealthStatus.UNHEALTHY
        
        response = HealthResponse(
            status=health_status,
            timestamp=datetime.utcnow(),
            service="transcription-service",
            version="1.0.0",
            checks=checks
        )
        
        # Return appropriate HTTP status code
        status_code = status.HTTP_200_OK
        if health_status == HealthStatus.UNHEALTHY:
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        elif health_status == HealthStatus.DEGRADED:
            status_code = status.HTTP_200_OK  # Still return 200 for degraded
        
        return response
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Health check failed: {str(e)}"
        )


@router.get("/ready", response_model=dict)
async def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness probe for container orchestration.
    
    Returns 200 if service is ready to receive traffic.
    """
    try:
        # Basic database connectivity check
        db.execute(text("SELECT 1"))
        
        return {
            "status": "ready",
            "timestamp": datetime.utcnow(),
            "service": "transcription-service"
        }
        
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )


@router.get("/live", response_model=dict)
async def liveness_check():
    """
    Liveness probe for container orchestration.
    
    Returns 200 if service is alive and running.
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow(),
        "service": "transcription-service"
    }

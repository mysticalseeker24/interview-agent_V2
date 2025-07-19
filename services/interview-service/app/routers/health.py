"""Health check router for TalentSync Interview Service."""
import time
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from app.core.settings import settings
from app.schemas.interview import HealthCheck, ServiceHealth
from app.services.pinecone_service import PineconeService
from app.services.followup_service import DynamicFollowUpService
from app.services.session_service import SessionService

router = APIRouter()


@router.get("/", response_model=HealthCheck)
async def health_check() -> HealthCheck:
    """Comprehensive health check for all services."""
    start_time = time.time()
    
    health_status = HealthCheck(
        status="healthy",
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        timestamp=time.time(),
        uptime_seconds=time.time() - start_time,
        dependencies={}
    )
    
    return health_status


@router.get("/detailed", response_model=Dict[str, Any])
async def detailed_health_check() -> Dict[str, Any]:
    """Detailed health check with individual service status."""
    detailed_status = {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": time.time(),
        "overall_status": "healthy",
        "services": {}
    }
    
    try:
        # Check Pinecone service
        pinecone_service = PineconeService()
        pinecone_health = await pinecone_service.health_check()
        detailed_status["services"]["pinecone"] = pinecone_health
        
        # Check follow-up service
        followup_service = DynamicFollowUpService()
        followup_health = await followup_service.health_check()
        detailed_status["services"]["followup_service"] = followup_health
        
        # Check session service
        session_service = SessionService()
        await session_service.connect()
        session_health = await session_service.health_check()
        detailed_status["services"]["session_service"] = session_health
        await session_service.disconnect()
        
        # Determine overall status
        all_healthy = all(
            service.get("status") == "healthy" 
            for service in detailed_status["services"].values()
        )
        
        if not all_healthy:
            detailed_status["overall_status"] = "degraded"
        
        return detailed_status
        
    except Exception as e:
        detailed_status["overall_status"] = "unhealthy"
        detailed_status["error"] = str(e)
        return detailed_status


@router.get("/ping")
async def ping() -> Dict[str, str]:
    """Simple ping endpoint for load balancers."""
    return {"status": "pong", "service": settings.APP_NAME}


@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """Readiness check for Kubernetes deployments."""
    try:
        # Quick checks for essential services
        pinecone_service = PineconeService()
        pinecone_health = await pinecone_service.health_check()
        
        session_service = SessionService()
        await session_service.connect()
        session_health = await session_service.health_check()
        await session_service.disconnect()
        
        if pinecone_health["status"] == "healthy" and session_health["status"] == "healthy":
            return {"status": "ready", "timestamp": time.time()}
        else:
            return {"status": "not_ready", "timestamp": time.time()}
            
    except Exception as e:
        return {"status": "not_ready", "error": str(e), "timestamp": time.time()}


@router.get("/live")
async def liveness_check() -> Dict[str, str]:
    """Liveness check for Kubernetes deployments."""
    return {"status": "alive", "service": settings.APP_NAME} 
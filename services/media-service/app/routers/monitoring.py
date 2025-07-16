"""
Monitoring API routes for health checks and metrics.
"""
import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, Response, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.media import HealthCheckResponse, MetricsResponse
from app.services.monitoring import metrics_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.
    
    Returns comprehensive health status including:
    - Service status
    - Database connectivity
    - Storage accessibility
    - Memory usage
    - Uptime
    """
    try:
        async with get_db() as db:
            health_status = await metrics_service.get_health_status(db)
            return health_status
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "unknown"
        }


@router.get("/metrics/prometheus")
async def prometheus_metrics() -> Response:
    """
    Prometheus metrics endpoint.
    
    Returns metrics in Prometheus format for monitoring systems.
    """
    try:
        metrics = metrics_service.get_prometheus_metrics()
        return Response(
            content=metrics,
            media_type="text/plain",
            headers={"Cache-Control": "no-cache"}
        )
    except Exception as e:
        logger.error(f"Error generating Prometheus metrics: {e}")
        return Response(
            content=f"# Error generating metrics: {e}",
            media_type="text/plain",
            status_code=500
        )


@router.get("/prometheus")
async def prometheus_metrics() -> str:
    """
    Prometheus metrics endpoint (alternative).
    
    Returns metrics in Prometheus format as plain text.
    """
    try:
        return metrics_service.get_prometheus_metrics()
    except Exception as e:
        logger.error(f"Error generating Prometheus metrics: {e}")
        return f"# Error generating metrics: {e}"


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get comprehensive service metrics.
    
    Returns detailed metrics including:
    - Session statistics
    - Chunk processing statistics
    - Storage usage
    - Processing queue status
    """
    try:
        metrics = await metrics_service.collect_database_metrics(db)
        return metrics
    except Exception as e:
        logger.error(f"Error collecting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 
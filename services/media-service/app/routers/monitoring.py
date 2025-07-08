"""
Health check and monitoring API routes.
"""
import logging
import time
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, Response, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.media import HealthCheckResponse, MetricsResponse
from app.services.monitoring import metrics_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["monitoring"])


@router.get("/health")
async def health_check(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Health check endpoint.
    
    Returns comprehensive health status including:
    - Service status
    - Database connectivity
    - Storage accessibility
    - Redis connectivity
    - Basic metrics
    """
    try:
        health_data = await metrics_service.get_health_status(db)
        return health_data
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "unknown",
            "error": str(e),
            "components": {}
        }


@router.get("/metrics/prometheus")
async def prometheus_metrics() -> Response:
    """
    Prometheus metrics endpoint.
    
    Returns metrics in Prometheus text format for scraping by
    monitoring systems.
    """
    try:
        metrics_data = metrics_service.get_prometheus_metrics()
        return Response(
            content=metrics_data,
            media_type="text/plain"
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
    Prometheus metrics endpoint.
    
    Returns metrics in Prometheus format for scraping.
    """
    try:
        return metrics_service.get_prometheus_metrics()
    except Exception as e:
        logger.error(f"Error generating Prometheus metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    JSON metrics endpoint.
    
    Returns key metrics in JSON format for dashboard consumption.
    """
    try:
        db_metrics = await metrics_service.collect_database_metrics(db)
        
        return {
            "total_sessions": db_metrics.get("sessions", {}).get("total", 0),
            "active_sessions": db_metrics.get("sessions", {}).get("active", 0),
            "total_chunks": db_metrics.get("chunks", {}).get("total", 0),
            "pending_chunks": db_metrics.get("chunks", {}).get("processing", 0),
            "processed_chunks": db_metrics.get("chunks", {}).get("uploaded", 0),
            "failed_chunks": db_metrics.get("chunks", {}).get("failed", 0),
            "storage_used_bytes": db_metrics.get("storage", {}).get("total_bytes", 0),
            "average_chunk_size_bytes": db_metrics.get("storage", {}).get("average_chunk_size", 0),
            "processing_queue_size": db_metrics.get("processing", {}).get("pending_tasks", 0),
        }
    except Exception as e:
        logger.error(f"Error collecting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

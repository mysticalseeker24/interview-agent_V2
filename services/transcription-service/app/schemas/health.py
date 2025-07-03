"""Health check schema definitions."""
from pydantic import BaseModel
from enum import Enum
from datetime import datetime
from typing import Dict, Any


class HealthStatus(str, Enum):
    """Health status enumeration."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: HealthStatus
    timestamp: datetime
    service: str
    version: str
    checks: Dict[str, Any]
    assemblyai_api: str = "not_tested"

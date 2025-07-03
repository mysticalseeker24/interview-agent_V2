"""Health check router for User Service."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get("/", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint to verify service and database connectivity.
    
    Returns:
        HealthResponse: Service health status
    """
    try:
        # Test database connection
        await db.execute("SELECT 1")
        
        return HealthResponse(
            status="healthy",
            service="user-service",
            version="0.1.0",
            database="connected"
        )
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            service="user-service",
            version="0.1.0",
            database="disconnected",
            error=str(e)
        )

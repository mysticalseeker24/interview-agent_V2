"""Health check router for interview service."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.schemas.health import HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health", response_model=dict)
async def health_check():
    """
    Standardized health check endpoint.
    
    Returns:
        dict: Health status
    """
    return {"status": "healthy"}

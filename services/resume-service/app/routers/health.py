"""Health check router for Resume Service."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.schemas.health import HealthResponse
from app.services.resume_parsing_service import ResumeParsingService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint.
    
    Args:
        db: Database session
        
    Returns:
        Health status
    """
    try:
        # Test database connection
        await db.execute(text("SELECT 1"))
        database_status = "connected"
        
        # Test spaCy model
        parser = ResumeParsingService()
        spacy_status = "loaded" if parser.nlp else "not_loaded"
        
        return HealthResponse(
            status="ok",
            service="resume-service",
            database=database_status,
            spacy_model=spacy_status
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy"
        )

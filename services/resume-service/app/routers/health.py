"""Health check router for Resume Service."""
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, status

from app.schemas.health import HealthResponse
from app.services.resume_parsing_service import ResumeParsingService
from app.core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Health status
    """
    try:
        settings = get_settings()
        
        # Test data directory
        data_dir = Path("data")
        storage_status = "available" if data_dir.exists() else "not_available"
        
        # Test spaCy model
        parser = ResumeParsingService()
        spacy_status = "loaded" if parser.nlp else "not_loaded"
        
        return HealthResponse(
            status="ok",
            service="resume-service",
            storage=storage_status,
            spacy_model=spacy_status
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy"
        )

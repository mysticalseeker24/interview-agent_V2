"""
Logging configuration for Media Service.
"""
import logging
import sys
from pathlib import Path

from app.core.config import get_settings

settings = get_settings()


def setup_logging() -> None:
    """Setup logging configuration."""
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format=settings.log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / "media_service.log"),
        ],
    )
    
    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("celery").setLevel(logging.INFO)
    
    # Create logger for this application
    logger = logging.getLogger(__name__)
    logger.info("Logging configured successfully") 
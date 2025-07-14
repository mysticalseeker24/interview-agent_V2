"""
Logging configuration for TalentSync Auth Gateway Service.

Provides structured logging with performance optimization for high-throughput scenarios.
"""
import logging
import sys
from typing import Any, Dict

from app.core.settings import settings


def setup_logging() -> None:
    """
    Configure application logging with performance optimizations.
    
    Sets up structured logging with appropriate levels and formatters
    for high-throughput production environments.
    """
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
        force=True,
    )
    
    # Set specific logger levels for performance
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    # Create logger for this service
    logger = logging.getLogger("talentsync.user-service")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    logger.info(f"Logging configured for {settings.SERVICE_NAME} v{settings.VERSION}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the specified name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(f"talentsync.user-service.{name}")


class PerformanceLogger:
    """
    Performance-optimized logger for high-throughput operations.
    
    Provides structured logging with minimal overhead for critical paths.
    """
    
    def __init__(self, name: str):
        """
        Initialize performance logger.
        
        Args:
            name: Logger name
        """
        self.logger = get_logger(name)
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message with optional structured data."""
        if kwargs:
            self.logger.info(f"{message} | {kwargs}")
        else:
            self.logger.info(message)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message with optional structured data."""
        if kwargs:
            self.logger.warning(f"{message} | {kwargs}")
        else:
            self.logger.warning(message)
    
    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message with optional structured data."""
        if kwargs:
            self.logger.error(f"{message} | {kwargs}")
        else:
            self.logger.error(message)
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message with optional structured data."""
        if settings.DEBUG:
            if kwargs:
                self.logger.debug(f"{message} | {kwargs}")
            else:
                self.logger.debug(message) 
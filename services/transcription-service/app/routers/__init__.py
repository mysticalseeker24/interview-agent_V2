"""
Router initialization for Transcription Service.
"""

from .transcription import router as transcription_router
from .media import router as media_router
from .health import router as health_router

__all__ = ["transcription_router", "media_router", "health_router"]

"""
API routers initialization.
"""
from app.routers.media import router as media_router
from app.routers.monitoring import router as monitoring_router

__all__ = ["media_router", "monitoring_router"]

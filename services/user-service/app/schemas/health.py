"""Health check schema definitions."""
from typing import Optional
from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str
    service: str
    version: str
    database: str
    error: Optional[str] = None

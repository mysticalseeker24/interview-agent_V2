"""Health check schema definitions."""
from typing import Optional
from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str
    service: str
    version: str
    database: str
    redis: Optional[str] = None
    pinecone: Optional[str] = None
    error: Optional[str] = None

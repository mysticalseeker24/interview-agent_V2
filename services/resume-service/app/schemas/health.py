"""Health check schema definitions."""
from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str
    service: str
    database: str
    spacy_model: str = "not_loaded"

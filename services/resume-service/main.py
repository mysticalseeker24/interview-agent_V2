"""
Main entry point for the Resume Processing Service.
"""
import uvicorn
from app.api import app

if __name__ == "__main__":
    uvicorn.run(
        "app.api:app",
        host="0.0.0.0",
        port=8004,
        reload=True,
        log_level="info"
    ) 
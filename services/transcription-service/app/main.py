from fastapi import FastAPI
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.routers import transcription
from app.services.monitoring import service_monitor

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events."""
    # Startup
    await service_monitor.start_monitoring(interval_seconds=60)
    
    yield
    
    # Shutdown
    await service_monitor.stop_monitoring()

app = FastAPI(
    title="TalentSync Transcription Service",
    description="Chunked audio transcription service using OpenAI Whisper",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(transcription.router, prefix="/transcribe")

@app.get("/health")
async def health_check():
    return JSONResponse(content={"status": "healthy", "service": "transcription-service"})

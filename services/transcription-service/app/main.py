from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path
from app.routers import transcription, tts
from app.services.monitoring import service_monitor

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events."""
    # Startup
    await service_monitor.start_monitoring(interval_seconds=60)
    
    # Ensure TTS files directory exists
    tts_directory = Path("tts_files")
    tts_directory.mkdir(exist_ok=True)
    
    yield
    
    # Shutdown
    await service_monitor.stop_monitoring()

app = FastAPI(
    title="TalentSync Transcription & TTS Service",
    description="Enhanced transcription service with Text-to-Speech using OpenAI Whisper and TTS",
    version="2.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(transcription.router, prefix="/transcribe")
app.include_router(tts.router, prefix="/api/v1")

# Mount static files for TTS audio serving
app.mount("/tts/files", StaticFiles(directory="tts_files"), name="tts_files")

@app.get("/health")
async def health_check():
    return JSONResponse(content={
        "status": "healthy", 
        "service": "transcription-tts-service",
        "features": ["transcription", "tts", "caching", "monitoring"]
    })

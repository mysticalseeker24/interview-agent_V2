import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pathlib import Path
from ..core.database import get_db
from ..models import TTSCache
from ..schemas.transcription import TTSRequest, TTSResponse, TTSCacheInfo
from ..services.playai_tts import GroqTTSClient
from ..core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/tts", tags=["text-to-speech"])

# Initialize TTS client
groq_tts_client = GroqTTSClient()


@router.post("/generate", response_model=TTSResponse)
async def generate_tts(
    request: TTSRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate text-to-speech audio using Groq Play.ai TTS API.
    
    This endpoint accepts text and returns a URL to the generated audio file.
    Results are cached to improve performance and reduce API costs.
    """
    try:
        # Validate input
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        if len(request.text) > 10000:
            raise HTTPException(status_code=400, detail="Text too long. Max length: 10000 characters")
        
        # Check cache first
        cache_key = groq_tts_client._generate_cache_key(request.text, request.voice, request.format)
        cached_result = await groq_tts_client._check_cache(cache_key)
        
        if cached_result:
            # Update cache hit count in database
            cache_record = await db.execute(
                select(TTSCache).where(TTSCache.file_path.contains(cache_key))
            )
            cache_record = cache_record.scalar_one_or_none()
            
            if cache_record:
                cache_record.cache_hit_count += 1
                await db.commit()
            
            return TTSResponse(
                file_url=cached_result["file_url"],
                file_path=cached_result["file_path"],
                file_size_bytes=cached_result["file_size_bytes"],
                duration_seconds=cached_result["duration_seconds"],
                is_cached=True
            )
        
        # Generate new TTS
        tts_result = await groq_tts_client.synthesize(
            text=request.text,
            voice=request.voice,
            format=request.format
        )
        
        # Save to database cache
        cache_record = TTSCache(
            text=request.text,
            voice=request.voice,
            format=request.format,
            file_path=tts_result["file_path"],
            file_size_bytes=tts_result["file_size_bytes"],
            duration_seconds=tts_result["duration_seconds"]
        )
        
        db.add(cache_record)
        await db.commit()
        await db.refresh(cache_record)
        
        return TTSResponse(
            file_url=tts_result["file_url"],
            file_path=tts_result["file_path"],
            file_size_bytes=tts_result["file_size_bytes"],
            duration_seconds=tts_result["duration_seconds"],
            is_cached=False
        )
        
    except Exception as e:
        logger.error(f"TTS generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")


@router.get("/files/{filename}")
async def serve_tts_file(filename: str):
    """
    Serve cached TTS audio files.
    
    This endpoint serves the generated audio files from the cache directory.
    """
    try:
        file_path = settings.tts_cache_dir / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        # Validate file is within cache directory
        try:
            file_path.resolve().relative_to(settings.tts_cache_dir.resolve())
        except ValueError:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return FileResponse(
            path=file_path,
            media_type="audio/wav" if filename.endswith(".wav") else "audio/mpeg",
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to serve TTS file {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to serve audio file")


@router.get("/cache-info", response_model=TTSCacheInfo)
async def get_cache_info(db: AsyncSession = Depends(get_db)):
    """
    Get information about TTS cache.
    
    Returns statistics about cached files and usage patterns.
    """
    try:
        # Get database cache stats
        total_requests = await db.execute(select(func.count(TTSCache.id)))
        total_requests = total_requests.scalar()
        
        total_size = await db.execute(select(func.sum(TTSCache.file_size_bytes)))
        total_size = total_size.scalar() or 0
        
        avg_duration = await db.execute(select(func.avg(TTSCache.duration_seconds)))
        avg_duration = avg_duration.scalar() or 0.0
        
        # Get file system cache info
        fs_cache_info = await groq_tts_client.get_cache_info()
        
        return TTSCacheInfo(
            total_requests=total_requests,
            cache_hits=fs_cache_info.get("cache_hits", 0),
            cache_misses=fs_cache_info.get("cache_misses", 0),
            total_file_size=total_size,
            average_duration=avg_duration
        )
        
    except Exception as e:
        logger.error(f"Failed to get cache info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get cache info: {str(e)}")


@router.post("/cache/cleanup")
async def cleanup_cache(db: AsyncSession = Depends(get_db)):
    """
    Clean up old cached files.
    
    Removes files older than the configured maximum age.
    This endpoint is also automatically called after each interview session.
    """
    try:
        # Use the new cleanup_cache method for interview-aware cleanup
        cleanup_result = await groq_tts_client.cleanup_cache()
        
        if cleanup_result["status"] == "success":
            logger.info(f"TTS cache cleanup completed: {cleanup_result['cleanup_result']}")
            return {
                "message": "Cache cleanup completed successfully",
                "status": "success",
                "cleanup_result": cleanup_result["cleanup_result"]
            }
        else:
            logger.warning(f"TTS cache cleanup had issues: {cleanup_result['message']}")
            return {
                "message": cleanup_result["message"],
                "status": "partial",
                "cleanup_result": cleanup_result["cleanup_result"]
            }
        
    except Exception as e:
        logger.error(f"Failed to cleanup cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup cache: {str(e)}")


@router.get("/voices")
async def get_available_voices():
    """
    Get list of available voices from Groq Play.ai TTS API.
    """
    try:
        voices = await groq_tts_client.get_available_voices()
        return {
            "voices": voices,
            "default_voice": settings.groq_default_voice,
            "total_voices": len(voices)
        }
        
    except Exception as e:
        logger.error(f"Failed to get available voices: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get available voices: {str(e)}")


@router.get("/health")
async def tts_health_check():
    """
    Check TTS service health.
    """
    try:
        health_status = await groq_tts_client.health_check()
        return {
            "service": "TTS",
            "status": health_status["status"],
            "message": health_status["message"],
            "voices_available": health_status.get("voices_available", 0)
        }
        
    except Exception as e:
        logger.error(f"TTS health check failed: {str(e)}")
        return {
            "service": "TTS",
            "status": "unhealthy",
            "message": f"Health check failed: {str(e)}",
            "voices_available": 0
        }


@router.get("/stats")
async def get_tts_stats(db: AsyncSession = Depends(get_db)):
    """
    Get detailed TTS statistics.
    """
    try:
        # Database stats
        total_requests = await db.execute(select(func.count(TTSCache.id)))
        total_requests = total_requests.scalar()
        
        total_size = await db.execute(select(func.sum(TTSCache.file_size_bytes)))
        total_size = total_size.scalar() or 0
        
        avg_duration = await db.execute(select(func.avg(TTSCache.duration_seconds)))
        avg_duration = avg_duration.scalar() or 0.0
        
        # Voice usage stats
        voice_stats = await db.execute(
            select(TTSCache.voice, func.count(TTSCache.id))
            .group_by(TTSCache.voice)
        )
        voice_stats = voice_stats.all()
        
        # Format usage stats
        format_stats = await db.execute(
            select(TTSCache.format, func.count(TTSCache.id))
            .group_by(TTSCache.format)
        )
        format_stats = format_stats.all()
        
        return {
            "total_requests": total_requests,
            "total_size_bytes": total_size,
            "average_duration_seconds": avg_duration,
            "voice_usage": {voice: count for voice, count in voice_stats},
            "format_usage": {format: count for format, count in format_stats},
            "cache_directory": str(settings.tts_cache_dir),
            "max_file_age_days": settings.max_file_age_days
        }
        
    except Exception as e:
        logger.error(f"Failed to get TTS stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get TTS stats: {str(e)}") 
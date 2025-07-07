from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pathlib import Path
import os

from app.core.database import get_session
from app.schemas.transcription import TTSRequestIn, TTSRequestOut, TTSCacheInfo, VoiceType
from app.services.tts_service import TTSService


router = APIRouter(prefix="/tts", tags=["Text-to-Speech"])

@router.post("/generate", response_model=TTSRequestOut, status_code=status.HTTP_201_CREATED)
async def generate_tts(
    request: TTSRequestIn,
    session: AsyncSession = Depends(get_session)
):
    """
    Generate Text-to-Speech audio with caching.
    
    - **text**: Text to convert to speech (max 4000 characters)
    - **voice**: Voice type (alloy, echo, fable, onyx, nova, shimmer)
    - **format**: Audio format (mp3, wav, flac, aac)
    - **session_id**: Optional interview session ID for tracking
    - **persona_name**: Optional interviewer persona name
    
    Returns the generated audio file URL and metadata.
    Implements intelligent caching to avoid regenerating identical requests.
    """
    
    tts_service = TTSService()
    
    try:
        result = await tts_service.generate_tts(session, request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"TTS generation failed: {str(e)}"
        )


@router.get("/files/{filename}")
async def serve_tts_file(filename: str):
    """
    Serve TTS audio files.
    
    - **filename**: Name of the TTS audio file to serve
    
    Returns the audio file for playback or download.
    """
    
    tts_directory = Path("tts_files")
    file_path = tts_directory / filename
    
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found"
        )
    
    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file path"
        )
    
    # Determine media type based on file extension
    media_type_map = {
        '.mp3': 'audio/mpeg',
        '.wav': 'audio/wav',
        '.flac': 'audio/flac',
        '.aac': 'audio/aac'
    }
    
    media_type = media_type_map.get(file_path.suffix.lower(), 'audio/mpeg')
    
    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename
    )


@router.get("/session/{session_id}/history", response_model=List[TTSRequestOut])
async def get_session_tts_history(
    session_id: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Get TTS generation history for a specific interview session.
    
    - **session_id**: Interview session ID
    
    Returns list of all TTS requests made during the session.
    """
    
    tts_service = TTSService()
    
    try:
        history = await tts_service.get_session_tts_history(session, session_id)
        return history
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve TTS history: {str(e)}"
        )


@router.get("/cache/info", response_model=TTSCacheInfo)
async def get_cache_info(
    session: AsyncSession = Depends(get_session)
):
    """
    Get TTS cache statistics and information.
    
    Returns cache performance metrics and storage information.
    """
    
    tts_service = TTSService()
    
    try:
        cache_info = await tts_service.get_cache_info(session)
        return cache_info
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve cache info: {str(e)}"
        )


@router.post("/cache/cleanup")
async def cleanup_old_files(
    session: AsyncSession = Depends(get_session)
):
    """
    Clean up old TTS files and database entries.
    
    Removes files older than the cache duration and their database records.
    This endpoint should be called periodically for maintenance.
    """
    
    tts_service = TTSService()
    
    try:
        cleanup_result = await tts_service.cleanup_old_files(session)
        return {
            "message": "Cleanup completed successfully",
            "deleted_files": cleanup_result["deleted_files"],
            "deleted_records": cleanup_result["deleted_records"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cleanup failed: {str(e)}"
        )


@router.get("/voices", response_model=List[str])
async def list_available_voices():
    """
    List all available TTS voices.
    
    Returns the list of voice options supported by OpenAI TTS.
    """
    
    return [voice.value for voice in VoiceType]


@router.post("/test", response_model=TTSRequestOut)
async def test_tts_generation(
    text: str = Query(..., max_length=100, description="Test text for TTS"),
    voice: VoiceType = Query(VoiceType.ALLOY, description="Voice to test"),
    session: AsyncSession = Depends(get_session)
):
    """
    Test TTS generation with a short text.
    
    - **text**: Short text to test (max 100 characters)
    - **voice**: Voice type to test
    
    Useful for testing TTS functionality and voice characteristics.
    """
    
    if len(text.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Test text cannot be empty"
        )
    
    request = TTSRequestIn(
        text=text,
        voice=voice,
        format="mp3",
        session_id="test_session",
        persona_name="test"
    )
    
    tts_service = TTSService()
    
    try:
        result = await tts_service.generate_tts(session, request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"TTS test failed: {str(e)}"
        )

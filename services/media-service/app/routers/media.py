"""
Media API routes for chunk upload and session management.
"""
import logging
import time
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.media import (
    ChunkUploadResponse,
    MediaSession,
    MediaSessionCreate,
    SessionSummaryResponse,
    MediaValidationResponse,
    DeviceEnumerationResponse,
)
from app.services.media_service import media_service
from app.services.monitoring import metrics_service
from app.services.device_service import device_service
from app.services.event_service import event_service
from app.workers.media_tasks import process_chunk, validate_chunk

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/media", tags=["media"])


@router.post("/session", response_model=MediaSession)
async def create_session(
    session_data: MediaSessionCreate,
    db: AsyncSession = Depends(get_db)
) -> MediaSession:
    """
    Create a new media session for chunked uploads.
    """
    try:
        session = await media_service.create_session(db, session_data)
        logger.info(f"Created session: {session.session_id}")
        return session
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chunk-upload", response_model=ChunkUploadResponse)
async def upload_chunk(
    background_tasks: BackgroundTasks,
    session_id: str = Form(..., description="Session identifier"),
    sequence_index: int = Form(..., description="Chunk sequence index"),
    total_chunks: Optional[int] = Form(None, description="Total expected chunks"),
    question_id: Optional[str] = Form(None, description="Question identifier"),
    overlap_seconds: float = Form(2.0, description="Overlap duration in seconds"),
    file: UploadFile = File(..., description="Audio chunk file"),
    db: AsyncSession = Depends(get_db)
) -> ChunkUploadResponse:
    """
    Upload a media chunk.
    
    **Request Fields** (multipart/form-data):
    - `session_id` (str): Session identifier
    - `sequence_index` (int): Chunk sequence index (0, 1, 2, ...)
    - `total_chunks` (int, optional): Total expected chunks for validation
    - `question_id` (str, optional): Associated question ID
    - `overlap_seconds` (float): Overlap duration (default: 2.0)
    - `file` (UploadFile): Audio chunk blob (up to ~5 min + overlap)
    
    **Behavior**:
    - Saves file as `uploads/{session_id}/chunk_{sequence_index}.webm`
    - Creates or updates MediaChunk record
    - Triggers background processing if upload successful
    - Marks session as complete if this is the last chunk
    
    **Response**:
    ```json
    {
      "chunk_id": 42,
      "sequence_index": 3,
      "file_path": "/uploads/abc123/chunk_3.webm",
      "session_id": "abc123",
      "upload_status": "uploaded",
      "message": "Chunk uploaded successfully"
    }
    ```
    """
    start_time = time.time()
    
    try:
        # Validate input
        if sequence_index < 0:
            raise HTTPException(status_code=400, detail="sequence_index must be >= 0")
        
        if overlap_seconds < 0:
            raise HTTPException(status_code=400, detail="overlap_seconds must be >= 0")
        
        if total_chunks is not None and total_chunks < 1:
            raise HTTPException(status_code=400, detail="total_chunks must be >= 1")
        
        # Upload chunk
        response = await media_service.upload_chunk(
            db=db,
            session_id=session_id,
            sequence_index=sequence_index,
            file=file,
            total_chunks=total_chunks,
            question_id=question_id,
            overlap_seconds=overlap_seconds
        )
        
        # Record metrics
        upload_duration = time.time() - start_time
        metrics_service.record_chunk_upload(session_id, "success", upload_duration)
        
        # Queue background processing
        background_tasks.add_task(
            lambda: process_chunk.delay(response.chunk_id)
        )
        
        # Queue validation
        background_tasks.add_task(
            lambda: validate_chunk.delay(response.chunk_id)
        )
        
        logger.info(
            f"Successfully uploaded chunk {sequence_index} for session {session_id} "
            f"(chunk_id: {response.chunk_id})"
        )
        
        return response
        
    except HTTPException:
        # Record failed upload
        upload_duration = time.time() - start_time
        metrics_service.record_chunk_upload(session_id, "failed", upload_duration)
        raise
    except Exception as e:
        upload_duration = time.time() - start_time
        metrics_service.record_chunk_upload(session_id, "failed", upload_duration)
        logger.error(f"Error uploading chunk {sequence_index} for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/session/{session_id}/summary", response_model=SessionSummaryResponse)
async def get_session_summary(
    session_id: str,
    db: AsyncSession = Depends(get_db)
) -> SessionSummaryResponse:
    """
    Get comprehensive summary of a media session.
    
    Returns session metadata, statistics, and list of all chunks
    with their current status and processing information.
    """
    try:
        summary = await media_service.get_session_summary(db, session_id)
        return summary
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session summary for {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}/gaps")
async def get_session_gaps(
    session_id: str,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Find missing chunk sequence indices (gaps) in a session.
    
    Returns list of missing sequence indices that indicate
    potential upload failures or network issues.
    """
    try:
        gaps = await media_service.get_chunks_with_gaps(db, session_id)
        return {
            "session_id": session_id,
            "gaps": gaps,
            "gap_count": len(gaps),
            "has_gaps": len(gaps) > 0
        }
    except Exception as e:
        logger.error(f"Error finding gaps for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate-file")
async def validate_file(
    file: UploadFile = File(..., description="File to validate")
) -> MediaValidationResponse:
    """
    Validate a file before upload.
    
    Checks file size, format, and basic requirements without
    actually saving the file. Useful for client-side validation.
    """
    try:
        # Use media service validation
        from app.services.media_service import MediaService
        temp_service = MediaService()
        validation_result = await temp_service._validate_file(file)
        
        # Reset file pointer for potential future use
        await file.seek(0)
        
        return validation_result
        
    except Exception as e:
        logger.error(f"Error validating file: {e}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.delete("/session/{session_id}")
async def delete_session(
    session_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Delete a session and all its associated chunks and files.
    
    This operation is irreversible. Use with caution.
    """
    try:
        # Queue cleanup task
        background_tasks.add_task(
            lambda: media_service.cleanup_old_files(db, max_age_days=0)
        )
        
        return {
            "message": f"Session {session_id} deletion queued",
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/storage/stats")
async def get_storage_statistics(
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Get storage usage statistics.
    
    Returns information about disk usage, file counts,
    and storage distribution across sessions.
    """
    try:
        stats = await media_service.get_storage_statistics(db)
        return stats
    except Exception as e:
        logger.error(f"Error getting storage statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/devices", response_model=DeviceEnumerationResponse)
async def enumerate_devices() -> dict:
    """
    Enumerate available media devices.
    
    Returns available audio input/output devices and video input devices
    for the frontend to populate camera/mic dropdowns on the Lobby page.
    """
    try:
        devices = await device_service.get_available_devices()
        
        return {
            **devices,
            "platform": device_service.platform,
        }
        
    except Exception as e:
        logger.error(f"Error enumerating devices: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to enumerate devices: {str(e)}"
        )


@router.post("/event")
async def create_event(
    event_data: dict,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Create a new event record.
    
    Stores event details such as type, timestamp,
    and associated session or chunk IDs.
    """
    try:
        event = await event_service.create_event(db, event_data)
        return {"message": "Event recorded", "event_id": event.event_id}
    except Exception as e:
        logger.error(f"Error creating event: {e}")
        raise HTTPException(status_code=500, detail=str(e))

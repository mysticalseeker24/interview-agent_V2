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
        validation_result = await media_service._validate_file(file)
        return validation_result
    except Exception as e:
        logger.error(f"Error validating file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}")
async def delete_session(
    session_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Delete a media session and all associated chunks.
    
    This will remove all files and database records for the session.
    """
    try:
        # Get session
        from sqlalchemy import select
        from app.models.media import MediaSession, MediaChunk
        
        result = await db.execute(
            select(MediaSession).where(MediaSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get all chunks for session
        result = await db.execute(
            select(MediaChunk).where(MediaChunk.session_id == session_id)
        )
        chunks = result.scalars().all()
        
        # Delete files
        deleted_files = 0
        for chunk in chunks:
            try:
                from pathlib import Path
                file_path = Path(chunk.file_path)
                if file_path.exists():
                    file_path.unlink()
                    deleted_files += 1
            except Exception as e:
                logger.warning(f"Failed to delete file {chunk.file_path}: {e}")
        
        # Delete database records
        for chunk in chunks:
            await db.delete(chunk)
        
        await db.delete(session)
        await db.commit()
        
        # Clean up empty session directory
        try:
            from pathlib import Path
            session_dir = Path(f"uploads/{session_id}")
            if session_dir.exists() and not any(session_dir.iterdir()):
                session_dir.rmdir()
        except Exception as e:
            logger.warning(f"Failed to remove session directory: {e}")
        
        logger.info(f"Deleted session {session_id} with {len(chunks)} chunks and {deleted_files} files")
        
        return {
            "session_id": session_id,
            "deleted_chunks": len(chunks),
            "deleted_files": deleted_files,
            "message": "Session deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/storage/stats")
async def get_storage_statistics(
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Get storage statistics and usage information.
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
    
    Returns information about available audio and video devices
    for client-side media capture.
    """
    try:
        devices = await device_service.get_available_devices()
        
        return DeviceEnumerationResponse(
            audio_inputs=devices["audio_inputs"],
            audio_outputs=devices["audio_outputs"],
            video_inputs=devices["video_inputs"],
            platform=device_service.platform
        )
        
    except Exception as e:
        logger.error(f"Error enumerating devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/event")
async def create_event(
    event_data: dict,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Create a custom event for testing or external integration.
    """
    try:
        # Log the event
        logger.info(f"Received custom event: {event_data}")
        
        # Store event in database if needed
        # This could be extended to store events in a separate table
        
        return {
            "status": "success",
            "event_id": f"event_{int(time.time())}",
            "timestamp": time.time(),
            "data": event_data
        }
        
    except Exception as e:
        logger.error(f"Error creating event: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 
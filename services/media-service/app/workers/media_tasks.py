"""
Background tasks for Media Service using Celery.
"""
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List

import httpx
from celery import Task
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.models.media import MediaChunk, MediaSession, MediaProcessingTask
from app.services.media_service import media_service
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)
settings = get_settings()


class DatabaseTask(Task):
    """Base task class that provides database session management."""
    
    def __init__(self):
        self._session = None
    
    @property
    def session(self):
        if self._session is None:
            self._session = AsyncSessionLocal()
        return self._session
    
    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        if self._session:
            self._session.close()


@celery_app.task(bind=True, base=DatabaseTask, name="app.workers.media_tasks.process_chunk")
def process_chunk(self, chunk_id: int) -> Dict[str, Any]:
    """
    Process a media chunk - validate, extract metadata, trigger transcription.
    """
    import asyncio
    return asyncio.run(self._process_chunk_async(chunk_id))


async def _process_chunk_async(chunk_id: int) -> Dict[str, Any]:
    """Async implementation of chunk processing."""
    logger.info(f"Processing chunk {chunk_id}")
    
    async with AsyncSessionLocal() as db:
        try:
            # Get chunk
            result = await db.execute(
                select(MediaChunk).where(MediaChunk.id == chunk_id)
            )
            chunk = result.scalar_one_or_none()
            
            if not chunk:
                raise ValueError(f"Chunk {chunk_id} not found")
            
            # Update status
            chunk.upload_status = "processing"
            await db.commit()
            
            # Validate file exists
            file_path = Path(chunk.file_path)
            if not file_path.exists():
                chunk.upload_status = "failed"
                chunk.validation_errors = json.dumps(["File not found"])
                chunk.is_valid = False
                await db.commit()
                return {"status": "failed", "error": "File not found"}
            
            # Extract audio metadata (placeholder - would use actual audio processing)
            metadata = await _extract_audio_metadata(file_path)
            
            # Update chunk with metadata
            if metadata:
                chunk.duration_seconds = metadata.get("duration")
                chunk.sample_rate = metadata.get("sample_rate")
                chunk.bit_rate = metadata.get("bit_rate")
                chunk.channels = metadata.get("channels")
                chunk.audio_quality_score = metadata.get("quality_score")
                chunk.noise_level = metadata.get("noise_level")
                chunk.silence_percentage = metadata.get("silence_percentage")
            
            chunk.upload_status = "processed"
            chunk.processed_at = datetime.utcnow()
            await db.commit()
            
            # Trigger transcription service
            transcription_result = await _trigger_transcription(chunk)
            
            if transcription_result.get("success"):
                chunk.transcription_status = "processing"
            else:
                chunk.transcription_status = "failed"
                logger.error(f"Failed to trigger transcription for chunk {chunk_id}")
            
            await db.commit()
            
            logger.info(f"Successfully processed chunk {chunk_id}")
            return {
                "status": "success",
                "chunk_id": chunk_id,
                "metadata": metadata,
                "transcription_triggered": transcription_result.get("success", False)
            }
            
        except Exception as e:
            logger.error(f"Error processing chunk {chunk_id}: {e}")
            
            # Update chunk status
            try:
                result = await db.execute(
                    select(MediaChunk).where(MediaChunk.id == chunk_id)
                )
                chunk = result.scalar_one_or_none()
                if chunk:
                    chunk.upload_status = "failed"
                    chunk.validation_errors = json.dumps([str(e)])
                    chunk.is_valid = False
                    await db.commit()
            except Exception as update_error:
                logger.error(f"Failed to update chunk status: {update_error}")
            
            return {"status": "failed", "error": str(e)}


@celery_app.task(bind=True, base=DatabaseTask, name="app.workers.media_tasks.validate_chunk")
def validate_chunk(self, chunk_id: int) -> Dict[str, Any]:
    """Validate a media chunk for quality and completeness."""
    import asyncio
    return asyncio.run(self._validate_chunk_async(chunk_id))


async def _validate_chunk_async(chunk_id: int) -> Dict[str, Any]:
    """Async implementation of chunk validation."""
    logger.info(f"Validating chunk {chunk_id}")
    
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(MediaChunk).where(MediaChunk.id == chunk_id)
            )
            chunk = result.scalar_one_or_none()
            
            if not chunk:
                return {"status": "failed", "error": "Chunk not found"}
            
            validation_errors = []
            
            # Check file exists
            file_path = Path(chunk.file_path)
            if not file_path.exists():
                validation_errors.append("File does not exist")
            else:
                # Check file size
                actual_size = file_path.stat().st_size
                if chunk.file_size_bytes and abs(actual_size - chunk.file_size_bytes) > 1024:
                    validation_errors.append(f"File size mismatch: expected {chunk.file_size_bytes}, got {actual_size}")
                
                # Check if file is readable
                try:
                    with open(file_path, 'rb') as f:
                        f.read(1024)  # Read first 1KB
                except Exception as e:
                    validation_errors.append(f"File not readable: {e}")
            
            # Update validation results
            chunk.is_valid = len(validation_errors) == 0
            if validation_errors:
                chunk.validation_errors = json.dumps(validation_errors)
            
            await db.commit()
            
            return {
                "status": "success",
                "chunk_id": chunk_id,
                "is_valid": chunk.is_valid,
                "errors": validation_errors
            }
            
        except Exception as e:
            logger.error(f"Error validating chunk {chunk_id}: {e}")
            return {"status": "failed", "error": str(e)}


@celery_app.task(bind=True, base=DatabaseTask, name="app.workers.media_tasks.cleanup_session")
def cleanup_session(self, session_id: str) -> Dict[str, Any]:
    """Clean up a completed session's temporary files."""
    import asyncio
    return asyncio.run(self._cleanup_session_async(session_id))


async def _cleanup_session_async(session_id: str) -> Dict[str, Any]:
    """Async implementation of session cleanup."""
    logger.info(f"Cleaning up session {session_id}")
    
    async with AsyncSessionLocal() as db:
        try:
            result = await media_service.cleanup_old_files(db, max_age_days=0)
            return {"status": "success", "session_id": session_id, "cleanup_result": result}
            
        except Exception as e:
            logger.error(f"Error cleaning up session {session_id}: {e}")
            return {"status": "failed", "error": str(e)}


@celery_app.task(bind=True, base=DatabaseTask, name="app.workers.media_tasks.check_session_gaps")
def check_session_gaps(self) -> Dict[str, Any]:
    """Check for gaps in chunk sequences across all active sessions."""
    import asyncio
    return asyncio.run(self._check_session_gaps_async())


async def _check_session_gaps_async() -> Dict[str, Any]:
    """Async implementation of gap checking."""
    logger.info("Checking for session gaps")
    
    async with AsyncSessionLocal() as db:
        try:
            # Get all active sessions
            result = await db.execute(
                select(MediaSession).where(MediaSession.session_status == "active")
            )
            active_sessions = result.scalars().all()
            
            gap_report = {}
            total_gaps = 0
            
            for session in active_sessions:
                gaps = await media_service.get_chunks_with_gaps(db, session.session_id)
                if gaps:
                    gap_report[session.session_id] = gaps
                    total_gaps += len(gaps)
                    logger.warning(f"Session {session.session_id} has gaps: {gaps}")
            
            return {
                "status": "success",
                "total_sessions_checked": len(active_sessions),
                "sessions_with_gaps": len(gap_report),
                "total_gaps": total_gaps,
                "gap_details": gap_report
            }
            
        except Exception as e:
            logger.error(f"Error checking session gaps: {e}")
            return {"status": "failed", "error": str(e)}


@celery_app.task(bind=True, base=DatabaseTask, name="app.workers.media_tasks.cleanup_old_files")
def cleanup_old_files(self) -> Dict[str, Any]:
    """Periodic cleanup of old files and sessions."""
    import asyncio
    return asyncio.run(self._cleanup_old_files_async())


async def _cleanup_old_files_async() -> Dict[str, Any]:
    """Async implementation of old files cleanup."""
    logger.info("Starting periodic cleanup of old files")
    
    async with AsyncSessionLocal() as db:
        try:
            result = await media_service.cleanup_old_files(db)
            logger.info(f"Cleanup completed: {result}")
            return {"status": "success", "cleanup_result": result}
            
        except Exception as e:
            logger.error(f"Error during periodic cleanup: {e}")
            return {"status": "failed", "error": str(e)}


@celery_app.task(bind=True, name="app.workers.media_tasks.health_check")
def health_check(self) -> Dict[str, Any]:
    """Health check task to monitor worker status."""
    logger.debug("Worker health check")
    
    try:
        # Check database connectivity
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def check_db():
            async with AsyncSessionLocal() as db:
                await db.execute(select(1))
                return True
        
        db_healthy = loop.run_until_complete(check_db())
        loop.close()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected" if db_healthy else "disconnected"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


# Helper functions

async def _extract_audio_metadata(file_path: Path) -> Dict[str, Any]:
    """
    Extract metadata from audio file.
    This is a placeholder - in production, you'd use libraries like ffprobe or librosa.
    """
    try:
        # Placeholder implementation
        file_size = file_path.stat().st_size
        
        # Estimate duration based on file size (very rough)
        estimated_duration = max(30, file_size / 32000)  # Rough estimate
        
        return {
            "duration": estimated_duration,
            "sample_rate": 44100,  # Default
            "bit_rate": 128000,    # Default
            "channels": 1,         # Mono
            "quality_score": 0.8,  # Placeholder
            "noise_level": 0.1,    # Placeholder
            "silence_percentage": 5.0  # Placeholder
        }
        
    except Exception as e:
        logger.error(f"Error extracting metadata from {file_path}: {e}")
        return {}


async def _trigger_transcription(chunk: MediaChunk) -> Dict[str, Any]:
    """
    Trigger transcription service for a chunk.
    """
    try:
        transcription_url = f"{settings.transcription_service_url}/transcription/chunk-upload"
        
        # Prepare data for transcription service
        chunk_data = {
            "session_id": chunk.session_id,
            "sequence_index": chunk.sequence_index,
            "overlap_seconds": chunk.overlap_seconds,
            "file_path": chunk.file_path,
            "question_id": chunk.question_id
        }
        
        # Make HTTP request to transcription service
        async with httpx.AsyncClient() as client:
            response = await client.post(
                transcription_url,
                json=chunk_data,
                timeout=30.0
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully triggered transcription for chunk {chunk.id}")
                return {"success": True, "response": response.json()}
            else:
                logger.error(f"Transcription service error: {response.status_code} - {response.text}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
    except Exception as e:
        logger.error(f"Error triggering transcription for chunk {chunk.id}: {e}")
        return {"success": False, "error": str(e)}

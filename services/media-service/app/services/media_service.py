"""
Core Media Service for handling chunked audio uploads and processing.
"""
import json
import logging
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import aiofiles
from fastapi import HTTPException, UploadFile
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.media import MediaChunk, MediaSession, MediaProcessingTask
from app.schemas.media import (
    ChunkUploadResponse,
    MediaChunkCreate,
    MediaChunkUpdate,
    MediaSessionCreate,
    MediaSessionUpdate,
    MediaValidationResponse,
    SessionSummaryResponse,
)

logger = logging.getLogger(__name__)
settings = get_settings()


class MediaService:
    """Service for handling media operations."""
    
    def __init__(self):
        self.upload_dir = settings.upload_dir
        self.max_file_size = settings.max_file_size
        self.allowed_extensions = settings.allowed_extensions
        
    async def create_session(
        self,
        db: AsyncSession,
        session_data: MediaSessionCreate
    ) -> MediaSession:
        """Create a new media session."""
        try:
            # Check if session already exists
            result = await db.execute(
                select(MediaSession).where(MediaSession.session_id == session_data.session_id)
            )
            existing_session = result.scalar_one_or_none()
            
            if existing_session:
                logger.info(f"Session {session_data.session_id} already exists")
                return existing_session
            
            # Create new session
            session = MediaSession(**session_data.model_dump())
            db.add(session)
            await db.flush()
            await db.refresh(session)
            
            # Create session directory
            session_dir = self.upload_dir / session_data.session_id
            session_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Created new media session: {session_data.session_id}")
            return session
            
        except Exception as e:
            logger.error(f"Error creating session {session_data.session_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")
    
    async def upload_chunk(
        self,
        db: AsyncSession,
        session_id: str,
        sequence_index: int,
        file: UploadFile,
        total_chunks: Optional[int] = None,
        question_id: Optional[str] = None,
        overlap_seconds: float = 2.0
    ) -> ChunkUploadResponse:
        """Upload and process a media chunk."""
        try:
            # Validate file
            validation_result = await self._validate_file(file)
            if not validation_result.is_valid:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file: {', '.join(validation_result.errors)}"
                )
            
            # Ensure session exists
            await self._ensure_session_exists(db, session_id)
            
            # Generate file name and path
            file_extension = Path(file.filename).suffix.lower().lstrip('.')
            file_name = f"chunk_{sequence_index:04d}.{file_extension}"
            session_dir = self.upload_dir / session_id
            session_dir.mkdir(parents=True, exist_ok=True)
            file_path = session_dir / file_name
            
            # Save file
            file_size = await self._save_file(file, file_path)
            
            # Check for existing chunk and handle overwrite
            result = await db.execute(
                select(MediaChunk).where(
                    and_(
                        MediaChunk.session_id == session_id,
                        MediaChunk.sequence_index == sequence_index
                    )
                )
            )
            existing_chunk = result.scalar_one_or_none()
            
            if existing_chunk:
                # Update existing chunk
                chunk = await self._update_existing_chunk(
                    db, existing_chunk, file_path, file_size, file_name, file_extension
                )
                logger.info(f"Updated existing chunk {sequence_index} for session {session_id}")
            else:
                # Create new chunk
                chunk = await self._create_new_chunk(
                    db, session_id, sequence_index, file_path, file_size,
                    file_name, file_extension, question_id, overlap_seconds
                )
                logger.info(f"Created new chunk {sequence_index} for session {session_id}")
            
            # Update session statistics
            await self._update_session_stats(db, session_id, total_chunks)
            
            # Check if this is the last chunk and trigger completion
            is_final_chunk = total_chunks and sequence_index == total_chunks - 1
            if is_final_chunk:
                await self._handle_session_completion(db, session_id)
            
            # Emit event to other services (import here to avoid circular imports)
            try:
                from app.services.event_service import event_service
                await event_service.emit_chunk_uploaded_event(
                    session_id=session_id,
                    chunk_id=chunk.id,
                    sequence_index=chunk.sequence_index,
                    file_path=str(chunk.file_path),
                    file_size_bytes=chunk.file_size_bytes or 0,
                    overlap_seconds=chunk.overlap_seconds,
                    question_id=question_id,
                    total_chunks=total_chunks,
                    is_final_chunk=is_final_chunk
                )
                logger.info(f"Emitted chunk upload event for session {session_id}, chunk {sequence_index}")
            except Exception as e:
                logger.warning(f"Failed to emit chunk upload event: {e}")
                # Don't fail the upload if event emission fails
            
            return ChunkUploadResponse(
                chunk_id=chunk.id,
                sequence_index=chunk.sequence_index,
                file_path=str(chunk.file_path),
                session_id=chunk.session_id,
                upload_status=chunk.upload_status,
                message="Chunk uploaded successfully"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error uploading chunk {sequence_index} for session {session_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to upload chunk: {str(e)}")
    
    async def get_session_summary(
        self,
        db: AsyncSession,
        session_id: str
    ) -> SessionSummaryResponse:
        """Get comprehensive session summary."""
        try:
            # Get session
            result = await db.execute(
                select(MediaSession).where(MediaSession.session_id == session_id)
            )
            session = result.scalar_one_or_none()
            
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            
            # Get all chunks for session
            result = await db.execute(
                select(MediaChunk)
                .where(MediaChunk.session_id == session_id)
                .order_by(MediaChunk.sequence_index)
            )
            chunks = result.scalars().all()
            
            # Calculate statistics
            uploaded_chunks = len([c for c in chunks if c.upload_status == "uploaded"])
            processed_chunks = len([c for c in chunks if c.transcription_status == "completed"])
            failed_chunks = len([c for c in chunks if c.upload_status == "failed" or c.transcription_status == "failed"])
            
            return SessionSummaryResponse(
                session_id=session.session_id,
                total_chunks=session.total_chunks,
                uploaded_chunks=uploaded_chunks,
                processed_chunks=processed_chunks,
                failed_chunks=failed_chunks,
                total_duration_seconds=session.total_duration_seconds,
                session_status=session.session_status,
                created_at=session.created_at,
                updated_at=session.updated_at,
                chunks=[chunk for chunk in chunks]
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting session summary for {session_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get session summary: {str(e)}")
    
    async def get_chunks_with_gaps(
        self,
        db: AsyncSession,
        session_id: str
    ) -> List[int]:
        """Find missing chunk sequence indices (gaps) in a session."""
        try:
            result = await db.execute(
                select(MediaChunk.sequence_index)
                .where(MediaChunk.session_id == session_id)
                .order_by(MediaChunk.sequence_index)
            )
            existing_indices = [row[0] for row in result.fetchall()]
            
            if not existing_indices:
                return []
            
            # Find gaps
            gaps = []
            for i in range(min(existing_indices), max(existing_indices) + 1):
                if i not in existing_indices:
                    gaps.append(i)
            
            if gaps:
                logger.warning(f"Found gaps in session {session_id}: {gaps}")
            
            return gaps
            
        except Exception as e:
            logger.error(f"Error finding gaps in session {session_id}: {e}")
            return []
    
    async def cleanup_old_files(
        self,
        db: AsyncSession,
        max_age_days: int = None
    ) -> Dict[str, int]:
        """Clean up old media files and database records."""
        try:
            max_age = max_age_days or settings.max_file_age_days
            cutoff_date = datetime.utcnow() - timedelta(days=max_age)
            
            # Find old sessions
            result = await db.execute(
                select(MediaSession)
                .where(MediaSession.created_at < cutoff_date)
                .where(MediaSession.session_status.in_(["completed", "failed", "abandoned"]))
            )
            old_sessions = result.scalars().all()
            
            deleted_files = 0
            deleted_chunks = 0
            deleted_sessions = 0
            
            for session in old_sessions:
                # Get chunks for this session
                result = await db.execute(
                    select(MediaChunk).where(MediaChunk.session_id == session.session_id)
                )
                chunks = result.scalars().all()
                
                # Delete files
                session_dir = self.upload_dir / session.session_id
                if session_dir.exists():
                    try:
                        shutil.rmtree(session_dir)
                        deleted_files += len(chunks)
                        logger.info(f"Deleted directory for session {session.session_id}")
                    except Exception as e:
                        logger.error(f"Error deleting directory {session_dir}: {e}")
                
                # Delete database records
                for chunk in chunks:
                    await db.delete(chunk)
                    deleted_chunks += 1
                
                await db.delete(session)
                deleted_sessions += 1
            
            logger.info(f"Cleanup completed: {deleted_sessions} sessions, {deleted_chunks} chunks, {deleted_files} files")
            
            return {
                "deleted_sessions": deleted_sessions,
                "deleted_chunks": deleted_chunks,
                "deleted_files": deleted_files
            }
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")
    
    async def get_storage_statistics(self, db: AsyncSession) -> Dict[str, any]:
        """Get storage usage statistics."""
        try:
            # Database statistics
            result = await db.execute(select(func.count(MediaSession.id)))
            total_sessions = result.scalar()
            
            result = await db.execute(
                select(func.count(MediaSession.id))
                .where(MediaSession.session_status == "active")
            )
            active_sessions = result.scalar()
            
            result = await db.execute(select(func.count(MediaChunk.id)))
            total_chunks = result.scalar()
            
            result = await db.execute(
                select(func.sum(MediaChunk.file_size_bytes))
            )
            total_storage_bytes = result.scalar() or 0
            
            result = await db.execute(
                select(func.avg(MediaChunk.file_size_bytes))
            )
            avg_chunk_size = result.scalar() or 0
            
            # File system statistics
            upload_dir_size = sum(
                f.stat().st_size for f in self.upload_dir.rglob('*') if f.is_file()
            ) if self.upload_dir.exists() else 0
            
            return {
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "total_chunks": total_chunks,
                "storage_used_bytes": total_storage_bytes,  # Fixed naming consistency
                "upload_dir_size_bytes": upload_dir_size,
                "average_chunk_size_bytes": float(avg_chunk_size),
                "storage_utilization": total_storage_bytes / (1024**3),  # GB
            }
            
        except Exception as e:
            logger.error(f"Error getting storage statistics: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")
    
    # Private helper methods
    
    async def _validate_file(self, file: UploadFile) -> MediaValidationResponse:
        """Validate uploaded file."""
        errors = []
        warnings = []
        
        # Check file size
        file_content = await file.read()
        file_size = len(file_content)
        await file.seek(0)  # Reset file pointer
        
        if file_size > self.max_file_size:
            errors.append(f"File too large: {file_size} bytes (max: {self.max_file_size})")
        
        if file_size == 0:
            errors.append("Empty file")
        
        # Check file extension
        if file.filename:
            extension = Path(file.filename).suffix.lower().lstrip('.')
            if extension not in self.allowed_extensions:
                errors.append(f"Unsupported file extension: {extension}")
        else:
            errors.append("No filename provided")
        
        # Check content type
        if file.content_type and not file.content_type.startswith('audio/'):
            warnings.append(f"Unexpected content type: {file.content_type}")
        
        return MediaValidationResponse(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            file_info={
                "size_bytes": file_size,
                "content_type": file.content_type,
                "filename": file.filename
            }
        )
    
    async def _save_file(self, file: UploadFile, file_path: Path) -> int:
        """Save uploaded file to disk."""
        file_size = 0
        async with aiofiles.open(file_path, 'wb') as out_file:
            while content := await file.read(8192):  # Read in 8KB chunks
                await out_file.write(content)
                file_size += len(content)
        return file_size
    
    async def _ensure_session_exists(self, db: AsyncSession, session_id: str) -> MediaSession:
        """Ensure session exists, create if not."""
        result = await db.execute(
            select(MediaSession).where(MediaSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            session_data = MediaSessionCreate(session_id=session_id)
            session = await self.create_session(db, session_data)
        
        return session
    
    async def _create_new_chunk(
        self,
        db: AsyncSession,
        session_id: str,
        sequence_index: int,
        file_path: Path,
        file_size: int,
        file_name: str,
        file_extension: str,
        question_id: Optional[str],
        overlap_seconds: float
    ) -> MediaChunk:
        """Create a new media chunk."""
        chunk_data = MediaChunkCreate(
            session_id=session_id,
            sequence_index=sequence_index,
            question_id=question_id,
            overlap_seconds=overlap_seconds,
            file_name=file_name,
            file_extension=file_extension
        )
        
        chunk = MediaChunk(
            **chunk_data.model_dump(),
            file_path=str(file_path),
            file_size_bytes=file_size,
            upload_status="uploaded"
        )
        
        db.add(chunk)
        await db.flush()
        await db.refresh(chunk)
        return chunk
    
    async def _update_existing_chunk(
        self,
        db: AsyncSession,
        chunk: MediaChunk,
        file_path: Path,
        file_size: int,
        file_name: str,
        file_extension: str
    ) -> MediaChunk:
        """Update an existing chunk."""
        # Remove old file if it exists
        if chunk.file_path and Path(chunk.file_path).exists():
            try:
                os.remove(chunk.file_path)
            except Exception as e:
                logger.warning(f"Could not remove old file {chunk.file_path}: {e}")
        
        # Update chunk
        chunk.file_path = str(file_path)
        chunk.file_size_bytes = file_size
        chunk.file_name = file_name
        chunk.file_extension = file_extension
        chunk.upload_status = "uploaded"
        chunk.uploaded_at = datetime.utcnow()
        
        await db.flush()
        await db.refresh(chunk)
        return chunk
    
    async def _update_session_stats(
        self,
        db: AsyncSession,
        session_id: str,
        total_chunks: Optional[int]
    ) -> None:
        """Update session statistics."""
        result = await db.execute(
            select(MediaSession).where(MediaSession.session_id == session_id)
        )
        session = result.scalar_one()
        
        # Count current chunks
        result = await db.execute(
            select(func.count(MediaChunk.id))
            .where(MediaChunk.session_id == session_id)
        )
        current_chunk_count = result.scalar()
        
        # Calculate total duration
        result = await db.execute(
            select(func.sum(MediaChunk.duration_seconds))
            .where(MediaChunk.session_id == session_id)
        )
        total_duration = result.scalar() or 0.0
        
        # Update session
        session.total_chunks = current_chunk_count
        session.total_duration_seconds = total_duration
        if total_chunks:
            session.extra_data = json.dumps({"expected_total_chunks": total_chunks})
        session.updated_at = datetime.utcnow()
    
    async def _handle_session_completion(
        self,
        db: AsyncSession,
        session_id: str
    ) -> None:
        """Handle session completion logic."""
        result = await db.execute(
            select(MediaSession).where(MediaSession.session_id == session_id)
        )
        session = result.scalar_one()
        
        session.session_status = "completed"
        session.completed_at = datetime.utcnow()
        
        logger.info(f"Session {session_id} marked as completed")
        
        # Emit session completion event
        try:
            from app.services.event_service import event_service
            await event_service.emit_session_completed_event(
                session_id=session_id,
                total_chunks=session.total_chunks,
                total_duration_seconds=session.total_duration_seconds
            )
            logger.info(f"Emitted session completion event for session {session_id}")
        except Exception as e:
            logger.warning(f"Failed to emit session completion event: {e}")
        
        # Here you could trigger additional processing:
        # - Send webhook to transcription service
        # - Queue background processing tasks
        # - Notify other services


# Global service instance
media_service = MediaService()

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
            failed_chunks = len([c for c in chunks if c.upload_status == "failed"])
            
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
                chunks=chunks
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting session summary for {session_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_chunks_with_gaps(
        self,
        db: AsyncSession,
        session_id: str
    ) -> List[int]:
        """Find missing chunk sequence indices (gaps) in a session."""
        try:
            # Get all chunks for session
            result = await db.execute(
                select(MediaChunk.sequence_index)
                .where(MediaChunk.session_id == session_id)
                .order_by(MediaChunk.sequence_index)
            )
            existing_indices = [row[0] for row in result.fetchall()]
            
            if not existing_indices:
                return []
            
            # Find gaps
            expected_indices = set(range(min(existing_indices), max(existing_indices) + 1))
            missing_indices = list(expected_indices - set(existing_indices))
            
            return sorted(missing_indices)
            
        except Exception as e:
            logger.error(f"Error finding gaps for session {session_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def cleanup_old_files(
        self,
        db: AsyncSession,
        max_age_days: int = None
    ) -> Dict[str, int]:
        """Clean up old files and database records."""
        try:
            max_age = max_age_days or settings.max_file_age_days
            cutoff_date = datetime.utcnow() - timedelta(days=max_age)
            
            # Find old chunks
            result = await db.execute(
                select(MediaChunk)
                .where(MediaChunk.uploaded_at < cutoff_date)
            )
            old_chunks = result.scalars().all()
            
            deleted_files = 0
            deleted_records = 0
            
            for chunk in old_chunks:
                try:
                    # Delete file if it exists
                    file_path = Path(chunk.file_path)
                    if file_path.exists():
                        file_path.unlink()
                        deleted_files += 1
                        logger.info(f"Deleted old file: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete file {chunk.file_path}: {e}")
                
                # Delete database record
                await db.delete(chunk)
                deleted_records += 1
            
            # Clean up empty session directories
            for session_dir in self.upload_dir.iterdir():
                if session_dir.is_dir() and not any(session_dir.iterdir()):
                    try:
                        session_dir.rmdir()
                        logger.info(f"Removed empty session directory: {session_dir}")
                    except Exception as e:
                        logger.warning(f"Failed to remove directory {session_dir}: {e}")
            
            await db.commit()
            
            return {
                "deleted_files": deleted_files,
                "deleted_records": deleted_records,
                "cutoff_date": cutoff_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_storage_statistics(self, db: AsyncSession) -> Dict[str, any]:
        """Get storage statistics."""
        try:
            # Count sessions and chunks
            session_result = await db.execute(select(func.count(MediaSession.id)))
            total_sessions = session_result.scalar()
            
            chunk_result = await db.execute(select(func.count(MediaChunk.id)))
            total_chunks = chunk_result.scalar()
            
            # Calculate storage usage
            total_size = 0
            chunk_sizes = []
            
            for session_dir in self.upload_dir.iterdir():
                if session_dir.is_dir():
                    for file_path in session_dir.rglob("*"):
                        if file_path.is_file():
                            file_size = file_path.stat().st_size
                            total_size += file_size
                            chunk_sizes.append(file_size)
            
            avg_chunk_size = sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0
            
            return {
                "total_sessions": total_sessions,
                "total_chunks": total_chunks,
                "storage_used_bytes": total_size,
                "storage_used_mb": round(total_size / (1024 * 1024), 2),
                "average_chunk_size_bytes": round(avg_chunk_size, 2),
                "upload_directory": str(self.upload_dir),
                "max_file_size_mb": round(self.max_file_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting storage statistics: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def _validate_file(self, file: UploadFile) -> MediaValidationResponse:
        """Validate uploaded file."""
        errors = []
        warnings = []
        file_info = {}
        
        try:
            # Check file size
            if file.size and file.size > self.max_file_size:
                errors.append(f"File size {file.size} exceeds maximum {self.max_file_size}")
            
            # Check file extension
            if file.filename:
                file_extension = Path(file.filename).suffix.lower().lstrip('.')
                if file_extension not in self.allowed_extensions:
                    errors.append(f"File extension '{file_extension}' not allowed. Allowed: {', '.join(self.allowed_extensions)}")
                file_info["extension"] = file_extension
            
            # Check content type
            if file.content_type:
                file_info["content_type"] = file.content_type
                if not file.content_type.startswith("audio/"):
                    warnings.append(f"Unexpected content type: {file.content_type}")
            
            file_info["size"] = file.size
            file_info["filename"] = file.filename
            
            is_valid = len(errors) == 0
            
            return MediaValidationResponse(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings,
                file_info=file_info
            )
            
        except Exception as e:
            return MediaValidationResponse(
                is_valid=False,
                errors=[f"Validation error: {str(e)}"],
                file_info=file_info
            )
    
    async def _save_file(self, file: UploadFile, file_path: Path) -> int:
        """Save uploaded file to disk."""
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
                return len(content)
        except Exception as e:
            logger.error(f"Error saving file {file_path}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    async def _ensure_session_exists(self, db: AsyncSession, session_id: str) -> MediaSession:
        """Ensure session exists, create if it doesn't."""
        result = await db.execute(
            select(MediaSession).where(MediaSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            # Create session if it doesn't exist
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
        """Create a new chunk record."""
        chunk_data = MediaChunkCreate(
            session_id=session_id,
            question_id=question_id,
            sequence_index=sequence_index,
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
        """Update an existing chunk record."""
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
        try:
            # Get current chunk count
            result = await db.execute(
                select(func.count(MediaChunk.id))
                .where(MediaChunk.session_id == session_id)
            )
            current_chunks = result.scalar()
            
            # Get total duration
            result = await db.execute(
                select(func.sum(MediaChunk.duration_seconds))
                .where(MediaChunk.session_id == session_id)
            )
            total_duration = result.scalar() or 0.0
            
            # Update session
            result = await db.execute(
                select(MediaSession).where(MediaSession.session_id == session_id)
            )
            session = result.scalar_one_or_none()
            
            if session:
                session.total_chunks = total_chunks or current_chunks
                session.total_duration_seconds = total_duration
                session.updated_at = datetime.utcnow()
                
                await db.flush()
                
        except Exception as e:
            logger.error(f"Error updating session stats for {session_id}: {e}")
    
    async def _handle_session_completion(
        self,
        db: AsyncSession,
        session_id: str
    ) -> None:
        """Handle session completion."""
        try:
            result = await db.execute(
                select(MediaSession).where(MediaSession.session_id == session_id)
            )
            session = result.scalar_one_or_none()
            
            if session:
                session.session_status = "completed"
                session.completed_at = datetime.utcnow()
                session.updated_at = datetime.utcnow()
                
                await db.flush()
                
                # Emit session completion event
                try:
                    from app.services.event_service import event_service
                    await event_service.emit_session_completed_event(
                        session_id=session_id,
                        total_chunks=session.total_chunks,
                        total_duration_seconds=session.total_duration_seconds
                    )
                    logger.info(f"Emitted session completion event for {session_id}")
                except Exception as e:
                    logger.warning(f"Failed to emit session completion event: {e}")
                
        except Exception as e:
            logger.error(f"Error handling session completion for {session_id}: {e}")


# Global service instance
media_service = MediaService() 
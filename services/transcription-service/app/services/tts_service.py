import os
import uuid
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from openai import OpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.core.config import settings
from app.models.transcription import TTSRequest
from app.schemas.transcription import TTSRequestIn, TTSRequestOut, TTSCacheInfo


class TTSService:
    """Text-to-Speech service using OpenAI TTS with caching and file management."""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.tts_directory = Path("tts_files")
        self.tts_directory.mkdir(exist_ok=True)
        self.cache_duration_hours = 24  # Cache files for 24 hours
        
    async def generate_tts(
        self, 
        session: AsyncSession, 
        request: TTSRequestIn
    ) -> TTSRequestOut:
        """Generate TTS audio with caching support."""
        
        # Check cache first
        cached_tts = await self._check_cache(session, request)
        if cached_tts:
            print(f"✅ TTS cache hit for text: '{request.text[:50]}...'")
            return TTSRequestOut(
                tts_id=cached_tts.id,
                file_path=cached_tts.file_path,
                url=f"/tts/files/{Path(cached_tts.file_path).name}",
                voice=cached_tts.voice,
                format=cached_tts.format,
                duration=cached_tts.duration,
                file_size=cached_tts.file_size,
                created_at=cached_tts.created_at
            )
        
        # Generate new TTS audio
        print(f"🔊 Generating new TTS for text: '{request.text[:50]}...' with voice: {request.voice}")
        
        try:
            # Create TTS using OpenAI
            response = self.client.audio.speech.create(
                model="tts-1",
                voice=request.voice,
                input=request.text,
                response_format=request.format
            )
            
            # Generate unique filename
            text_hash = hashlib.md5(request.text.encode()).hexdigest()[:8]
            filename = f"{text_hash}_{request.voice}_{uuid.uuid4().hex[:8]}.{request.format}"
            file_path = self.tts_directory / filename
            
            # Save audio file
            with open(file_path, "wb") as f:
                f.write(response.content)
            
            # Get file metadata
            file_size = os.path.getsize(file_path)
            duration = self._estimate_duration(request.text)
            
            # Save to database
            tts_request = TTSRequest(
                text=request.text,
                voice=request.voice,
                format=request.format,
                file_path=str(file_path),
                file_size=file_size,
                duration=duration
            )
            
            session.add(tts_request)
            await session.commit()
            await session.refresh(tts_request)
            
            print(f"✅ TTS generated successfully: {filename} ({file_size} bytes, {duration:.1f}s)")
            
            return TTSRequestOut(
                tts_id=tts_request.id,
                file_path=str(file_path),
                url=f"/tts/files/{filename}",
                voice=request.voice,
                format=request.format,
                duration=duration,
                file_size=file_size,
                created_at=tts_request.created_at
            )
            
        except Exception as e:
            print(f"❌ Error generating TTS: {e}")
            raise Exception(f"TTS generation failed: {str(e)}")
    
    async def _check_cache(
        self, 
        session: AsyncSession, 
        request: TTSRequestIn
    ) -> Optional[TTSRequest]:
        """Check if TTS already exists in cache."""
        
        # Create cache cutoff time
        cache_cutoff = datetime.utcnow() - timedelta(hours=self.cache_duration_hours)
        
        # Query for existing TTS with same parameters
        stmt = select(TTSRequest).where(
            TTSRequest.text == request.text,
            TTSRequest.voice == request.voice,
            TTSRequest.format == request.format,
            TTSRequest.created_at > cache_cutoff
        ).order_by(TTSRequest.created_at.desc())
        
        result = await session.execute(stmt)
        cached_tts = result.scalar_one_or_none()
        
        # Verify file still exists
        if cached_tts and os.path.exists(cached_tts.file_path):
            return cached_tts
        elif cached_tts:
            # File missing, remove from database
            await session.delete(cached_tts)
            await session.commit()
        
        return None
    
    def _estimate_duration(self, text: str) -> float:
        """Estimate audio duration based on text length."""
        # Average speaking rate: ~150 words per minute
        words = len(text.split())
        estimated_seconds = (words / 150) * 60
        return max(1.0, estimated_seconds)  # Minimum 1 second
    
    async def get_cache_info(self, session: AsyncSession) -> TTSCacheInfo:
        """Get TTS cache statistics."""
        
        # Total requests count
        total_stmt = select(func.count(TTSRequest.id))
        total_result = await session.execute(total_stmt)
        total_requests = total_result.scalar() or 0
        
        # Cache size (recent entries)
        cache_cutoff = datetime.utcnow() - timedelta(hours=self.cache_duration_hours)
        cache_stmt = select(func.count(TTSRequest.id)).where(
            TTSRequest.created_at > cache_cutoff
        )
        cache_result = await session.execute(cache_stmt)
        cache_size = cache_result.scalar() or 0
        
        # Oldest cache entry
        oldest_stmt = select(TTSRequest.created_at).where(
            TTSRequest.created_at > cache_cutoff
        ).order_by(TTSRequest.created_at.asc()).limit(1)
        oldest_result = await session.execute(oldest_stmt)
        oldest_entry = oldest_result.scalar_one_or_none()
        
        return TTSCacheInfo(
            cache_hit=False,  # This is set dynamically in requests
            total_requests=total_requests,
            cache_size=cache_size,
            oldest_entry=oldest_entry
        )
    
    async def cleanup_old_files(self, session: AsyncSession) -> Dict[str, int]:
        """Clean up old TTS files and database entries."""
        
        cleanup_cutoff = datetime.utcnow() - timedelta(hours=self.cache_duration_hours * 2)
        
        # Find old entries
        old_stmt = select(TTSRequest).where(
            TTSRequest.created_at < cleanup_cutoff
        )
        old_result = await session.execute(old_stmt)
        old_entries = old_result.scalars().all()
        
        deleted_files = 0
        deleted_records = 0
        
        for entry in old_entries:
            # Delete file if it exists
            if os.path.exists(entry.file_path):
                try:
                    os.remove(entry.file_path)
                    deleted_files += 1
                except OSError as e:
                    print(f"Warning: Could not delete file {entry.file_path}: {e}")
            
            # Delete database record
            await session.delete(entry)
            deleted_records += 1
        
        await session.commit()
        
        print(f"🧹 Cleaned up {deleted_files} files and {deleted_records} database records")
        
        return {
            "deleted_files": deleted_files,
            "deleted_records": deleted_records
        }
    
    async def get_session_tts_history(
        self, 
        session: AsyncSession, 
        session_id: str
    ) -> list[TTSRequestOut]:
        """Get TTS history for a specific interview session."""
        
        stmt = select(TTSRequest).where(
            TTSRequest.session_id == session_id
        ).order_by(TTSRequest.created_at.asc())
        
        result = await session.execute(stmt)
        tts_entries = result.scalars().all()
        
        return [
            TTSRequestOut(
                tts_id=entry.id,
                file_path=entry.file_path,
                url=f"/tts/files/{Path(entry.file_path).name}",
                voice=entry.voice,
                format=entry.format,
                duration=entry.duration,
                file_size=entry.file_size,
                created_at=entry.created_at
            )
            for entry in tts_entries
        ]

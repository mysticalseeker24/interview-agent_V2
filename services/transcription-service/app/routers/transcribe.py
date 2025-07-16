import base64
import json
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ..core.database import get_db
from ..models import Transcription, TTSCache, MediaChunk
from ..schemas.transcription import (
    TranscriptionResponse, TTSRequest, TTSResponse, TTSCacheInfo,
    ChunkUploadRequest, ChunkUploadResponse, SessionCompleteRequest, SessionCompleteResponse
)
from ..services.groq_stt import GroqSTTClient
from ..services.playai_tts import GroqTTSClient
from ..core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/transcribe", tags=["transcription"])

# Initialize clients
groq_client = GroqSTTClient()
groq_tts_client = GroqTTSClient()


@router.post("/", response_model=TranscriptionResponse)
async def transcribe_chunk(
    chunk_id: str = Form(...),
    session_id: str = Form(...),
    sequence_index: int = Form(...),
    overlap_seconds: float = Form(2.0),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Transcribe an audio chunk using Groq Whisper Large v3.
    
    This endpoint accepts audio chunks and returns transcription results.
    Supports chunked processing with overlap for real-time interviews.
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in settings.allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"File type {file_extension} not allowed. Allowed: {settings.allowed_extensions}"
            )
        
        # Read file content
        audio_bytes = await file.read()
        if len(audio_bytes) > settings.max_file_size:
            raise HTTPException(
                status_code=400, 
                detail=f"File too large. Max size: {settings.max_file_size} bytes"
            )
        
        # Transcribe using Groq
        transcription_result = await groq_client.transcribe(
            audio_bytes=audio_bytes,
            response_format="verbose_json"
        )
        
        # Save to database
        transcription = Transcription(
            chunk_id=chunk_id,
            session_id=session_id,
            sequence_index=sequence_index,
            transcript_text=transcription_result["text"],
            confidence=transcription_result.get("confidence"),
            segments=json.dumps(transcription_result.get("segments", [])),
            language=transcription_result.get("language"),
            duration_seconds=transcription_result.get("duration")
        )
        
        db.add(transcription)
        await db.commit()
        await db.refresh(transcription)
        
        logger.info(f"Transcription completed for chunk {chunk_id}")
        
        return TranscriptionResponse(
            transcript=transcription_result["text"],
            segments=transcription_result.get("segments"),
            confidence=transcription_result.get("confidence"),
            language=transcription_result.get("language"),
            duration_seconds=transcription_result.get("duration")
        )
        
    except Exception as e:
        logger.error(f"Transcription failed for chunk {chunk_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@router.post("/chunk", response_model=ChunkUploadResponse)
async def process_chunk(
    request: ChunkUploadRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Process an audio chunk with base64 encoded data.
    
    This endpoint is designed for real-time chunked processing
    with 2-second overlap between chunks.
    """
    try:
        # Decode base64 audio data
        try:
            audio_bytes = base64.b64decode(request.audio_data)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 audio data: {str(e)}")
        
        # Validate chunk size
        if len(audio_bytes) > settings.max_file_size:
            raise HTTPException(
                status_code=400, 
                detail=f"Chunk too large. Max size: {settings.max_file_size} bytes"
            )
        
        # Check if chunk already exists
        existing_chunk = await db.execute(
            select(MediaChunk).where(MediaChunk.chunk_id == request.chunk_id)
        )
        existing_chunk = existing_chunk.scalar_one_or_none()
        
        if existing_chunk:
            return ChunkUploadResponse(
                chunk_id=request.chunk_id,
                session_id=request.session_id,
                sequence_index=request.sequence_index,
                transcription_id=existing_chunk.transcription_id,
                status="already_processed",
                message="Chunk already processed"
            )
        
        # Create media chunk record
        media_chunk = MediaChunk(
            session_id=request.session_id,
            chunk_id=request.chunk_id,
            sequence_index=request.sequence_index
        )
        
        db.add(media_chunk)
        await db.commit()
        await db.refresh(media_chunk)
        
        # Process transcription in background
        background_tasks.add_task(
            _process_chunk_transcription,
            request.chunk_id,
            request.session_id,
            request.sequence_index,
            audio_bytes,
            request.overlap_seconds
        )
        
        return ChunkUploadResponse(
            chunk_id=request.chunk_id,
            session_id=request.session_id,
            sequence_index=request.sequence_index,
            status="processing",
            message="Chunk uploaded and queued for transcription"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chunk processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chunk processing failed: {str(e)}")


async def _process_chunk_transcription(
    chunk_id: str,
    session_id: str,
    sequence_index: int,
    audio_bytes: bytes,
    overlap_seconds: float
):
    """Background task to process chunk transcription."""
    try:
        # Transcribe using Groq
        transcription_result = await groq_client.transcribe(
            audio_bytes=audio_bytes,
            response_format="verbose_json"
        )
        
        # Save to database (using new session)
        from ..core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            transcription = Transcription(
                chunk_id=chunk_id,
                session_id=session_id,
                sequence_index=sequence_index,
                transcript_text=transcription_result["text"],
                confidence=transcription_result.get("confidence"),
                segments=json.dumps(transcription_result.get("segments", [])),
                language=transcription_result.get("language"),
                duration_seconds=transcription_result.get("duration")
            )
            
            db.add(transcription)
            await db.commit()
            await db.refresh(transcription)
            
            # Update media chunk status
            media_chunk = await db.execute(
                select(MediaChunk).where(MediaChunk.chunk_id == chunk_id)
            )
            media_chunk = media_chunk.scalar_one_or_none()
            
            if media_chunk:
                media_chunk.transcription_status = "completed"
                media_chunk.transcription_id = transcription.id
                media_chunk.processed_at = func.now()
                await db.commit()
        
        logger.info(f"Background transcription completed for chunk {chunk_id}")
        
    except Exception as e:
        logger.error(f"Background transcription failed for chunk {chunk_id}: {str(e)}")
        # Update chunk status to failed
        try:
            from ..core.database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                media_chunk = await db.execute(
                    select(MediaChunk).where(MediaChunk.chunk_id == chunk_id)
                )
                media_chunk = media_chunk.scalar_one_or_none()
                
                if media_chunk:
                    media_chunk.transcription_status = "failed"
                    await db.commit()
        except Exception as update_error:
            logger.error(f"Failed to update chunk status: {str(update_error)}")


@router.post("/session-complete", response_model=SessionCompleteResponse)
async def complete_session(
    request: SessionCompleteRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Complete a session and return the full transcript.
    
    This endpoint aggregates all chunks for a session and returns
    the complete transcript with deduplication of overlapping segments.
    """
    try:
        # Get all transcriptions for the session
        transcriptions = await db.execute(
            select(Transcription)
            .where(Transcription.session_id == request.session_id)
            .order_by(Transcription.sequence_index)
        )
        transcriptions = transcriptions.scalars().all()
        
        if not transcriptions:
            raise HTTPException(
                status_code=404, 
                detail=f"No transcriptions found for session {request.session_id}"
            )
        
        # Aggregate transcript with overlap handling
        full_transcript = _aggregate_transcript_with_overlap(transcriptions)
        
        # Calculate overall confidence
        total_confidence = sum(t.confidence or 0.0 for t in transcriptions)
        avg_confidence = total_confidence / len(transcriptions) if transcriptions else 0.0
        
        # Calculate total duration
        total_duration = sum(t.duration_seconds or 0.0 for t in transcriptions)
        
        return SessionCompleteResponse(
            session_id=request.session_id,
            full_transcript=full_transcript,
            total_chunks=len(transcriptions),
            confidence_score=avg_confidence,
            duration_seconds=total_duration
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session completion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Session completion failed: {str(e)}")


def _aggregate_transcript_with_overlap(transcriptions: List[Transcription]) -> str:
    """Aggregate transcriptions with overlap handling."""
    if not transcriptions:
        return ""
    
    # Sort by sequence index
    sorted_transcriptions = sorted(transcriptions, key=lambda t: t.sequence_index)
    
    # Simple aggregation - in production, you'd implement more sophisticated
    # overlap detection and deduplication
    aggregated_text = ""
    
    for i, transcription in enumerate(sorted_transcriptions):
        text = transcription.transcript_text.strip()
        
        if i == 0:
            aggregated_text = text
        else:
            # Simple overlap handling - remove potential duplicates
            # This is a basic implementation; production would use more sophisticated algorithms
            if aggregated_text.endswith(text[:50]):  # Check for overlap
                aggregated_text += text[50:]
            else:
                aggregated_text += " " + text
    
    return aggregated_text.strip()


@router.get("/session/{session_id}/transcript")
async def get_session_transcript(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get the complete transcript for a session."""
    try:
        transcriptions = await db.execute(
            select(Transcription)
            .where(Transcription.session_id == session_id)
            .order_by(Transcription.sequence_index)
        )
        transcriptions = transcriptions.scalars().all()
        
        if not transcriptions:
            raise HTTPException(
                status_code=404, 
                detail=f"No transcriptions found for session {session_id}"
            )
        
        full_transcript = _aggregate_transcript_with_overlap(transcriptions)
        
        return {
            "session_id": session_id,
            "transcript": full_transcript,
            "total_chunks": len(transcriptions),
            "chunks": [
                {
                    "chunk_id": t.chunk_id,
                    "sequence_index": t.sequence_index,
                    "text": t.transcript_text,
                    "confidence": t.confidence,
                    "duration_seconds": t.duration_seconds
                }
                for t in transcriptions
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session transcript: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get session transcript: {str(e)}") 
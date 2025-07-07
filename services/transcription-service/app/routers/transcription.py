from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Dict, Any
import base64
import time

from app.schemas.transcription import (
    Transcription, 
    TranscriptionCreate,
    TranscriptionChunkRequest,
    TranscriptionChunkResponse,
    CompleteSessionRequest,
    SessionCompleteResponse
)
from app.models.transcription import Transcription as TranscriptionModel
from app.services.transcription_service import TranscriptionService
from app.services.integration_service import IntegrationService
from app.services.monitoring import service_monitor, record_transcription_start, record_transcription_success, record_transcription_error, record_session_completion
from app.core.database import get_session
from app.core.config import settings

router = APIRouter()
transcription_service = TranscriptionService()
integration_service = IntegrationService()

# Health and Monitoring Endpoints
@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "transcription-service",
        "version": settings.SERVICE_VERSION,
        "timestamp": time.time()
    }

@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with component status."""
    return await service_monitor.get_service_health()

@router.get("/metrics")
async def get_metrics():
    """Get service metrics and statistics."""
    return await service_monitor.get_service_metrics()

# Transcription Endpoints
@router.post("/", response_model=Transcription)
async def create_transcription(
    transcription: TranscriptionCreate,
    session: AsyncSession = Depends(get_session)
):
    """Create a simple transcription record."""
    new_transcription = TranscriptionModel(
        session_id=transcription.session_id,
        question_id=transcription.question_id,
        transcript_text=transcription.transcript_text
    )
    session.add(new_transcription)
    await session.commit()
    await session.refresh(new_transcription)
    return new_transcription

@router.post("/chunk/{media_chunk_id}", response_model=TranscriptionChunkResponse)
async def transcribe_chunk(
    media_chunk_id: str,
    request: TranscriptionChunkRequest = Body(...),
    session: AsyncSession = Depends(get_session)
):
    """Transcribe a single audio chunk using OpenAI Whisper."""
    # Record transcription start
    await record_transcription_start(request.session_id, media_chunk_id)
    
    start_time = time.time()
    
    try:
        # Use performance monitor
        async with service_monitor.get_performance_monitor(
            "transcribe_chunk", 
            {"session_id": request.session_id, "chunk_id": media_chunk_id}
        ):
            # Decode base64 audio data
            audio_data = base64.b64decode(request.audio_data)
            
            # Transcribe the audio chunk
            transcript_result = await transcription_service.transcribe_audio_chunk(audio_data)
            
            # Save the transcription chunk
            transcription = await transcription_service.save_transcription_chunk(
                session=session,
                session_id=request.session_id,
                media_chunk_id=media_chunk_id,
                sequence_index=request.sequence_index,
                transcript_text=transcript_result["text"],
                segments=transcript_result["segments"],
                confidence_score=transcript_result["confidence_score"],
                question_id=request.question_id
            )
        
        # Record success metrics
        duration_ms = (time.time() - start_time) * 1000
        await record_transcription_success(
            request.session_id, 
            media_chunk_id, 
            duration_ms, 
            transcript_result["confidence_score"]
        )
        
        # Create response
        response = TranscriptionChunkResponse(
            id=transcription.id,
            session_id=transcription.session_id,
            media_chunk_id=transcription.media_chunk_id,
            sequence_index=transcription.sequence_index,
            transcript_text=transcription.transcript_text,
            segments=transcription.segments,
            confidence_score=transcription.confidence_score,
            created_at=transcription.created_at
        )
        
        # Trigger integration hooks if enabled
        if settings.enable_integrations:
            try:
                chunk_data = {
                    "transcript_text": transcription.transcript_text,
                    "question_id": transcription.question_id,
                    "confidence_score": transcription.confidence_score,
                    "media_chunk_id": transcription.media_chunk_id,
                    "sequence_index": transcription.sequence_index
                }
                
                followup_result = await integration_service.notify_chunk_transcribed(
                    session_id=request.session_id,
                    chunk_data=chunk_data
                )
                
                if followup_result:
                    # Add follow-up info to response metadata (optional)
                    response.follow_up_triggered = True
                    response.follow_up_question = followup_result.get("follow_up_question")
                
            except Exception as e:
                # Log integration error but don't fail the main request
                print(f"Integration hook failed: {e}")
        
        return response
    
    except Exception as e:
        # Record error metrics
        error_type = type(e).__name__
        await record_transcription_error(request.session_id, media_chunk_id, error_type)
        
        raise HTTPException(status_code=500, detail=f"Error processing audio chunk: {str(e)}")

@router.post("/session-complete/{session_id}", response_model=SessionCompleteResponse)
async def complete_session(
    session_id: str,
    request: CompleteSessionRequest = Body(...),
    session: AsyncSession = Depends(get_session)
):
    """Aggregate all chunks for a session into a complete transcript."""
    start_time = time.time()
    
    try:
        # Use performance monitor
        async with service_monitor.get_performance_monitor(
            "session_completion", 
            {"session_id": session_id}
        ):
            # Get aggregated transcript
            aggregated_result = await transcription_service.aggregate_session_transcript(
                session=session,
                session_id=session_id
            )
            
            # Create final transcription record (master transcript)
            final_transcription = TranscriptionModel(
                session_id=session_id,
                transcript_text=aggregated_result["full_transcript"],
                segments=aggregated_result["segments"],
                confidence_score=aggregated_result["confidence_score"]
            )
            session.add(final_transcription)
            await session.commit()
            
            # Create response
            response = SessionCompleteResponse(
                session_id=session_id,
                full_transcript=aggregated_result["full_transcript"],
                total_chunks=aggregated_result["total_chunks"],
                confidence_score=aggregated_result["confidence_score"],
                segments=aggregated_result["segments"]
            )
        
        # Record session completion metrics
        duration_ms = (time.time() - start_time) * 1000
        await record_session_completion(
            session_id, 
            aggregated_result["total_chunks"], 
            duration_ms
        )
        
        # Trigger integration hooks if enabled
        if settings.enable_integrations:
            try:
                feedback_result = await integration_service.notify_session_complete(
                    session_id=session_id,
                    session_data=aggregated_result
                )
                
                if feedback_result:
                    # Add feedback info to response metadata (optional)
                    response.feedback_triggered = True
                    response.feedback_task_id = feedback_result.get("task_id")
                
            except Exception as e:
                # Log integration error but don't fail the main request
                print(f"Integration hook failed: {e}")
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error completing session: {str(e)}")

@router.get("/session/{session_id}", response_model=List[Transcription])
async def get_transcriptions_by_session(
    session_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Get all transcriptions for a session."""
    result = await session.execute(
        select(TranscriptionModel)
        .where(TranscriptionModel.session_id == session_id)
        .order_by(TranscriptionModel.sequence_index.asc().nullsfirst())
    )
    transcriptions = result.scalars().all()
    if not transcriptions:
        raise HTTPException(status_code=404, detail="No transcriptions found for this session")
    return transcriptions

@router.get("/session/{session_id}/chunks", response_model=List[TranscriptionChunkResponse])
async def get_session_chunks(
    session_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Get all transcription chunks for a session."""
    chunks = await transcription_service.get_session_chunks(session, session_id)
    
    if not chunks:
        raise HTTPException(status_code=404, detail="No transcription chunks found for this session")
    
    return [
        TranscriptionChunkResponse(
            id=chunk.id,
            session_id=chunk.session_id,
            media_chunk_id=chunk.media_chunk_id,
            sequence_index=chunk.sequence_index,
            transcript_text=chunk.transcript_text,
            segments=chunk.segments,
            confidence_score=chunk.confidence_score,
            created_at=chunk.created_at
        )
        for chunk in chunks
    ]

@router.get("/session/{session_id}/transcript")
async def get_session_transcript(
    session_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Get the aggregated transcript for a session."""
    try:
        aggregated_result = await transcription_service.aggregate_session_transcript(
            session=session,
            session_id=session_id
        )
        return aggregated_result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting session transcript: {str(e)}")

@router.get("/integrations/health")
async def get_integrations_health():
    """Get health status of integrated services."""
    if not settings.enable_integrations:
        return {"integrations": "disabled"}
    
    try:
        health_status = await integration_service.health_check()
        return health_status
    except Exception as e:
        return {"integrations": "error", "message": str(e)}

@router.post("/integrations/test-followup")
async def test_followup_integration(
    session_id: str,
    transcript_text: str = Body(..., embed=True)
):
    """Test follow-up integration manually."""
    if not settings.enable_integrations:
        raise HTTPException(status_code=503, detail="Integrations are disabled")
    
    try:
        result = await integration_service.trigger_followup_generation(
            session_id=session_id,
            transcript_text=transcript_text
        )
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error testing follow-up integration: {str(e)}")

@router.post("/integrations/test-feedback")
async def test_feedback_integration(
    session_id: str,
    regenerate: bool = False
):
    """Test feedback integration manually."""
    if not settings.enable_integrations:
        raise HTTPException(status_code=503, detail="Integrations are disabled")
    
    try:
        result = await integration_service.trigger_feedback_generation(
            session_id=session_id,
            regenerate=regenerate
        )
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error testing feedback integration: {str(e)}")

# Legacy endpoints for backward compatibility
@router.post("/chunk")
async def transcribe_chunk_legacy(
    request: TranscriptionChunkRequest = Body(...),
    session: AsyncSession = Depends(get_session)
):
    """Legacy endpoint for chunk transcription."""
    return await transcribe_chunk(request.media_chunk_id, request, session)

@router.post("/complete")
async def complete_session_legacy(
    request: CompleteSessionRequest = Body(...),
    session: AsyncSession = Depends(get_session)
):
    """Legacy endpoint for session completion."""
    return await complete_session(request.session_id, request, session)

@router.get("/{session_id}", response_model=List[Transcription])
async def get_transcriptions_by_session_legacy(
    session_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Legacy endpoint for getting transcriptions by session."""
    return await get_transcriptions_by_session(session_id, session)

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.database import get_db
from ..services.interview_pipeline import InterviewPipeline
from ..schemas.interview import InterviewRoundRequest, InterviewRoundResponse, PipelineStatusResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/interview", tags=["interview-pipeline"])

# Initialize interview pipeline
interview_pipeline = InterviewPipeline()


@router.post("/round", response_model=InterviewRoundResponse)
async def process_interview_round(
    agent_question: str = Form(...),
    session_id: str = Form(...),
    round_number: int = Form(1),
    user_audio: UploadFile = File(...),
    domain: Optional[str] = Form(None),
    persona_name: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Process one round of the interview pipeline.
    
    This endpoint handles the complete STT → JSON → TTS flow:
    1. Agent asks question (TTS)
    2. User responds (STT)
    3. Response processed into JSON
    4. Agent replies based on JSON (TTS)
    """
    try:
        # Get the persona if domain and persona_name are provided
        persona = None
        if domain and persona_name:
            from app.services.persona_service import persona_service
            persona = persona_service.get_persona(domain, persona_name)
            if not persona:
                logger.warning(f"Persona '{persona_name}' not found for domain '{domain}', using default")
        
        # Read audio file
        audio_bytes = await user_audio.read()
        
        # Process the interview round
        result = await interview_pipeline.process_interview_round(
            agent_question=agent_question,
            user_audio_bytes=audio_bytes,
            session_id=session_id,
            round_number=round_number,
            persona=persona
        )
        
        logger.info(f"Interview round {round_number} processed successfully for session {session_id}")
        
        return InterviewRoundResponse(
            session_id=result["session_id"],
            round_number=result["round_number"],
            agent_question=result["agent_question"],
            agent_question_audio_url=result["agent_question_audio"]["file_url"],
            user_response=result["user_response"],
            agent_reply=result["agent_reply"],
            agent_reply_audio_url=result["agent_reply_audio"]["file_url"],
            timestamp=result["timestamp"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Interview round processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Interview round processing failed: {str(e)}")


@router.get("/status", response_model=PipelineStatusResponse)
async def get_pipeline_status():
    """
    Get the status of the interview pipeline components.
    
    Returns health status of STT and TTS services.
    """
    try:
        status = await interview_pipeline.get_pipeline_status()
        return PipelineStatusResponse(**status)
        
    except Exception as e:
        logger.error(f"Failed to get pipeline status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get pipeline status: {str(e)}")


@router.post("/tts-only")
async def generate_tts_only(
    text: str = Form(...),
    voice: str = Form("Briggs-PlayAI")
):
    """
    Generate TTS audio only (for agent questions).
    
    This endpoint is useful for generating agent questions
    without the full interview pipeline.
    """
    try:
        if not text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        if len(text) > 10000:
            raise HTTPException(status_code=400, detail="Text too long. Max length: 10000 characters")
        
        # Generate TTS
        tts_result = await interview_pipeline.tts_client.synthesize(
            text=text,
            voice=voice,
            format="wav"
        )
        
        return {
            "text": text,
            "voice": voice,
            "audio_url": tts_result["file_url"],
            "file_size_bytes": tts_result["file_size_bytes"],
            "duration_seconds": tts_result["duration_seconds"]
        }
        
    except Exception as e:
        logger.error(f"TTS generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")


@router.post("/stt-only")
async def transcribe_audio_only(
    audio_file: UploadFile = File(...)
):
    """
    Transcribe audio only (for user responses).
    
    This endpoint is useful for transcribing user responses
    without the full interview pipeline.
    """
    try:
        if not audio_file.filename:
            raise HTTPException(status_code=400, detail="No audio file provided")
        
        # Read audio file
        audio_bytes = await audio_file.read()
        if len(audio_bytes) == 0:
            raise HTTPException(status_code=400, detail="Audio file is empty")
        
        # Transcribe
        transcription_result = await interview_pipeline.stt_client.transcribe(
            audio_bytes=audio_bytes,
            response_format="verbose_json"
        )
        
        return {
            "text": transcription_result["text"],
            "confidence": transcription_result.get("confidence", 0.0),
            "segments": transcription_result.get("segments", []),
            "language": transcription_result.get("language", "en"),
            "duration_seconds": transcription_result.get("duration", 0.0)
        }
        
    except Exception as e:
        logger.error(f"STT transcription failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"STT transcription failed: {str(e)}") 
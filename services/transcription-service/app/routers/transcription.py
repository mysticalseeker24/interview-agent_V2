"""
Transcription endpoints for the Transcription Service.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from ..core.database import get_db
from ..core.security import get_current_user
from ..schemas.transcription import TranscriptionRequest, TranscriptionResponse, TranscriptionListResponse
from ..schemas.user import User
from ..services.transcription_service import TranscriptionService
from ..services.database_service import DatabaseService

router = APIRouter(
    prefix="",
    tags=["transcription"],
    responses={404: {"description": "Not found"}},
)

logger = logging.getLogger(__name__)


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    language: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Transcribe audio file using hybrid STT approach.
    
    1. Try OpenAI Whisper first
    2. If any segment confidence < 0.85, fallback to AssemblyAI
    3. Return normalized response with transcript and segments
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith("audio/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an audio file"
            )
        
        # Initialize transcription service
        transcription_service = TranscriptionService()
        
        # Process the transcription
        result = await transcription_service.transcribe_audio(
            file=file,
            language=language,
            user_id=current_user.id
        )
        
        logger.info(f"Transcription completed successfully for user {current_user.id}")
        
        return TranscriptionResponse(**result)
        
    except ValueError as e:
        logger.warning(f"Invalid request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error processing transcription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process transcription: {str(e)}"
        )


@router.get("/", response_model=TranscriptionListResponse)
async def get_transcriptions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all transcriptions for the current user.
    """
    try:
        database_service = DatabaseService()
        
        transcriptions = await database_service.get_user_transcriptions(
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            db=db
        )
        
        total = await database_service.get_user_transcriptions_count(
            user_id=current_user.id,
            db=db
        )
        
        return TranscriptionListResponse(
            transcriptions=[
                TranscriptionResponse(
                    id=t.id,
                    transcript=t.transcript,
                    segments=t.segments,
                    confidence=t.confidence,
                    language=t.language,
                    provider=t.provider,
                    created_at=t.created_at
                )
                for t in transcriptions
            ],
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error fetching transcriptions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch transcriptions: {str(e)}"
        )


@router.get("/{transcription_id}", response_model=TranscriptionResponse)
async def get_transcription(
    transcription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific transcription by ID.
    """
    try:
        database_service = DatabaseService()
        
        transcription = await database_service.get_transcription(
            transcription_id=transcription_id,
            user_id=current_user.id,
            db=db
        )
        
        if not transcription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transcription not found"
            )
        
        return TranscriptionResponse(
            id=transcription.id,
            transcript=transcription.transcript,
            segments=transcription.segments,
            confidence=transcription.confidence,
            language=transcription.language,
            provider=transcription.provider,
            created_at=transcription.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching transcription {transcription_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch transcription: {str(e)}"
        )


@router.delete("/{transcription_id}")
async def delete_transcription(
    transcription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a specific transcription.
    """
    try:
        database_service = DatabaseService()
        
        deleted = await database_service.delete_transcription(
            transcription_id=transcription_id,
            user_id=current_user.id,
            db=db
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transcription not found"
            )
        
        logger.info(f"Transcription {transcription_id} deleted successfully")
        
        return {"message": "Transcription deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting transcription {transcription_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete transcription: {str(e)}"
        )

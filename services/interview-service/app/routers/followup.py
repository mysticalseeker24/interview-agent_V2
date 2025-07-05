"""Follow-up question generation router."""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.followup import (
    FollowUpRequest, 
    FollowUpResponse, 
    SessionQuestionResponse
)
from app.services.dynamic_followup_service import DynamicFollowUpService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/followup", tags=["followup"])


@router.post("/generate", response_model=FollowUpResponse, status_code=status.HTTP_200_OK)
async def generate_followup_question(
    request: FollowUpRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a dynamic follow-up question based on candidate's answer.
    
    This endpoint:
    1. Embeds the candidate's answer using OpenAI
    2. Queries Pinecone for similar follow-up templates
    3. Filters out already asked questions
    4. Optionally uses GPT-4.1 for refinement
    5. Logs the chosen question to prevent repeats
    
    Args:
        request: Follow-up generation request
        db: Database session
        
    Returns:
        Generated follow-up question with metadata
        
    Raises:
        HTTPException: If generation fails
    """
    try:
        followup_service = DynamicFollowUpService(db)
        
        result = await followup_service.generate_followup_question(
            session_id=request.session_id,
            answer_text=request.answer_text,
            use_llm=request.use_llm,
            max_candidates=request.max_candidates
        )
        
        return FollowUpResponse(**result)
        
    except Exception as e:
        logger.error(f"Error generating follow-up question: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate follow-up question: {str(e)}"
        )


@router.get("/history/{session_id}", response_model=List[SessionQuestionResponse])
async def get_session_question_history(
    session_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get the history of questions asked in a session.
    
    Args:
        session_id: Session ID
        db: Database session
        
    Returns:
        List of questions asked in the session
        
    Raises:
        HTTPException: If retrieval fails
    """
    try:
        followup_service = DynamicFollowUpService(db)
        
        history = await followup_service.get_session_question_history(session_id)
        
        return [SessionQuestionResponse(**item) for item in history]
        
    except Exception as e:
        logger.error(f"Error getting session question history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session question history: {str(e)}"
        )


@router.get("/health")
async def followup_health_check():
    """Health check for follow-up service."""
    return {
        "service": "dynamic_followup",
        "status": "healthy",
        "features": {
            "rag_based_selection": True,
            "llm_refinement": True,
            "question_tracking": True,
            "duplicate_prevention": True
        }
    }

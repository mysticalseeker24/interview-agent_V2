"""Session management routers for interview service."""
import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.session import (
    SessionCreate, SessionResponse, NextQuestionResponse, AnswerSubmit
)
from app.schemas.user import UserRead
from app.services.session_service import SessionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/", response_model=SessionResponse)
async def create_session(
    session_data: SessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(get_current_user)
):
    """
    Create a new interview session.
    
    Args:
        session_data: Session creation data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Created session with seeded question queue
    """
    try:
        service = SessionService(db)
        session = await service.create_session(current_user.id, session_data)
        
        logger.info(f"Created session {session.id} for user {current_user.id}")
        
        return SessionResponse(
            id=session.id,
            user_id=session.user_id,
            module_id=session.module_id,
            mode=session.mode,
            status=session.status,
            current_question_index=session.current_question_index,
            estimated_duration_minutes=session.estimated_duration_minutes,
            created_at=session.created_at,
            started_at=session.started_at,
            completed_at=session.completed_at,
            queue_length=len(session.queue)
        )
        
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create session"
        )


@router.get("/{session_id}/next", response_model=NextQuestionResponse)
async def get_next_question(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(get_current_user)
):
    """
    Get the next question for a session.
    
    Args:
        session_id: Session ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Next question or completion status
    """
    try:
        service = SessionService(db)
        response = await service.get_next_question(session_id, current_user.id)
        
        logger.info(f"Retrieved next question for session {session_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting next question: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get next question"
        )


@router.post("/{session_id}/answer")
async def submit_answer(
    session_id: int,
    answer_data: AnswerSubmit,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(get_current_user)
):
    """
    Submit an answer and get the next question.
    
    Args:
        session_id: Session ID
        answer_data: Answer submission data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Response with next question or completion status
    """
    try:
        service = SessionService(db)
        result = await service.submit_answer(session_id, current_user.id, answer_data)
        
        logger.info(f"Submitted answer for session {session_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting answer: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit answer"
        )


@router.get("/{session_id}/status", response_model=SessionResponse)
async def get_session_status(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(get_current_user)
):
    """
    Get session status and progress.
    
    Args:
        session_id: Session ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Session status and progress information
    """
    try:
        service = SessionService(db)
        session = await service._get_session_with_auth(session_id, current_user.id)
        
        return SessionResponse(
            id=session.id,
            user_id=session.user_id,
            module_id=session.module_id,
            mode=session.mode,
            status=session.status,
            current_question_index=session.current_question_index,
            estimated_duration_minutes=session.estimated_duration_minutes,
            created_at=session.created_at,
            started_at=session.started_at,
            completed_at=session.completed_at,
            queue_length=len(session.queue)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get session status"
        )

"""Sessions router for managing interview sessions in TalentSync Interview Service."""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from app.dependencies.auth import get_current_user, User
from app.schemas.interview import Session, SessionCreate, SessionUpdate, NextQuestionResponse
from app.services.session_service import SessionService
from app.services.pinecone_service import PineconeService

router = APIRouter()


@router.post("/", response_model=Session)
async def create_session(
    session_data: SessionCreate
) -> Session:
    """
    Create a new interview session.
    
    Args:
        session_data: Session creation data
        
    Returns:
        Created session
    """
    try:
        session_service = SessionService()
        await session_service.connect()
        
        current_user = await get_current_user()
        session = await session_service.create_session(session_data, current_user.id)
        
        await session_service.disconnect()
        return session
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@router.get("/{session_id}", response_model=Session)
async def get_session(
    session_id: UUID
) -> Session:
    """
    Get session details by ID.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Session details
        
    Raises:
        HTTPException: If session not found or access denied
    """
    try:
        session_service = SessionService()
        await session_service.connect()
        
        session = await session_service.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        current_user = await get_current_user()
        # Check if user owns the session (in dev mode, always allow access)
        # if session.user_id != current_user.id and current_user.role != "admin":
        #     raise HTTPException(status_code=403, detail="Access denied")
        
        await session_service.disconnect()
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve session: {str(e)}")


@router.put("/{session_id}", response_model=Session)
async def update_session(
    session_id: UUID,
    session_updates: SessionUpdate
) -> Session:
    """
    Update session status and metadata.
    
    Args:
        session_id: Session identifier
        session_updates: Session update data
        
    Returns:
        Updated session
        
    Raises:
        HTTPException: If session not found or access denied
    """
    try:
        session_service = SessionService()
        await session_service.connect()
        
        # Check if session exists and user has access
        existing_session = await session_service.get_session(session_id)
        if not existing_session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        current_user = await get_current_user()
        # Check if user owns the session (in dev mode, always allow access)
        # if existing_session.user_id != current_user.id and current_user.role != "admin":
        #     raise HTTPException(status_code=403, detail="Access denied")
        
        # Update session
        updated_session = await session_service.update_session(session_id, session_updates)
        
        if not updated_session:
            raise HTTPException(status_code=500, detail="Failed to update session")
        
        await session_service.disconnect()
        return updated_session
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update session: {str(e)}")


@router.get("/user/sessions", response_model=List[Session])
async def get_user_sessions(
    limit: Optional[int] = Query(50, ge=1, le=100, description="Maximum number of sessions to return")
) -> List[Session]:
    """
    Get user's interview sessions with pagination.
    
    Args:
        limit: Maximum number of sessions to return
        
    Returns:
        List of user's sessions
    """
    try:
        session_service = SessionService()
        await session_service.connect()
        
        current_user = await get_current_user()
        sessions = await session_service.get_user_sessions(current_user.id, limit)
        
        await session_service.disconnect()
        return sessions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve user sessions: {str(e)}")


@router.post("/{session_id}/start")
async def start_session(
    session_id: UUID
) -> JSONResponse:
    """
    Start an interview session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Success response
    """
    try:
        session_service = SessionService()
        await session_service.connect()
        
        current_user = await get_current_user()
        
        # Check if session exists and user has access
        session = await session_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Check if user owns the session (in dev mode, always allow access)
        # if session.user_id != current_user.id and current_user.role != "admin":
        #     raise HTTPException(status_code=403, detail="Access denied")
        
        # Update session status to active
        session_update = SessionUpdate(status="active")
        updated_session = await session_service.update_session(session_id, session_update)
        
        if not updated_session:
            raise HTTPException(status_code=500, detail="Failed to start session")
        
        await session_service.disconnect()
        
        return JSONResponse(
            status_code=200,
            content={"message": "Session started successfully", "session_id": str(session_id)}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start session: {str(e)}")


@router.post("/{session_id}/complete")
async def complete_session(
    session_id: UUID
) -> JSONResponse:
    """
    Complete an interview session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Success response
    """
    try:
        session_service = SessionService()
        await session_service.connect()
        
        current_user = await get_current_user()
        
        # Check if session exists and user has access
        session = await session_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Check if user owns the session (in dev mode, always allow access)
        # if session.user_id != current_user.id and current_user.role != "admin":
        #     raise HTTPException(status_code=403, detail="Access denied")
        
        # Update session status to completed
        session_update = SessionUpdate(status="completed")
        updated_session = await session_service.update_session(session_id, session_update)
        
        if not updated_session:
            raise HTTPException(status_code=500, detail="Failed to complete session")
        
        await session_service.disconnect()
        
        return JSONResponse(
            status_code=200,
            content={"message": "Session completed successfully", "session_id": str(session_id)}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete session: {str(e)}")


@router.post("/{session_id}/cancel")
async def cancel_session(
    session_id: UUID
) -> JSONResponse:
    """
    Cancel an interview session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Success response
    """
    try:
        session_service = SessionService()
        await session_service.connect()
        
        current_user = await get_current_user()
        
        # Check if session exists and user has access
        session = await session_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Check if user owns the session (in dev mode, always allow access)
        # if session.user_id != current_user.id and current_user.role != "admin":
        #     raise HTTPException(status_code=403, detail="Access denied")
        
        # Update session status to cancelled
        session_update = SessionUpdate(status="cancelled")
        updated_session = await session_service.update_session(session_id, session_update)
        
        if not updated_session:
            raise HTTPException(status_code=500, detail="Failed to cancel session")
        
        await session_service.disconnect()
        
        return JSONResponse(
            status_code=200,
            content={"message": "Session cancelled successfully", "session_id": str(session_id)}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel session: {str(e)}")


@router.delete("/{session_id}")
async def delete_session(
    session_id: UUID
) -> JSONResponse:
    """
    Delete a session (admin only or session owner).
    
    Args:
        session_id: Session identifier
        
    Returns:
        Success response
    """
    try:
        session_service = SessionService()
        await session_service.connect()
        
        # Check if session exists
        session = await session_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        current_user = await get_current_user()
        # Check if user has permission to delete (in dev mode, always allow access)
        # if session.user_id != current_user.id and current_user.role != "admin":
        #     raise HTTPException(status_code=403, detail="Access denied")
        
        # Delete session
        success = await session_service.delete_session(session_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete session")
        
        await session_service.disconnect()
        
        return JSONResponse(
            status_code=200,
            content={"message": "Session deleted successfully", "session_id": str(session_id)}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")


@router.get("/{session_id}/next-question", response_model=NextQuestionResponse)
async def get_next_question(
    session_id: UUID
) -> NextQuestionResponse:
    """
    Get the next question for an active session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Next question and session status
    """
    try:
        session_service = SessionService()
        await session_service.connect()
        
        # Check if session exists and user has access
        session = await session_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        current_user = await get_current_user()
        # Check if user owns the session (in dev mode, always allow access)
        # if session.user_id != current_user.id and current_user.role != "admin":
        #     raise HTTPException(status_code=403, detail="Access denied")
        
        # Check if session is active
        if session.status != "active":
            raise HTTPException(status_code=400, detail="Session is not active")
        
        # For now, return a mock response
        # In production, this would integrate with the question service
        response = NextQuestionResponse(
            question=None,  # Would be populated by question service
            session=session,
            is_complete=False,
            remaining_questions=10,  # Mock value
            estimated_time_remaining_minutes=30  # Mock value
        )
        
        await session_service.disconnect()
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get next question: {str(e)}") 
"""Post-interview feedback generation router."""
import logging
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.feedback import (
    FeedbackGenerationRequest,
    FeedbackGenerationResponse,
    FeedbackStatusResponse,
    FeedbackReportResponse,
    FeedbackScoresResponse
)
from app.tasks.feedback import generate_feedback
from app.tasks import celery_app
from app.models.session import Session
from app.models.feedback_report import FeedbackReport
from app.models.score import Score
from sqlalchemy import select

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/feedback", tags=["feedback"])


@router.post("/generate", response_model=FeedbackGenerationResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_feedback_generation(
    request: FeedbackGenerationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Start asynchronous feedback generation for a completed interview session.
    
    This endpoint:
    1. Validates that the session exists and is completed
    2. Checks if feedback has already been generated
    3. Starts a Celery task for feedback generation
    4. Returns task ID for progress tracking
    
    Args:
        request: Feedback generation request
        db: Database session
        
    Returns:
        Task information for tracking feedback generation progress
        
    Raises:
        HTTPException: If session not found, not completed, or feedback already exists
    """
    try:
        # Verify session exists and is completed
        session_query = select(Session).where(Session.id == request.session_id)
        result = await db.execute(session_query)
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {request.session_id} not found"
            )
        
        if session.status != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Session {request.session_id} is not completed. Status: {session.status}"
            )
        
        # Check if feedback already exists
        feedback_query = select(FeedbackReport).where(FeedbackReport.session_id == request.session_id)
        result = await db.execute(feedback_query)
        existing_feedback = result.scalar_one_or_none()
        
        if existing_feedback and not request.regenerate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Feedback already exists for session {request.session_id}. Use regenerate=true to overwrite."
            )
        
        # Start Celery task
        task = generate_feedback.delay(request.session_id)
        
        logger.info(f"Started feedback generation task {task.id} for session {request.session_id}")
        
        return FeedbackGenerationResponse(
            task_id=task.id,
            session_id=request.session_id,
            status="PENDING",
            message="Feedback generation started"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting feedback generation for session {request.session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start feedback generation"
        )


@router.get("/status/{task_id}", response_model=FeedbackStatusResponse)
async def get_feedback_status(task_id: str):
    """
    Get the status of a feedback generation task.
    
    Args:
        task_id: Celery task ID
        
    Returns:
        Current task status and progress information
        
    Raises:
        HTTPException: If task not found
    """
    try:
        task_result = celery_app.AsyncResult(task_id)
        
        if task_result.state == "PENDING":
            response = FeedbackStatusResponse(
                task_id=task_id,
                status="PENDING",
                progress=0,
                message="Task is pending execution"
            )
        elif task_result.state == "PROGRESS":
            response = FeedbackStatusResponse(
                task_id=task_id,
                status="PROGRESS",
                progress=task_result.info.get("progress", 0),
                step=task_result.info.get("step", ""),
                message=task_result.info.get("message", "Processing...")
            )
        elif task_result.state == "SUCCESS":
            response = FeedbackStatusResponse(
                task_id=task_id,
                status="SUCCESS",
                progress=100,
                message="Feedback generation completed successfully",
                result=task_result.result
            )
        elif task_result.state == "FAILURE":
            response = FeedbackStatusResponse(
                task_id=task_id,
                status="FAILURE",
                progress=0,
                message=f"Task failed: {str(task_result.info)}",
                error=str(task_result.info)
            )
        else:
            response = FeedbackStatusResponse(
                task_id=task_id,
                status=task_result.state,
                progress=0,
                message=f"Task in state: {task_result.state}"
            )
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting task status for {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get task status"
        )


@router.get("/report/{session_id}", response_model=FeedbackReportResponse)
async def get_feedback_report(
    session_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve the complete feedback report for a session.
    
    Args:
        session_id: Session ID
        db: Database session
        
    Returns:
        Complete feedback report with scores and AI narrative
        
    Raises:
        HTTPException: If session or feedback report not found
    """
    try:
        # Get feedback report
        feedback_query = select(FeedbackReport).where(FeedbackReport.session_id == session_id)
        result = await db.execute(feedback_query)
        feedback_report = result.scalar_one_or_none()
        
        if not feedback_report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feedback report not found for session {session_id}"
            )
        
        # Get session info
        session_query = select(Session).where(Session.id == session_id)
        result = await db.execute(session_query)
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        
        return FeedbackReportResponse(
            session_id=session_id,
            candidate_name=session.candidate_name,
            module_name=session.module.name if session.module else "Unknown",
            avg_correctness=feedback_report.avg_correctness,
            avg_fluency=feedback_report.avg_fluency,
            avg_depth=feedback_report.avg_depth,
            overall_score=feedback_report.overall_score,
            correctness_percentile=feedback_report.correctness_percentile,
            fluency_percentile=feedback_report.fluency_percentile,
            depth_percentile=feedback_report.depth_percentile,
            overall_percentile=feedback_report.overall_percentile,
            report_text=feedback_report.report_text,
            strengths=feedback_report.strengths or [],
            areas_for_improvement=feedback_report.areas_for_improvement or [],
            recommendations=feedback_report.recommendations or [],
            generated_at=feedback_report.generated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving feedback report for session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve feedback report"
        )


@router.get("/scores/{session_id}", response_model=FeedbackScoresResponse)
async def get_feedback_scores(
    session_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed per-question scores for a session.
    
    Args:
        session_id: Session ID
        db: Database session
        
    Returns:
        Detailed breakdown of scores per question
        
    Raises:
        HTTPException: If session not found or no scores available
    """
    try:
        # Verify session exists
        session_query = select(Session).where(Session.id == session_id)
        result = await db.execute(session_query)
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        
        # Get all scores for the session
        scores_query = select(Score).where(Score.session_id == session_id).order_by(Score.id)
        result = await db.execute(scores_query)
        scores = result.scalars().all()
        
        if not scores:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No scores found for session {session_id}"
            )
        
        return FeedbackScoresResponse(
            session_id=session_id,
            scores=[
                {
                    "question_id": score.question_id,
                    "response_id": score.response_id,
                    "correctness": score.correctness,
                    "fluency": score.fluency,
                    "depth": score.depth,
                    "word_count": score.word_count,
                    "duration_seconds": score.duration_seconds,
                    "words_per_minute": score.words_per_minute,
                    "computed_at": score.computed_at
                }
                for score in scores
            ]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving scores for session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve scores"
        )


@router.delete("/report/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_feedback_report(
    session_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a feedback report and associated scores for a session.
    
    Args:
        session_id: Session ID
        db: Database session
        
    Raises:
        HTTPException: If feedback report not found
    """
    try:
        # Check if feedback report exists
        feedback_query = select(FeedbackReport).where(FeedbackReport.session_id == session_id)
        result = await db.execute(feedback_query)
        feedback_report = result.scalar_one_or_none()
        
        if not feedback_report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feedback report not found for session {session_id}"
            )
        
        # Delete associated scores first (due to foreign key constraints)
        scores_query = select(Score).where(Score.session_id == session_id)
        result = await db.execute(scores_query)
        scores = result.scalars().all()
        
        for score in scores:
            await db.delete(score)
        
        # Delete feedback report
        await db.delete(feedback_report)
        await db.commit()
        
        logger.info(f"Deleted feedback report and {len(scores)} scores for session {session_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting feedback report for session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete feedback report"
        )


@router.get("/health")
async def feedback_health():
    """Health check endpoint for feedback service."""
    try:
        # Check Celery connection
        inspector = celery_app.control.inspect()
        active_tasks = inspector.active()
        
        return {
            "status": "healthy",
            "service": "feedback-generation",
            "celery_workers": len(active_tasks) if active_tasks else 0,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Feedback health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Feedback service unhealthy"
        )

"""
Router for vector embedding and question syncing operations.
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.embedding_service import EmbeddingService
from app.schemas.question import QuestionSync, QuestionResponse, QuestionSyncBatch

router = APIRouter()
embedding_service = EmbeddingService()

@router.post("/sync/question", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def sync_question(
    question: QuestionSync,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Sync a question to Pinecone vector database.
    
    This endpoint can be called after question creation or update
    to ensure the embedding is synced to Pinecone.
    """
    # Sync in background to avoid blocking
    background_tasks.add_task(
        embedding_service.sync_question_on_create, 
        question_data=question.dict()
    )
    
    return {
        "status": "success",
        "message": f"Question {question.id} sync started in background"
    }

@router.post("/sync/questions/batch", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def sync_questions_batch(
    batch: QuestionSyncBatch,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Sync a batch of questions to Pinecone vector database.
    
    This endpoint is useful for bulk operations or migrations.
    """
    # Sync in background to avoid blocking
    background_tasks.add_task(
        embedding_service.batch_sync_questions, 
        questions=batch.questions
    )
    
    return {
        "status": "success",
        "message": f"Batch sync of {len(batch.questions)} questions started in background"
    }

@router.post("/sync/questions/all", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def sync_all_questions(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Sync all questions to Pinecone vector database.
    
    This endpoint is useful for initial setup or full reindexing.
    """
    # Sync in background to avoid blocking
    background_tasks.add_task(
        embedding_service.continuous_sync_worker,
        batch_size=100
    )
    
    return {
        "status": "success",
        "message": "Full sync of all questions started in background"
    }

@router.get("/followups", response_model=List[int])
async def get_followup_questions(
    answer: str,
    asked: str = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Get follow-up questions based on an answer.
    
    Args:
        answer: The candidate's answer text
        asked: Comma-separated list of already asked question IDs
    
    Returns:
        List of recommended follow-up question IDs
    """
    # Convert comma-separated string to set if provided
    asked_ids = set()
    if asked:
        try:
            asked_ids = {int(id_str) for id_str in asked.split(',') if id_str.strip()}
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid format for asked parameter. Expected comma-separated integers."
            )
    
    # Get followups
    followups = await embedding_service.retrieve_followups(answer, asked_ids)
    
    return followups

@router.get("/search", response_model=List[Dict[str, Any]])
async def search_questions(
    query: str,
    domain: str = None,
    question_type: str = None,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """
    Search questions by semantic similarity.
    
    Args:
        query: Search query text
        domain: Optional domain filter
        question_type: Optional question type filter
        limit: Maximum number of results (default: 10)
    
    Returns:
        List of matching questions with similarity scores
    """
    filters = {}
    if domain:
        filters["domain"] = domain
    if question_type:
        filters["type"] = question_type
        
    results = await embedding_service.search_questions_by_content(
        search_text=query,
        filters=filters,
        limit=limit
    )
    
    return results

@router.get("/health", response_model=Dict[str, Any])
async def check_health():
    """
    Check health of embedding and vector search services.
    """
    health = await embedding_service.health_check()
    return health

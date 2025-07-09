"""
Database trigger for question sync via REST API.
This module contains functions for synchronizing questions between SQLite and Pinecone.
"""
import logging
import asyncio
import httpx
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, event
from app.models.question import Question

logger = logging.getLogger(__name__)

# Sync API endpoints
SYNC_QUESTION_ENDPOINT = "http://localhost:8002/api/vectors/sync/question"
BATCH_SYNC_ENDPOINT = "http://localhost:8002/api/vectors/sync/questions/batch"


async def sync_question_via_api(question_id: int, question_text: str, domain: str, 
                              question_type: str, difficulty: Optional[str] = None) -> bool:
    """
    Sync a question to Pinecone via the REST API.
    
    Args:
        question_id: Unique question identifier
        question_text: The question text
        domain: Question domain
        question_type: Type of question
        difficulty: Optional difficulty level
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Prepare payload
        payload = {
            "id": question_id,
            "text": question_text,
            "domain": domain,
            "type": question_type
        }
        
        if difficulty:
            payload["difficulty"] = difficulty
            
        # Make API call
        async with httpx.AsyncClient() as client:
            response = await client.post(
                SYNC_QUESTION_ENDPOINT,
                json=payload,
                timeout=10.0
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully synced question {question_id} via API")
                return True
            else:
                logger.error(f"Error syncing question {question_id}: {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"Error calling question sync API: {str(e)}")
        return False


# SQLAlchemy event listeners for automatic sync
@event.listens_for(Question, 'after_insert')
def question_after_insert(mapper, connection, target):
    """
    Trigger after a question is inserted.
    
    Args:
        mapper: SQLAlchemy mapper
        connection: SQLAlchemy connection
        target: Question instance
    """
    # Create async task to sync question
    question_id = target.id
    question_text = target.text
    domain = target.domain
    question_type = target.type
    difficulty = target.difficulty
    
    # Schedule async task to call API
    # Note: Since SQLAlchemy events are synchronous, we need to create a task
    # We could use BackgroundTasks here if available
    loop = asyncio.get_event_loop()
    task = loop.create_task(
        sync_question_via_api(
            question_id=question_id,
            question_text=question_text,
            domain=domain,
            question_type=question_type,
            difficulty=difficulty
        )
    )


@event.listens_for(Question, 'after_update')
def question_after_update(mapper, connection, target):
    """
    Trigger after a question is updated.
    
    Args:
        mapper: SQLAlchemy mapper
        connection: SQLAlchemy connection
        target: Question instance
    """
    # Same logic as after_insert - sync the updated question
    question_id = target.id
    question_text = target.text
    domain = target.domain
    question_type = target.type
    difficulty = target.difficulty
    
    # Schedule async task to call API
    loop = asyncio.get_event_loop()
    task = loop.create_task(
        sync_question_via_api(
            question_id=question_id,
            question_text=question_text,
            domain=domain,
            question_type=question_type,
            difficulty=difficulty
        )
    )

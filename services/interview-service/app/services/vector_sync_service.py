"""
Vector Sync Service for continuous synchronization of question embeddings.
Provides efficient sync operations via REST APIs.
"""
import os
import json
import logging
import asyncio
import httpx
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.embedding_service import EmbeddingService
from app.core.database import get_db

logger = logging.getLogger(__name__)

class VectorSyncService:
    """Service for continuous synchronization between SQLite and Pinecone via REST APIs."""
    
    def __init__(self):
        """Initialize the vector sync service."""
        self.embedding_service = EmbeddingService()
        self.service_url = os.getenv('INTERVIEW_SERVICE_URL', 'http://localhost:8002')
        self.sync_endpoint = f"{self.service_url}/api/v1/vectors/sync/question"
        self.batch_sync_endpoint = f"{self.service_url}/api/v1/vectors/sync/questions/batch"
        logger.info("Vector sync service initialized")
    
    async def schedule_sync(self, db: AsyncSession = None):
        """Schedule synchronization for all questions that need updating."""
        try:
            if db is None:
                db = await get_db().__anext__()
            
            # Query for questions needing sync
            from sqlalchemy import text
            query = """
                SELECT id, text, domain, question_type as type, difficulty 
                FROM questions
                WHERE last_synced IS NULL OR updated_at > last_synced
                ORDER BY updated_at DESC
                LIMIT 100
            """
            
            result = await db.execute(text(query))
            questions = result.fetchall()
            
            logger.info(f"Found {len(questions)} questions that need synchronization")
            
            # Process in batches
            if questions:
                # Group questions into batches of 10
                batch_size = 10
                for i in range(0, len(questions), batch_size):
                    batch = questions[i:i+batch_size]
                    batch_data = []
                    
                    for question in batch:
                        q_id, text, domain, q_type, difficulty = question
                        batch_data.append({
                            "id": q_id,
                            "text": text,
                            "domain": domain,
                            "type": q_type,
                            "difficulty": difficulty
                        })
                    
                    # Call batch sync endpoint
                    await self.sync_batch(batch_data)
                    
                    # Update sync status in database
                    for question in batch:
                        q_id = question[0]
                        update_query = """
                            UPDATE questions
                            SET last_synced = CURRENT_TIMESTAMP
                            WHERE id = :question_id
                        """
                        await db.execute(text(update_query), {"question_id": q_id})
                    
                    await db.commit()
                    logger.info(f"Synced batch of {len(batch)} questions")
                    
                logger.info(f"Completed synchronization of {len(questions)} questions")
                return True
            else:
                logger.info("No questions need synchronization")
                return False
                
        except Exception as e:
            logger.error(f"Error scheduling sync: {str(e)}")
            return False
    
    async def sync_question(self, question_data: Dict[str, Any]):
        """
        Sync a single question via REST API.
        
        Args:
            question_data: Question data including id, text, domain, type
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.sync_endpoint,
                    json=question_data,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.info(f"Successfully synced question {question_data['id']} via API")
                    return True
                else:
                    logger.error(f"Error syncing question {question_data['id']}: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error calling question sync API: {str(e)}")
            return False
    
    async def sync_batch(self, questions: List[Dict[str, Any]]):
        """
        Sync a batch of questions via REST API.
        
        Args:
            questions: List of question data dictionaries
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.batch_sync_endpoint,
                    json={"questions": questions},
                    timeout=30.0  # Longer timeout for batch operations
                )
                
                if response.status_code == 200:
                    logger.info(f"Successfully synced batch of {len(questions)} questions via API")
                    return True
                else:
                    logger.error(f"Error syncing batch: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error calling batch sync API: {str(e)}")
            return False
    
    async def direct_sync_question(self, question_id: int, question_text: str, 
                                 domain: str, question_type: str, 
                                 difficulty: Optional[str] = None):
        """
        Directly sync a question to Pinecone without going through the API.
        Useful for in-process synchronization.
        
        Args:
            question_id: Unique question identifier
            question_text: The question text
            domain: Question domain
            question_type: Type of question
            difficulty: Optional difficulty level
        """
        try:
            # Directly use embedding service
            await self.embedding_service.sync_question_on_create({
                'id': question_id,
                'text': question_text,
                'domain': domain,
                'type': question_type,
                'difficulty': difficulty
            })
            
            logger.info(f"Directly synced question {question_id} to Pinecone")
            return True
            
        except Exception as e:
            logger.error(f"Error directly syncing question {question_id}: {str(e)}")
            return False
    
    async def schedule_periodic_sync(self, interval_seconds: int = 300):
        """
        Schedule periodic synchronization of questions.
        
        Args:
            interval_seconds: Interval between sync operations in seconds
        """
        try:
            while True:
                logger.info(f"Running scheduled sync (interval: {interval_seconds}s)")
                await self.schedule_sync()
                await asyncio.sleep(interval_seconds)
                
        except Exception as e:
            logger.error(f"Error in periodic sync: {str(e)}")
            
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of vector sync service.
        
        Returns:
            Health status dictionary
        """
        try:
            # Check Pinecone health via embedding service
            embedding_health = await self.embedding_service.health_check()
            
            # Check API endpoints
            api_health = "healthy"
            api_details = {}
            
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.service_url}/api/v1/vectors/health",
                        timeout=5.0
                    )
                    if response.status_code != 200:
                        api_health = "unhealthy"
                        api_details["error"] = f"Status code: {response.status_code}"
            except Exception as e:
                api_health = "unhealthy"
                api_details["error"] = str(e)
            
            return {
                "vector_sync_service": "healthy",
                "embedding_service": embedding_health,
                "api_endpoints": {
                    "status": api_health,
                    "details": api_details
                },
                "overall_status": "healthy" if api_health == "healthy" and 
                                            embedding_health.get("overall_status") == "healthy" 
                                        else "unhealthy"
            }
            
        except Exception as e:
            logger.error(f"Vector sync service health check failed: {str(e)}")
            return {
                "vector_sync_service": "unhealthy",
                "error": str(e),
                "overall_status": "unhealthy"
            }

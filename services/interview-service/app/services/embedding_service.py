"""
Embedding service for continuous sync and semantic retrieval.
Handles question embeddings and RAG orchestration for the interview system.
"""
import logging
import asyncio
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.services.pinecone_service import PineconeService
from app.core.database import get_db

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for handling embeddings and continuous sync with Pinecone."""
    
    def __init__(self):
        """Initialize embedding service."""
        self.pinecone_service = PineconeService()
        logger.info("Embedding service initialized")
    
    async def sync_question_on_create(self, question_data: Dict[str, Any]) -> bool:
        """
        Sync question to Pinecone when created.
        
        Args:
            question_data: Question data including id, text, domain, type
            
        Returns:
            True if sync successful, False otherwise
        """
        try:
            await self.pinecone_service.sync_question_to_pinecone(
                question_id=question_data['id'],
                question_text=question_data['text'],
                domain=question_data.get('domain', 'general'),
                question_type=question_data.get('type', 'general'),
                difficulty=question_data.get('difficulty')
            )
            
            logger.info(f"Successfully synced question {question_data['id']} on create")
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync question {question_data['id']} on create: {str(e)}")
            return False
    
    async def sync_question_on_update(self, question_data: Dict[str, Any]) -> bool:
        """
        Sync question to Pinecone when updated.
        
        Args:
            question_data: Updated question data
            
        Returns:
            True if sync successful, False otherwise
        """
        try:
            # For updates, we upsert with the same ID to overwrite
            await self.pinecone_service.sync_question_to_pinecone(
                question_id=question_data['id'],
                question_text=question_data['text'],
                domain=question_data.get('domain', 'general'),
                question_type=question_data.get('type', 'general'),
                difficulty=question_data.get('difficulty')
            )
            
            logger.info(f"Successfully synced question {question_data['id']} on update")
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync question {question_data['id']} on update: {str(e)}")
            return False
    
    async def batch_sync_questions(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Batch sync multiple questions to Pinecone.
        
        Args:
            questions: List of question dictionaries
            
        Returns:
            Sync results summary
        """
        successful = 0
        failed = 0
        errors = []
        
        for question in questions:
            try:
                success = await self.sync_question_on_create(question)
                if success:
                    successful += 1
                else:
                    failed += 1
                    
            except Exception as e:
                failed += 1
                errors.append(f"Question {question.get('id', 'unknown')}: {str(e)}")
        
        results = {
            'total_questions': len(questions),
            'successful': successful,
            'failed': failed,
            'errors': errors
        }
        
        logger.info(f"Batch sync completed: {results}")
        return results
    
    async def get_semantic_follow_ups(self, session_id: int, answer_text: str, 
                                    session_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get semantically relevant follow-up questions based on candidate answer.
        
        Args:
            session_id: Current session ID
            answer_text: Candidate's answer text
            session_context: Session context with domain, difficulty, etc.
            
        Returns:
            List of relevant follow-up questions
        """
        try:
            # TODO: Get already asked question IDs from session
            exclude_ids = []  # This would come from session service
            
            follow_ups = await self.pinecone_service.get_follow_up_questions(
                answer_text=answer_text,
                session_context=session_context,
                exclude_ids=exclude_ids
            )
            
            logger.info(f"Retrieved {len(follow_ups)} follow-up questions for session {session_id}")
            return follow_ups
            
        except Exception as e:
            logger.error(f"Error getting semantic follow-ups for session {session_id}: {str(e)}")
            return []
    
    async def search_questions_by_content(self, search_text: str, filters: Dict[str, Any] = None,
                                        limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search questions by content using semantic similarity.
        
        Args:
            search_text: Text to search for
            filters: Optional filters (domain, type, difficulty)
            limit: Maximum number of results
            
        Returns:
            List of matching questions
        """
        try:
            domain = filters.get('domain') if filters else None
            question_type = filters.get('type') if filters else None
            
            results = await self.pinecone_service.search_similar_questions(
                query_text=search_text,
                domain=domain,
                question_type=question_type,
                top_k=limit
            )
            
            logger.info(f"Found {len(results)} questions for search: '{search_text[:50]}...'")
            return results
            
        except Exception as e:
            logger.error(f"Error searching questions by content: {str(e)}")
            return []
    
    async def continuous_sync_worker(self, batch_size: int = 100) -> None:
        """
        Background worker for continuous synchronization of questions.
        This is executed via REST API endpoint.
        
        Args:
            batch_size: Number of questions to process in each batch
        """
        try:
            logger.info(f"Starting continuous sync worker with batch size {batch_size}")
            
            # Get questions that need sync
            from sqlalchemy import text
            from app.core.database import async_session
            
            async with async_session() as session:
                # Get questions that need sync - either new or updated
                # We're assuming there's a last_synced column in the questions table
                query = """
                    SELECT id, text, domain, type, difficulty 
                    FROM questions
                    WHERE last_synced IS NULL OR updated_at > last_synced
                    ORDER BY updated_at DESC
                    LIMIT :limit
                """
                
                result = await session.execute(text(query), {"limit": batch_size})
                questions = result.fetchall()
                
                logger.info(f"Found {len(questions)} questions that need sync")
                
                # Process them in batches
                processed = 0
                for question in questions:
                    question_id, text, domain, q_type, difficulty = question
                    
                    # Sync to Pinecone
                    await self.pinecone_service.sync_question_to_pinecone(
                        question_id=question_id,
                        question_text=text,
                        domain=domain,
                        question_type=q_type,
                        difficulty=difficulty
                    )
                    
                    # Update sync status
                    update_query = """
                        UPDATE questions
                        SET last_synced = NOW()
                        WHERE id = :question_id
                    """
                    await session.execute(text(update_query), {"question_id": question_id})
                    
                    processed += 1
                    
                    if processed % 10 == 0:
                        logger.info(f"Synced {processed}/{len(questions)} questions")
                
                # Commit changes
                await session.commit()
                
            logger.info(f"Continuous sync worker completed. Synced {processed} questions.")
            
        except Exception as e:
            logger.error(f"Error in continuous sync worker: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Health check for embedding service and Pinecone connection.
        
        Returns:
            Health status
        """
        try:
            pinecone_health = await self.pinecone_service.health_check()
            
            return {
                'embedding_service': 'healthy',
                'pinecone': pinecone_health,
                'overall_status': 'healthy' if pinecone_health['healthy'] else 'unhealthy'
            }
            
        except Exception as e:
            logger.error(f"Embedding service health check failed: {str(e)}")
            return {
                'embedding_service': 'unhealthy',
                'error': str(e),
                'overall_status': 'unhealthy'
            }
    
    async def retrieve_followups(self, answer: str, asked: set = None) -> List[int]:
        """
        Retrieve follow-up questions based on answer, excluding already asked questions.
        
        Args:
            answer: Candidate's answer text
            asked: Set of question IDs that have already been asked
            
        Returns:
            List of question IDs for follow-up questions
        """
        try:
            if asked is None:
                asked = set()
                
            # Get embedding for answer
            emb = self.pinecone_service.get_embedding(answer)
            
            # Query Pinecone for similar questions
            results = self.pinecone_service.questions_index.query(
                vector=emb,
                top_k=10,
                include_metadata=True
            )
            
            # Filter out already asked questions
            candidates = [int(match.id) for match in results.matches if int(match.id) not in asked]
            
            logger.info(f"Retrieved {len(candidates)} follow-up question candidates")
            return candidates
            
        except Exception as e:
            logger.error(f"Error retrieving followups: {str(e)}")
            return []

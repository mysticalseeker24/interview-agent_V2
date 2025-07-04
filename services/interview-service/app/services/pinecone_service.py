"""
Pinecone vector database service for TalentSync Interview Service.
Handles embeddings, indexing, and semantic retrieval for questions.
"""
import logging
import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI

from app.core.config import get_settings

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

settings = get_settings()


class PineconeService:
    """Service for Pinecone vector operations and RAG orchestration."""
    
    def __init__(self):
        """Initialize Pinecone service with API key and environment."""
        # Get API key from settings or environment
        api_key = settings.PINECONE_API_KEY or os.getenv('PINECONE_API_KEY')
        
        if not api_key:
            raise ValueError("PINECONE_API_KEY not found in environment variables or settings")
        
        # Initialize Pinecone with new API
        self.pc = Pinecone(api_key=api_key)
        
        # Ensure questions index exists
        self._ensure_index_exists()
        
        # Get questions index
        self.questions_index = self.pc.Index('questions-embeddings')
        
        # Initialize OpenAI client for embeddings
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        logger.info("Pinecone service initialized successfully")
    
    def _ensure_index_exists(self):
        """Ensure the questions-embeddings index exists, create if it doesn't."""
        index_name = 'questions-embeddings'
        
        try:
            # Check if index exists
            existing_indexes = self.pc.list_indexes()
            index_names = [idx.name for idx in existing_indexes]
            
            if index_name not in index_names:
                logger.info(f"Creating Pinecone index: {index_name}")
                
                # Create index with OpenAI embedding dimensions
                self.pc.create_index(
                    name=index_name,
                    dimension=1536,  # OpenAI text-embedding-ada-002 dimension
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud='aws',
                        region='us-east-1'
                    )
                )
                
                logger.info(f"Successfully created Pinecone index: {index_name}")
            else:
                logger.info(f"Pinecone index {index_name} already exists")
                
        except Exception as e:
            logger.error(f"Error ensuring index exists: {str(e)}")
            raise
    
    def get_embedding(self, text: str) -> List[float]:
        """
        Generate embeddings for text using OpenAI's text-embedding-ada-002 model.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of embedding values
        """
        try:
            resp = self.openai_client.embeddings.create(
                input=text, 
                model='text-embedding-ada-002'
            )
            return resp.data[0].embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise
    
    def upsert_question_embedding(self, q_id: int, text: str, metadata: dict) -> None:
        """
        Upsert question embedding to Pinecone index.
        
        Args:
            q_id: Question ID
            text: Question text to embed
            metadata: Additional metadata for the question
        """
        try:
            # Generate embedding
            emb = self.get_embedding(text)
            
            # Upsert to Pinecone
            self.questions_index.upsert([(str(q_id), emb, metadata)])
            
            logger.info(f"Successfully upserted question {q_id} to Pinecone")
            
        except Exception as e:
            logger.error(f"Error upserting question {q_id}: {str(e)}")
            raise
    
    async def sync_question_to_pinecone(self, question_id: int, question_text: str, 
                                      domain: str, question_type: str, 
                                      difficulty: Optional[str] = None) -> None:
        """
        Sync a question to Pinecone with metadata.
        
        Args:
            question_id: Unique question identifier
            question_text: The question text
            domain: Question domain (e.g., 'Software Engineering', 'Product Management')
            question_type: Type of question (e.g., 'behavioral', 'technical', 'resume-driven')
            difficulty: Optional difficulty level
        """
        try:
            metadata = {
                'question_id': question_id,
                'domain': domain,
                'type': question_type,
                'text': question_text
            }
            
            if difficulty:
                metadata['difficulty'] = difficulty
            
            # Use sync method for upsert
            self.upsert_question_embedding(question_id, question_text, metadata)
            
            logger.info(f"Synced question {question_id} to Pinecone with metadata: {metadata}")
            
        except Exception as e:
            logger.error(f"Error syncing question {question_id} to Pinecone: {str(e)}")
            raise
    
    async def search_similar_questions(self, query_text: str, domain: Optional[str] = None,
                                     question_type: Optional[str] = None, 
                                     top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar questions using semantic similarity.
        
        Args:
            query_text: Text to search for
            domain: Optional domain filter
            question_type: Optional question type filter
            top_k: Number of results to return
            
        Returns:
            List of similar questions with metadata and scores
        """
        try:
            # Generate embedding for query
            query_embedding = self.get_embedding(query_text)
            
            # Build filter
            filter_dict = {}
            if domain:
                filter_dict['domain'] = domain
            if question_type:
                filter_dict['type'] = question_type
            
            # Search Pinecone
            results = self.questions_index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict if filter_dict else None
            )
            
            # Format results
            similar_questions = []
            for match in results.matches:
                similar_questions.append({
                    'question_id': match.metadata.get('question_id'),
                    'text': match.metadata.get('text'),
                    'domain': match.metadata.get('domain'),
                    'type': match.metadata.get('type'),
                    'difficulty': match.metadata.get('difficulty'),
                    'similarity_score': match.score
                })
            
            logger.info(f"Found {len(similar_questions)} similar questions for query")
            return similar_questions
            
        except Exception as e:
            logger.error(f"Error searching similar questions: {str(e)}")
            return []
    
    async def get_follow_up_questions(self, answer_text: str, session_context: Dict[str, Any],
                                    exclude_ids: List[int] = None) -> List[Dict[str, Any]]:
        """
        Get follow-up questions based on candidate's answer using RAG.
        
        Args:
            answer_text: Candidate's answer text
            session_context: Session context including domain, difficulty, etc.
            exclude_ids: Question IDs to exclude from results
            
        Returns:
            List of relevant follow-up questions
        """
        try:
            domain = session_context.get('domain')
            difficulty = session_context.get('difficulty')
            
            # Search for similar questions based on answer
            similar_questions = await self.search_similar_questions(
                query_text=answer_text,
                domain=domain,
                question_type='follow-up',
                top_k=10
            )
            
            # Filter out already asked questions
            if exclude_ids:
                similar_questions = [
                    q for q in similar_questions 
                    if q['question_id'] not in exclude_ids
                ]
            
            # Return top follow-ups
            return similar_questions[:3]
            
        except Exception as e:
            logger.error(f"Error getting follow-up questions: {str(e)}")
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of Pinecone service.
        
        Returns:
            Health status dictionary
        """
        try:
            # Try to describe index stats
            stats = self.questions_index.describe_index_stats()
            
            return {
                'healthy': True,
                'index_name': 'questions-embeddings',
                'total_vectors': stats.total_vector_count,
                'namespaces': len(stats.namespaces) if stats.namespaces else 0,
                'message': 'Pinecone service is healthy'
            }
            
        except Exception as e:
            logger.error(f"Pinecone health check failed: {str(e)}")
            return {
                'healthy': False,
                'error': str(e),
                'message': 'Pinecone service is unhealthy'
            }


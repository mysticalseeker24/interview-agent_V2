"""Pinecone vector database service with performance optimizations for TalentSync Interview Service."""
import asyncio
import logging
import time
from typing import List, Dict, Any, Optional
from functools import lru_cache

import httpx
from pinecone import Pinecone, ServerlessSpec
from openai import AsyncOpenAI

from app.core.settings import settings
from app.core.dataset_mapping import get_domain_for_dataset, is_valid_domain

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Circuit breaker pattern for external service calls."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def can_execute(self) -> bool:
        """Check if the circuit breaker allows execution."""
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def on_success(self):
        """Handle successful execution."""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def on_failure(self):
        """Handle failed execution."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")


class PineconeService:
    """High-performance Pinecone service with caching and circuit breakers."""
    
    def __init__(self):
        """Initialize Pinecone service with performance optimizations."""
        self.api_key = settings.PINECONE_API_KEY
        self.environment = settings.PINECONE_ENV
        self.index_name = settings.PINECONE_INDEX_NAME
        
        # Initialize Pinecone client
        self.pc = Pinecone(api_key=self.api_key)
        
        # Initialize OpenAI client for embeddings
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Circuit breaker for Pinecone operations
        self.pinecone_circuit_breaker = CircuitBreaker(
            failure_threshold=settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
            recovery_timeout=settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT
        )
        
        # Circuit breaker for OpenAI operations
        self.openai_circuit_breaker = CircuitBreaker(
            failure_threshold=settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
            recovery_timeout=settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT
        )
        
        # Cache for embeddings
        self._embedding_cache = {}
        self._cache_ttl = settings.CACHE_TTL
        
        # Ensure index exists
        self._ensure_index_exists()
        
        # Get index
        self.index = self.pc.Index(self.index_name)
        
        logger.info("Pinecone service initialized with performance optimizations")
    
    def _ensure_index_exists(self):
        """Ensure the questions-embeddings index exists, create if it doesn't."""
        try:
            existing_indexes = self.pc.list_indexes()
            index_names = [idx.name for idx in existing_indexes]
            
            if self.index_name not in index_names:
                logger.info(f"Creating Pinecone index: {self.index_name}")
                
                self.pc.create_index(
                    name=self.index_name,
                    dimension=1536,  # OpenAI text-embedding-ada-002 dimension
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud='aws',
                        region='us-east-1'
                    )
                )
                
                logger.info(f"Successfully created Pinecone index: {self.index_name}")
            else:
                logger.info(f"Pinecone index {self.index_name} already exists")
                
        except Exception as e:
            logger.error(f"Error ensuring index exists: {str(e)}")
            raise
    
    async def get_embedding(self, text: str) -> List[float]:
        """
        Generate embeddings for text using OpenAI with caching.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of embedding values
        """
        # Check cache first
        cache_key = hash(text)
        if cache_key in self._embedding_cache:
            cache_entry = self._embedding_cache[cache_key]
            if time.time() - cache_entry['timestamp'] < self._cache_ttl:
                logger.debug(f"Cache hit for embedding: {text[:50]}...")
                return cache_entry['embedding']
        
        # Check circuit breaker
        if not self.openai_circuit_breaker.can_execute():
            raise Exception("OpenAI circuit breaker is open")
        
        try:
            start_time = time.time()
            
            response = await asyncio.wait_for(
                self.openai_client.embeddings.create(
                    input=text,
                    model=settings.OPENAI_EMBEDDING_MODEL
                ),
                timeout=5.0  # Increase timeout to 5 seconds for embeddings
            )
            
            embedding = response.data[0].embedding
            processing_time = (time.time() - start_time) * 1000
            
            # Cache the result
            self._embedding_cache[cache_key] = {
                'embedding': embedding,
                'timestamp': time.time()
            }
            
            # Clean cache if too large
            if len(self._embedding_cache) > 1000:
                self._clean_cache()
            
            logger.debug(f"Generated embedding in {processing_time:.2f}ms")
            self.openai_circuit_breaker.on_success()
            
            return embedding
            
        except asyncio.TimeoutError:
            logger.error("OpenAI embedding request timeout")
            self.openai_circuit_breaker.on_failure()
            raise Exception("Embedding generation timeout")
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            self.openai_circuit_breaker.on_failure()
            raise
    
    def _clean_cache(self):
        """Clean old cache entries."""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._embedding_cache.items()
            if current_time - entry['timestamp'] > self._cache_ttl
        ]
        for key in expired_keys:
            del self._embedding_cache[key]
        logger.debug(f"Cleaned {len(expired_keys)} expired cache entries")
    
    async def upsert_questions(self, questions: List[Dict[str, Any]]) -> bool:
        """
        Upsert questions to Pinecone with batching for performance.
        
        Args:
            questions: List of question dictionaries with embeddings
            
        Returns:
            True if successful, False otherwise
        """
        if not self.pinecone_circuit_breaker.can_execute():
            raise Exception("Pinecone circuit breaker is open")
        
        try:
            start_time = time.time()
            
            # Prepare vectors for upsert
            vectors = []
            for question in questions:
                vector_data = {
                    "id": str(question["id"]),
                    "values": question["embedding"],
                    "metadata": {
                        "text": question["text"],
                        "domain": question.get("domain", "general"),
                        "difficulty": question.get("difficulty", "medium"),
                        "type": question.get("type", "general"),
                        "question_id": str(question["id"])
                    }
                }
                vectors.append(vector_data)
            
            # Upsert in batches for better performance
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                # Pinecone upsert is synchronous, no need to await
                self.index.upsert(vectors=batch)
            
            processing_time = (time.time() - start_time) * 1000
            logger.info(f"Upserted {len(questions)} questions in {processing_time:.2f}ms")
            
            self.pinecone_circuit_breaker.on_success()
            return True
            
        except asyncio.TimeoutError:
            logger.error("Pinecone upsert timeout")
            self.pinecone_circuit_breaker.on_failure()
            return False
        except Exception as e:
            logger.error(f"Error upserting questions: {str(e)}")
            self.pinecone_circuit_breaker.on_failure()
            return False
    
    async def query(
        self, 
        vector: List[float], 
        top_k: int = 5, 
        filter: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Query Pinecone for similar vectors with performance optimizations.
        
        Args:
            vector: Query vector
            top_k: Number of results to return
            filter: Optional filter dictionary
            
        Returns:
            List of similar questions with metadata and scores
        """
        if not self.pinecone_circuit_breaker.can_execute():
            raise Exception("Pinecone circuit breaker is open")
        
        try:
            start_time = time.time()
            
            # Build filter with performance optimizations
            query_filter = {}
            if filter:
                query_filter.update(filter)
            
            # Query Pinecone (Pinecone SDK v2+ returns QueryResponse directly)
            results = await asyncio.wait_for(
                asyncio.to_thread(
                    self.index.query,
                    vector=vector,
                    top_k=top_k,
                    include_metadata=True,
                    filter=query_filter if query_filter else None
                ),
                timeout=settings.REQUEST_TIMEOUT
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
            
            processing_time = (time.time() - start_time) * 1000
            logger.debug(f"Pinecone query completed in {processing_time:.2f}ms")
            
            self.pinecone_circuit_breaker.on_success()
            return similar_questions
            
        except asyncio.TimeoutError:
            logger.error("Pinecone query timeout")
            self.pinecone_circuit_breaker.on_failure()
            return []
        except Exception as e:
            logger.error(f"Error querying Pinecone: {str(e)}")
            self.pinecone_circuit_breaker.on_failure()
            return []
    
    async def search_similar_questions(
        self, 
        query_text: str, 
        domain: Optional[str] = None,
        question_type: Optional[str] = None, 
        top_k: int = 5,
        exclude_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar questions using semantic similarity.
        
        Args:
            query_text: Text to search for
            domain: Optional domain filter
            question_type: Optional question type filter
            top_k: Number of results to return
            exclude_ids: List of question IDs to exclude
            
        Returns:
            List of similar questions with metadata and scores
        """
        try:
            # Validate domain if provided
            if domain and not is_valid_domain(domain):
                logger.warning(f"Invalid domain provided: {domain}")
                domain = None
            
            # Generate embedding for query
            query_embedding = await self.get_embedding(query_text)
            
            # Build filter
            filter_dict = {}
            if domain:
                filter_dict['domain'] = domain
            if question_type:
                filter_dict['type'] = question_type
            
            # Query Pinecone
            results = await self.query(query_embedding, top_k * 2, filter_dict)
            
            # Filter out excluded IDs
            if exclude_ids:
                results = [r for r in results if r['question_id'] not in exclude_ids]
            
            # Return top_k results
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Error in semantic search: {str(e)}")
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Pinecone service health with lightweight retry to avoid transient failures."""
        attempts = 3
        last_error: Optional[str] = None
        start_time_overall = time.time()
        for attempt in range(1, attempts + 1):
            try:
                start_time = time.time()
                test_vector = [0.0] * 1536  # Zero vector for testing
                await asyncio.wait_for(
                    asyncio.to_thread(self.index.query, vector=test_vector, top_k=1),
                    timeout=settings.HEALTH_CHECK_TIMEOUT
                )
                response_time = (time.time() - start_time) * 1000
                self.pinecone_circuit_breaker.on_success()
                return {
                    "status": "healthy",
                    "response_time_ms": response_time,
                    "index_name": self.index_name,
                    "circuit_breaker_state": self.pinecone_circuit_breaker.state
                }
            except asyncio.TimeoutError:
                last_error = f"timeout after {settings.HEALTH_CHECK_TIMEOUT}s"
                logger.warning(f"Pinecone health check attempt {attempt}/{attempts} timed out")
            except Exception as e:
                last_error = str(e) if str(e) else "Unknown error"
                logger.warning(f"Pinecone health check attempt {attempt}/{attempts} failed: {last_error}")
            # brief backoff before retrying
            await asyncio.sleep(0.3)
        # All attempts failed
        total_time_ms = (time.time() - start_time_overall) * 1000
        return {
            "status": "unhealthy",
            "error": last_error or "Unknown error during health check",
            "response_time_ms": total_time_ms,
            "circuit_breaker_state": self.pinecone_circuit_breaker.state
        }
    
    async def get_index_stats(self) -> Dict[str, Any]:
        """Get Pinecone index statistics."""
        try:
            stats = self.index.describe_index_stats()
            return {
                "total_vector_count": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness,
                "namespaces": stats.namespaces
            }
        except Exception as e:
            logger.error(f"Error getting index stats: {str(e)}")
            return {"error": str(e)} 
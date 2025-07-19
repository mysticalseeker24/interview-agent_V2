"""Session management service with Redis-backed storage for TalentSync Interview Service."""
import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

import redis.asyncio as redis
from pydantic import ValidationError

from app.core.settings import settings
from app.schemas.interview import Session, SessionCreate, SessionUpdate

logger = logging.getLogger(__name__)


class SessionService:
    """High-performance session management with Redis storage."""
    
    def __init__(self):
        """Initialize session service with Redis connection."""
        self.redis_url = settings.REDIS_URL
        self.session_ttl = settings.SESSION_TTL
        self.redis_client: Optional[redis.Redis] = None
        self._connection_pool = None
        
        # Performance tracking
        self._operation_times = []
        self._cache_hits = 0
        self._cache_misses = 0
        
        logger.info("Session service initialized")
    
    async def connect(self):
        """Establish Redis connection with connection pooling."""
        try:
            if not self.redis_client:
                self.redis_client = redis.from_url(
                    self.redis_url,
                    max_connections=settings.REDIS_MAX_CONNECTIONS,
                    socket_connect_timeout=settings.REDIS_CONNECT_TIMEOUT,
                    socket_timeout=settings.REQUEST_TIMEOUT,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
                
                # Test connection
                await self.redis_client.ping()
                logger.info("Redis connection established successfully")
                
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise
    
    async def disconnect(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
            logger.info("Redis connection closed")
    
    def _get_session_key(self, session_id: UUID) -> str:
        """Generate Redis key for session."""
        return f"session:{session_id}"
    
    def _get_user_sessions_key(self, user_id: UUID) -> str:
        """Generate Redis key for user's sessions list."""
        return f"user_sessions:{user_id}"
    
    async def create_session(self, session_data: SessionCreate, user_id: UUID) -> Session:
        """
        Create a new interview session with performance optimizations.
        
        Args:
            session_data: Session creation data
            user_id: User ID creating the session
            
        Returns:
            Created session object
        """
        start_time = time.time()
        
        try:
            session_id = uuid4()
            now = datetime.utcnow()
            
            # Create session object
            session = Session(
                id=session_id,
                user_id=user_id,
                module_id=session_data.module_id,
                mode=session_data.mode,
                status="pending",
                current_question_index=0,
                estimated_duration_minutes=30,  # Default, can be updated
                created_at=now,
                started_at=None,
                completed_at=None,
                queue_length=0,
                asked_questions=[]
            )
            
            # Store in Redis with TTL
            session_key = self._get_session_key(session_id)
            user_sessions_key = self._get_user_sessions_key(user_id)
            
            # Use pipeline for atomic operations
            async with self.redis_client.pipeline() as pipe:
                # Store session data
                await pipe.setex(
                    session_key,
                    self.session_ttl,
                    session.model_dump_json()
                )
                
                # Add to user's session list
                await pipe.sadd(user_sessions_key, str(session_id))
                await pipe.expire(user_sessions_key, self.session_ttl)
                
                # Execute pipeline
                await pipe.execute()
            
            # Track performance
            operation_time = (time.time() - start_time) * 1000
            self._operation_times.append(operation_time)
            
            logger.info(f"Created session {session_id} for user {user_id} in {operation_time:.2f}ms")
            return session
            
        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            raise
    
    async def get_session(self, session_id: UUID) -> Optional[Session]:
        """
        Retrieve session by ID with caching.
        
        Args:
            session_id: Session ID to retrieve
            
        Returns:
            Session object if found, None otherwise
        """
        start_time = time.time()
        
        try:
            session_key = self._get_session_key(session_id)
            
            # Get session data from Redis
            session_data = await asyncio.wait_for(
                self.redis_client.get(session_key),
                timeout=settings.REQUEST_TIMEOUT
            )
            
            if not session_data:
                self._cache_misses += 1
                return None
            
            self._cache_hits += 1
            
            # Parse session data
            session_dict = json.loads(session_data)
            session = Session(**session_dict)
            
            # Track performance
            operation_time = (time.time() - start_time) * 1000
            self._operation_times.append(operation_time)
            
            return session
            
        except asyncio.TimeoutError:
            logger.error("Session retrieval timeout")
            return None
        except Exception as e:
            logger.error(f"Error retrieving session {session_id}: {str(e)}")
            return None
    
    async def update_session(self, session_id: UUID, updates: SessionUpdate) -> Optional[Session]:
        """
        Update session with atomic operations.
        
        Args:
            session_id: Session ID to update
            updates: Session update data
            
        Returns:
            Updated session object if successful, None otherwise
        """
        start_time = time.time()
        
        try:
            # Get current session
            session = await self.get_session(session_id)
            if not session:
                return None
            
            # Apply updates
            update_data = updates.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(session, field, value)
            
            # Update timestamps
            if updates.status == "active" and not session.started_at:
                session.started_at = datetime.utcnow()
            elif updates.status == "completed" and not session.completed_at:
                session.completed_at = datetime.utcnow()
            
            # Store updated session
            session_key = self._get_session_key(session_id)
            await asyncio.wait_for(
                self.redis_client.setex(
                    session_key,
                    self.session_ttl,
                    session.model_dump_json()
                ),
                timeout=settings.REQUEST_TIMEOUT
            )
            
            # Track performance
            operation_time = (time.time() - start_time) * 1000
            self._operation_times.append(operation_time)
            
            logger.info(f"Updated session {session_id} in {operation_time:.2f}ms")
            return session
            
        except asyncio.TimeoutError:
            logger.error("Session update timeout")
            return None
        except Exception as e:
            logger.error(f"Error updating session {session_id}: {str(e)}")
            return None
    
    async def get_user_sessions(self, user_id: UUID, limit: int = 50) -> List[Session]:
        """
        Get user's sessions with pagination.
        
        Args:
            user_id: User ID
            limit: Maximum number of sessions to return
            
        Returns:
            List of user's sessions
        """
        start_time = time.time()
        
        try:
            user_sessions_key = self._get_user_sessions_key(user_id)
            
            # Get user's session IDs
            session_ids = await asyncio.wait_for(
                self.redis_client.smembers(user_sessions_key),
                timeout=settings.REQUEST_TIMEOUT
            )
            
            # Get session details (limit to recent sessions)
            sessions = []
            session_ids_list = list(session_ids)[-limit:]  # Get most recent
            
            if session_ids_list:
                # Use pipeline for batch retrieval
                async with self.redis_client.pipeline() as pipe:
                    for session_id in session_ids_list:
                        session_key = self._get_session_key(UUID(session_id))
                        pipe.get(session_key)
                    
                    session_data_list = await pipe.execute()
                    
                    for session_data in session_data_list:
                        if session_data:
                            try:
                                session_dict = json.loads(session_data)
                                session = Session(**session_dict)
                                sessions.append(session)
                            except (json.JSONDecodeError, ValidationError) as e:
                                logger.warning(f"Invalid session data: {str(e)}")
                                continue
            
            # Sort by creation date (newest first)
            sessions.sort(key=lambda x: x.created_at, reverse=True)
            
            # Track performance
            operation_time = (time.time() - start_time) * 1000
            self._operation_times.append(operation_time)
            
            return sessions
            
        except asyncio.TimeoutError:
            logger.error("User sessions retrieval timeout")
            return []
        except Exception as e:
            logger.error(f"Error retrieving sessions for user {user_id}: {str(e)}")
            return []
    
    async def add_question_to_session(self, session_id: UUID, question_id: str) -> bool:
        """
        Add a question to session's asked questions list.
        
        Args:
            session_id: Session ID
            question_id: Question ID to add
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session = await self.get_session(session_id)
            if not session:
                return False
            
            # Add question to asked list if not already present
            if question_id not in session.asked_questions:
                session.asked_questions.append(question_id)
                
                # Update session
                await self.update_session(session_id, SessionUpdate())
                return True
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding question to session {session_id}: {str(e)}")
            return False
    
    async def get_session_queue(self, session_id: UUID) -> List[str]:
        """
        Get session's question queue.
        
        Args:
            session_id: Session ID
            
        Returns:
            List of question IDs in queue
        """
        try:
            session = await self.get_session(session_id)
            if not session:
                return []
            
            # For now, return empty queue - this will be populated by question service
            return []
            
        except Exception as e:
            logger.error(f"Error getting session queue {session_id}: {str(e)}")
            return []
    
    async def update_session_queue(self, session_id: UUID, question_ids: List[str]) -> bool:
        """
        Update session's question queue.
        
        Args:
            session_id: Session ID
            question_ids: List of question IDs for queue
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session = await self.get_session(session_id)
            if not session:
                return False
            
            # Update queue length
            session.queue_length = len(question_ids)
            
            # Store queue in Redis
            queue_key = f"session_queue:{session_id}"
            await asyncio.wait_for(
                self.redis_client.setex(
                    queue_key,
                    self.session_ttl,
                    json.dumps(question_ids)
                ),
                timeout=settings.REQUEST_TIMEOUT
            )
            
            # Update session
            await self.update_session(session_id, SessionUpdate())
            return True
            
        except Exception as e:
            logger.error(f"Error updating session queue {session_id}: {str(e)}")
            return False
    
    async def delete_session(self, session_id: UUID) -> bool:
        """
        Delete session and clean up related data.
        
        Args:
            session_id: Session ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session = await self.get_session(session_id)
            if not session:
                return False
            
            # Delete session data and related keys
            session_key = self._get_session_key(session_id)
            user_sessions_key = self._get_user_sessions_key(session.user_id)
            queue_key = f"session_queue:{session_id}"
            
            async with self.redis_client.pipeline() as pipe:
                await pipe.delete(session_key)
                await pipe.srem(user_sessions_key, str(session_id))
                await pipe.delete(queue_key)
                await pipe.execute()
            
            logger.info(f"Deleted session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {str(e)}")
            return False
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions (Redis TTL handles most cleanup).
        
        Returns:
            Number of sessions cleaned up
        """
        try:
            # Redis TTL handles most cleanup automatically
            # This method can be used for additional cleanup logic if needed
            return 0
            
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {str(e)}")
            return 0
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the service."""
        if not self._operation_times:
            return {
                "avg_operation_time_ms": 0,
                "p95_operation_time_ms": 0,
                "cache_hit_rate": 0,
                "total_operations": 0
            }
        
        sorted_times = sorted(self._operation_times)
        total_operations = len(self._operation_times)
        total_cache_requests = self._cache_hits + self._cache_misses
        
        return {
            "avg_operation_time_ms": sum(self._operation_times) / total_operations,
            "p95_operation_time_ms": sorted_times[int(0.95 * total_operations)],
            "p99_operation_time_ms": sorted_times[int(0.99 * total_operations)],
            "cache_hit_rate": self._cache_hits / total_cache_requests if total_cache_requests > 0 else 0,
            "total_operations": total_operations,
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check service health."""
        try:
            start_time = time.time()
            
            # Test Redis connection
            await asyncio.wait_for(
                self.redis_client.ping(),
                timeout=settings.HEALTH_CHECK_TIMEOUT
            )
            
            response_time = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "response_time_ms": response_time,
                "redis_connected": True,
                "performance_metrics": self.get_performance_metrics()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "redis_connected": False,
                "performance_metrics": self.get_performance_metrics()
            } 
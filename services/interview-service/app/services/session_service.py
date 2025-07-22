"""Session management service with Supabase-backed storage for TalentSync Interview Service."""
import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from pydantic import ValidationError

from app.core.settings import settings
from app.schemas.interview import Session, SessionCreate, SessionUpdate
from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


class SessionService:
    """High-performance session management with Supabase storage."""
    
    def __init__(self):
        """Initialize session service with Supabase connection."""
        self.supabase_service = SupabaseService()
        self.session_ttl = settings.SESSION_TTL
        
        # Performance tracking
        self._operation_times = []
        self._cache_hits = 0
        self._cache_misses = 0
        
        logger.info("Session service initialized with Supabase")
    
    async def connect(self):
        """Establish Supabase connection."""
        try:
            # Test connection by performing a health check
            health = await self.supabase_service.health_check()
            if health["status"] == "healthy":
                logger.info("Supabase connection established successfully")
            else:
                logger.warning(f"Supabase connection degraded: {health.get('message', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {str(e)}")
            raise
    
    async def disconnect(self):
        """Close Supabase connection."""
        # Supabase client handles connection management automatically
        logger.info("Supabase connection closed")
    
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
            session = await self.supabase_service.create_session(session_data, user_id)
            
            # Track performance
            operation_time = (time.time() - start_time) * 1000
            self._operation_times.append(operation_time)
            
            logger.info(f"Created session {session.id} for user {user_id} in {operation_time:.2f}ms")
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
            session = await self.supabase_service.get_session(session_id)
            
            if not session:
                self._cache_misses += 1
                return None
            
            self._cache_hits += 1
            
            # Track performance
            operation_time = (time.time() - start_time) * 1000
            self._operation_times.append(operation_time)
            
            return session
            
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
            session = await self.supabase_service.update_session(session_id, updates)
            
            if session:
                # Track performance
                operation_time = (time.time() - start_time) * 1000
                self._operation_times.append(operation_time)
                
                logger.info(f"Updated session {session_id} in {operation_time:.2f}ms")
            
            return session
            
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
            sessions = await self.supabase_service.get_user_sessions(user_id, limit)
            
            # Track performance
            operation_time = (time.time() - start_time) * 1000
            self._operation_times.append(operation_time)
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error getting user sessions for {user_id}: {str(e)}")
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
            return await self.supabase_service.add_question_to_session(session_id, question_id)
            
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
            return await self.supabase_service.get_session_queue(session_id)
            
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
            return await self.supabase_service.update_session_queue(session_id, question_ids)
            
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
            return await self.supabase_service.delete_session(session_id)
            
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {str(e)}")
            return False
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions (older than 24 hours).
        
        Returns:
            Number of sessions cleaned up
        """
        try:
            return await self.supabase_service.cleanup_expired_sessions()
            
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {str(e)}")
            return 0
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        # Get metrics from Supabase service
        supabase_metrics = self.supabase_service.get_performance_metrics()
        
        # Combine with local metrics
        if not self._operation_times:
            return {
                "avg_operation_time_ms": 0,
                "p95_operation_time_ms": 0,
                "p99_operation_time_ms": 0,
                "total_operations": 0,
                "cache_hit_rate": 0,
                "cache_hits": 0,
                "cache_misses": 0,
                "supabase_metrics": supabase_metrics
            }
        
        sorted_times = sorted(self._operation_times)
        total_operations = len(sorted_times)
        
        return {
            "avg_operation_time_ms": sum(sorted_times) / total_operations,
            "p95_operation_time_ms": sorted_times[int(total_operations * 0.95)],
            "p99_operation_time_ms": sorted_times[int(total_operations * 0.99)],
            "total_operations": total_operations,
            "cache_hit_rate": self._cache_hits / (self._cache_hits + self._cache_misses) if (self._cache_hits + self._cache_misses) > 0 else 0,
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "supabase_metrics": supabase_metrics
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check service health."""
        try:
            start_time = time.time()
            
            # Check Supabase service health
            supabase_health = await self.supabase_service.health_check()
            
            response_time = (time.time() - start_time) * 1000
            
            return {
                "status": supabase_health["status"],
                "response_time_ms": response_time,
                "supabase_connected": supabase_health.get("supabase_connected", False),
                "performance_metrics": self.get_performance_metrics(),
                "supabase_health": supabase_health
            }
            
        except Exception as e:
            return {
                "status": "degraded",
                "error": str(e),
                "supabase_connected": False,
                "performance_metrics": self.get_performance_metrics(),
                "message": "Session service health check failed"
            } 
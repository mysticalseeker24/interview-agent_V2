"""Supabase service for TalentSync Interview Service session management."""
import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

import httpx
from supabase import Client, create_client
from supabase.lib.client_options import ClientOptions

from app.core.settings import settings
from app.schemas.interview import Session, SessionCreate, SessionUpdate

logger = logging.getLogger(__name__)


class SupabaseService:
    """High-performance Supabase service for session management."""
    
    def __init__(self):
        """Initialize Supabase service with performance optimizations."""
        # Configure client options for high performance
        client_options = ClientOptions(
            schema="public",
            headers={
                "X-Client-Info": f"talentsync-interview-service/{settings.APP_VERSION}",
            },
            realtime={
                "params": {
                    "apikey": settings.SUPABASE_ANON_KEY,
                }
            },
        )
        
        # Initialize Supabase client with service role for admin operations
        self.client: Client = create_client(
            str(settings.SUPABASE_URL),
            settings.SUPABASE_SERVICE_ROLE_KEY,
            options=client_options,
        )
        
        # Performance tracking
        self._operation_times = []
        self._cache_hits = 0
        self._cache_misses = 0
        
        logger.info("Supabase service initialized successfully")
    
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
            
            # Prepare data for Supabase with proper datetime serialization
            session_dict = session.model_dump()
            session_dict['id'] = str(session_id)
            session_dict['user_id'] = str(user_id)
            session_dict['asked_questions'] = json.dumps(session.asked_questions)
            session_dict['parsed_resume_data'] = json.dumps(session_data.parsed_resume_data) if session_data.parsed_resume_data else None
            
            # Convert datetime objects to ISO format strings for JSON serialization
            for field in ['created_at', 'started_at', 'completed_at', 'updated_at']:
                if session_dict.get(field):
                    if isinstance(session_dict[field], datetime):
                        session_dict[field] = session_dict[field].isoformat()
                    elif session_dict[field] is None:
                        session_dict[field] = None
            
            # Store in Supabase
            response = self.client.table("interview_sessions").insert(session_dict).execute()
            
            if not response.data:
                raise Exception("Failed to create session in Supabase")
            
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
            # Get session data from Supabase
            response = self.client.table("interview_sessions").select("*").eq("id", str(session_id)).single().execute()
            
            if not response.data:
                self._cache_misses += 1
                return None
            
            self._cache_hits += 1
            
            # Parse session data
            session_dict = response.data
            session_dict['id'] = UUID(session_dict['id'])
            session_dict['user_id'] = UUID(session_dict['user_id'])
            session_dict['asked_questions'] = json.loads(session_dict['asked_questions']) if session_dict['asked_questions'] else []
            
            # Convert timestamps
            for field in ['created_at', 'started_at', 'completed_at', 'updated_at']:
                if session_dict.get(field):
                    session_dict[field] = datetime.fromisoformat(session_dict[field].replace('Z', '+00:00'))
            
            session = Session(**session_dict)
            
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
            
            # Prepare data for Supabase update
            update_dict = {}
            for field, value in update_data.items():
                if field == 'asked_questions':
                    update_dict[field] = json.dumps(value)
                else:
                    update_dict[field] = value
            
            # Update timestamps
            if session.started_at:
                update_dict['started_at'] = session.started_at.isoformat()
            if session.completed_at:
                update_dict['completed_at'] = session.completed_at.isoformat()
            
            # Update in Supabase
            response = self.client.table("interview_sessions").update(update_dict).eq("id", str(session_id)).execute()
            
            if not response.data:
                raise Exception("Failed to update session in Supabase")
            
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
            # Get user's sessions from Supabase
            response = self.client.table("interview_sessions").select("*").eq("user_id", str(user_id)).order("created_at", desc=True).limit(limit).execute()
            
            sessions = []
            for session_dict in response.data:
                try:
                    # Parse session data
                    session_dict['id'] = UUID(session_dict['id'])
                    session_dict['user_id'] = UUID(session_dict['user_id'])
                    session_dict['asked_questions'] = json.loads(session_dict['asked_questions']) if session_dict['asked_questions'] else []
                    
                    # Convert timestamps
                    for field in ['created_at', 'started_at', 'completed_at', 'updated_at']:
                        if session_dict.get(field):
                            session_dict[field] = datetime.fromisoformat(session_dict[field].replace('Z', '+00:00'))
                    
                    session = Session(**session_dict)
                    sessions.append(session)
                except Exception as e:
                    logger.warning(f"Invalid session data: {str(e)}")
                    continue
            
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
            session = await self.get_session(session_id)
            if not session:
                return False
            
            # Add question to asked questions
            if question_id not in session.asked_questions:
                session.asked_questions.append(question_id)
                
                # Update in Supabase
                update_dict = {
                    'asked_questions': json.dumps(session.asked_questions)
                }
                
                response = self.client.table("interview_sessions").update(update_dict).eq("id", str(session_id)).execute()
                
                if response.data:
                    logger.info(f"Added question {question_id} to session {session_id}")
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
            # Get session queue from Supabase
            response = self.client.table("session_queues").select("question_id").eq("session_id", str(session_id)).order("sequence_index").execute()
            
            question_ids = [item['question_id'] for item in response.data]
            return question_ids
            
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
            # Delete existing queue
            self.client.table("session_queues").delete().eq("session_id", str(session_id)).execute()
            
            # Insert new queue items
            queue_items = []
            for i, question_id in enumerate(question_ids):
                queue_items.append({
                    'session_id': str(session_id),
                    'question_id': question_id,
                    'sequence_index': i
                })
            
            if queue_items:
                response = self.client.table("session_queues").insert(queue_items).execute()
                if not response.data:
                    raise Exception("Failed to insert queue items")
            
            # Update session queue length
            await self.update_session(session_id, SessionUpdate(queue_length=len(question_ids)))
            
            logger.info(f"Updated session queue for {session_id} with {len(question_ids)} questions")
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
            # Delete session (cascade will handle related data)
            response = self.client.table("interview_sessions").delete().eq("id", str(session_id)).execute()
            
            if response.data:
                logger.info(f"Deleted session {session_id}")
                return True
            
            return False
            
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
            # Call the cleanup function in Supabase
            response = self.client.rpc('cleanup_expired_sessions').execute()
            
            deleted_count = response.data if response.data else 0
            logger.info(f"Cleaned up {deleted_count} expired sessions")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {str(e)}")
            return 0
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        if not self._operation_times:
            return {
                "avg_operation_time_ms": 0,
                "p95_operation_time_ms": 0,
                "p99_operation_time_ms": 0,
                "total_operations": 0,
                "cache_hit_rate": 0,
                "cache_hits": 0,
                "cache_misses": 0
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
            "cache_misses": self._cache_misses
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check service health."""
        try:
            start_time = time.time()
            
            # Test Supabase connection by querying a simple table
            response = self.client.table("interview_sessions").select("id").limit(1).execute()
            
            response_time = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "response_time_ms": response_time,
                "supabase_connected": True,
                "performance_metrics": self.get_performance_metrics()
            }
            
        except Exception as e:
            return {
                "status": "degraded",
                "error": str(e),
                "supabase_connected": False,
                "performance_metrics": self.get_performance_metrics(),
                "message": "Supabase connection failed"
            } 
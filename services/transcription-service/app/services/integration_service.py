"""
Integration service for triggering webhooks and events to other services.

This service provides hooks for:
1. Follow-Up service integration - trigger after chunk transcription
2. Feedback service integration - trigger after session completion
3. Analytics service integration - trigger for metrics collection
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
import httpx
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)


class IntegrationService:
    """Service for integrating with other TalentSync services."""
    
    def __init__(self):
        self.interview_service_url = getattr(settings, 'interview_service_url', 'http://localhost:8002')
        self.timeout = 30.0
        self.max_retries = 3
        self.retry_delay = 1.0
    
    async def _make_request(
        self, 
        method: str, 
        url: str, 
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Make HTTP request with retries."""
        
        if headers is None:
            headers = {"Content-Type": "application/json"}
        
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    if method.upper() == "GET":
                        response = await client.get(url, headers=headers)
                    elif method.upper() == "POST":
                        response = await client.post(url, json=data, headers=headers)
                    elif method.upper() == "PUT":
                        response = await client.put(url, json=data, headers=headers)
                    else:
                        raise ValueError(f"Unsupported HTTP method: {method}")
                    
                    if response.status_code in [200, 201, 202]:
                        return response.json() if response.content else {}
                    else:
                        logger.warning(f"Request failed with status {response.status_code}: {response.text}")
                        return None
                        
            except httpx.TimeoutException:
                logger.warning(f"Request timeout on attempt {attempt + 1}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    continue
                else:
                    logger.error(f"Request failed after {self.max_retries} attempts due to timeout")
                    return None
            except Exception as e:
                logger.warning(f"Request failed on attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    continue
                else:
                    logger.error(f"Request failed after {self.max_retries} attempts: {e}")
                    return None
        
        return None
    
    async def trigger_followup_generation(
        self, 
        session_id: str, 
        transcript_text: str, 
        question_id: Optional[str] = None,
        confidence_score: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Trigger follow-up question generation in the Interview Service.
        
        Args:
            session_id: Interview session ID
            transcript_text: Transcribed text from the candidate
            question_id: Optional question ID for context
            confidence_score: Optional confidence score from transcription
            
        Returns:
            Follow-up question data or None if failed
        """
        try:
            url = f"{self.interview_service_url}/api/v1/followup/generate"
            
            # Convert session_id to integer if needed
            try:
                session_id_int = int(session_id)
            except ValueError:
                logger.error(f"Invalid session_id format: {session_id}")
                return None
            
            payload = {
                "session_id": session_id_int,
                "answer_text": transcript_text,
                "use_llm": True,  # Use LLM for better follow-up generation
                "max_candidates": 5
            }
            
            logger.info(f"Triggering follow-up generation for session {session_id}")
            
            result = await self._make_request("POST", url, payload)
            
            if result:
                logger.info(f"Follow-up generation triggered successfully for session {session_id}")
                return result
            else:
                logger.error(f"Failed to trigger follow-up generation for session {session_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error triggering follow-up generation: {e}")
            return None
    
    async def trigger_feedback_generation(
        self, 
        session_id: str, 
        regenerate: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Trigger feedback generation in the Interview Service.
        
        Args:
            session_id: Interview session ID
            regenerate: Whether to regenerate existing feedback
            
        Returns:
            Feedback generation task info or None if failed
        """
        try:
            url = f"{self.interview_service_url}/api/v1/feedback/generate"
            
            # Convert session_id to integer if needed
            try:
                session_id_int = int(session_id)
            except ValueError:
                logger.error(f"Invalid session_id format: {session_id}")
                return None
            
            payload = {
                "session_id": session_id_int,
                "regenerate": regenerate
            }
            
            logger.info(f"Triggering feedback generation for session {session_id}")
            
            result = await self._make_request("POST", url, payload)
            
            if result:
                logger.info(f"Feedback generation triggered successfully for session {session_id}. Task ID: {result.get('task_id')}")
                return result
            else:
                logger.error(f"Failed to trigger feedback generation for session {session_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error triggering feedback generation: {e}")
            return None
    
    async def get_feedback_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get feedback generation status from the Interview Service.
        
        Args:
            task_id: Feedback generation task ID
            
        Returns:
            Task status info or None if failed
        """
        try:
            url = f"{self.interview_service_url}/api/v1/feedback/status/{task_id}"
            
            result = await self._make_request("GET", url)
            
            if result:
                logger.info(f"Retrieved feedback status for task {task_id}: {result.get('status')}")
                return result
            else:
                logger.error(f"Failed to get feedback status for task {task_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting feedback status: {e}")
            return None
    
    async def notify_transcription_complete(
        self, 
        session_id: str, 
        transcription_data: Dict[str, Any]
    ) -> bool:
        """
        Notify other services that transcription is complete.
        
        Args:
            session_id: Interview session ID
            transcription_data: Complete transcription data
            
        Returns:
            True if notification was successful, False otherwise
        """
        try:
            # Prepare notification payload
            notification_payload = {
                "event": "transcription_complete",
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "full_transcript": transcription_data.get("full_transcript", ""),
                    "total_chunks": transcription_data.get("total_chunks", 0),
                    "confidence_score": transcription_data.get("confidence_score"),
                    "segments": transcription_data.get("segments", [])
                }
            }
            
            # This could be extended to send to multiple services
            # For now, we'll just log it as a webhook placeholder
            logger.info(f"Transcription complete notification for session {session_id}: {json.dumps(notification_payload, indent=2)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending transcription complete notification: {e}")
            return False
    
    async def notify_chunk_transcribed(
        self, 
        session_id: str, 
        chunk_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Notify that a chunk has been transcribed and potentially trigger follow-up.
        
        Args:
            session_id: Interview session ID
            chunk_data: Transcribed chunk data
            
        Returns:
            Follow-up question data if generated, None otherwise
        """
        try:
            transcript_text = chunk_data.get("transcript_text", "")
            
            # Only trigger follow-up if there's meaningful content
            if len(transcript_text.strip()) > 10:  # Minimum text length threshold
                followup_result = await self.trigger_followup_generation(
                    session_id=session_id,
                    transcript_text=transcript_text,
                    question_id=chunk_data.get("question_id"),
                    confidence_score=chunk_data.get("confidence_score")
                )
                
                if followup_result:
                    logger.info(f"Follow-up question generated for session {session_id}")
                    return followup_result
            
            return None
            
        except Exception as e:
            logger.error(f"Error notifying chunk transcribed: {e}")
            return None
    
    async def notify_session_complete(
        self, 
        session_id: str, 
        session_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Notify that a session is complete and trigger feedback generation.
        
        Args:
            session_id: Interview session ID
            session_data: Complete session data
            
        Returns:
            Feedback generation task info if triggered, None otherwise
        """
        try:
            # Send transcription complete notification
            await self.notify_transcription_complete(session_id, session_data)
            
            # Trigger feedback generation
            feedback_result = await self.trigger_feedback_generation(
                session_id=session_id,
                regenerate=False
            )
            
            if feedback_result:
                logger.info(f"Feedback generation triggered for session {session_id}")
                return feedback_result
            
            return None
            
        except Exception as e:
            logger.error(f"Error notifying session complete: {e}")
            return None
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of integrated services.
        
        Returns:
            Health status of integrated services
        """
        health_status = {
            "integration_service": "healthy",
            "services": {}
        }
        
        # Check Interview Service
        try:
            url = f"{self.interview_service_url}/api/v1/health"
            result = await self._make_request("GET", url)
            
            if result:
                health_status["services"]["interview_service"] = "healthy"
            else:
                health_status["services"]["interview_service"] = "unhealthy"
                
        except Exception as e:
            health_status["services"]["interview_service"] = f"error: {e}"
        
        # Check Follow-Up Service
        try:
            url = f"{self.interview_service_url}/api/v1/followup/health"
            result = await self._make_request("GET", url)
            
            if result:
                health_status["services"]["followup_service"] = "healthy"
            else:
                health_status["services"]["followup_service"] = "unhealthy"
                
        except Exception as e:
            health_status["services"]["followup_service"] = f"error: {e}"
        
        # Check Feedback Service
        try:
            url = f"{self.interview_service_url}/api/v1/feedback/health"
            result = await self._make_request("GET", url)
            
            if result:
                health_status["services"]["feedback_service"] = "healthy"
            else:
                health_status["services"]["feedback_service"] = "unhealthy"
                
        except Exception as e:
            health_status["services"]["feedback_service"] = f"error: {e}"
        
        return health_status

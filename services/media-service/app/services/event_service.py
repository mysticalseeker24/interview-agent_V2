"""
Event emission service for inter-service communication.
"""
import asyncio
import json
import logging
from typing import Dict, Any, Optional

import httpx

from app.core.config import get_settings
from app.schemas.media import ChunkUploadEvent, SessionCompleteEvent

logger = logging.getLogger(__name__)
settings = get_settings()


class EventEmissionService:
    """Service for emitting events to other services."""
    
    def __init__(self):
        self.transcription_service_url = settings.transcription_service_url
        self.interview_service_url = settings.interview_service_url
        self.timeout = 30.0
    
    async def emit_chunk_uploaded_event(
        self,
        session_id: str,
        chunk_id: int,
        sequence_index: int,
        file_path: str,
        file_size_bytes: int,
        overlap_seconds: float,
        question_id: Optional[str] = None,
        total_chunks: Optional[int] = None,
        is_final_chunk: bool = False
    ) -> Dict[str, Any]:
        """
        Emit chunk uploaded event to transcription service.
        
        Args:
            session_id: Session identifier
            chunk_id: Chunk database ID
            sequence_index: Chunk sequence index
            file_path: Path to uploaded file
            file_size_bytes: File size in bytes
            overlap_seconds: Overlap duration
            question_id: Optional question identifier
            total_chunks: Expected total chunks
            is_final_chunk: Whether this is the final chunk
            
        Returns:
            Dict with emission results
        """
        try:
            event = ChunkUploadEvent(
                session_id=session_id,
                chunk_id=chunk_id,
                sequence_index=sequence_index,
                file_path=file_path,
                file_size_bytes=file_size_bytes,
                overlap_seconds=overlap_seconds,
                question_id=question_id,
                total_chunks=total_chunks,
                is_final_chunk=is_final_chunk
            )
            
            # Send to transcription service
            transcription_result = await self._send_to_transcription_service(event)
            
            # Optionally send to interview service for coordination
            interview_result = await self._send_to_interview_service(event)
            
            logger.info(f"Emitted chunk upload event for session {session_id}, chunk {sequence_index}")
            
            return {
                "success": True,
                "transcription_service": transcription_result,
                "interview_service": interview_result,
                "event": event.model_dump()
            }
            
        except Exception as e:
            logger.error(f"Error emitting chunk upload event: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def emit_session_completed_event(
        self,
        session_id: str,
        total_chunks: int,
        total_duration_seconds: float
    ) -> Dict[str, Any]:
        """
        Emit session completed event to other services.
        
        Args:
            session_id: Session identifier
            total_chunks: Total chunks uploaded
            total_duration_seconds: Total session duration
            
        Returns:
            Dict with emission results
        """
        try:
            event = SessionCompleteEvent(
                session_id=session_id,
                total_chunks=total_chunks,
                total_duration_seconds=total_duration_seconds
            )
            
            # Send to transcription service
            transcription_result = await self._send_session_complete_to_transcription(event)
            
            # Send to interview service
            interview_result = await self._send_session_complete_to_interview(event)
            
            logger.info(f"Emitted session completion event for session {session_id}")
            
            return {
                "success": True,
                "transcription_service": transcription_result,
                "interview_service": interview_result,
                "event": event.model_dump()
            }
            
        except Exception as e:
            logger.error(f"Error emitting session completion event: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _send_to_transcription_service(self, event: ChunkUploadEvent) -> Dict[str, Any]:
        """Send chunk upload event to transcription service."""
        try:
            url = f"{self.transcription_service_url}/transcription/chunk-notification"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=event.model_dump(),
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    logger.debug(f"Successfully notified transcription service about chunk {event.chunk_id}")
                    return {"success": True, "response": response.json()}
                else:
                    logger.warning(f"Transcription service returned {response.status_code}: {response.text}")
                    return {"success": False, "status_code": response.status_code, "error": response.text}
                    
        except httpx.TimeoutException:
            logger.error("Timeout connecting to transcription service")
            return {"success": False, "error": "timeout"}
        except httpx.ConnectError:
            logger.warning("Could not connect to transcription service - service may be down")
            return {"success": False, "error": "connection_failed"}
        except Exception as e:
            logger.error(f"Error sending to transcription service: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_to_interview_service(self, event: ChunkUploadEvent) -> Dict[str, Any]:
        """Send chunk upload event to interview service."""
        try:
            url = f"{self.interview_service_url}/interview/chunk-notification"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=event.model_dump(),
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    logger.debug(f"Successfully notified interview service about chunk {event.chunk_id}")
                    return {"success": True, "response": response.json()}
                else:
                    logger.warning(f"Interview service returned {response.status_code}: {response.text}")
                    return {"success": False, "status_code": response.status_code, "error": response.text}
                    
        except httpx.TimeoutException:
            logger.error("Timeout connecting to interview service")
            return {"success": False, "error": "timeout"}
        except httpx.ConnectError:
            logger.warning("Could not connect to interview service - service may be down")
            return {"success": False, "error": "connection_failed"}
        except Exception as e:
            logger.error(f"Error sending to interview service: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_session_complete_to_transcription(self, event: SessionCompleteEvent) -> Dict[str, Any]:
        """Send session completion event to transcription service."""
        try:
            url = f"{self.transcription_service_url}/transcription/session-complete"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=event.model_dump(),
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    logger.debug(f"Successfully notified transcription service about session completion {event.session_id}")
                    return {"success": True, "response": response.json()}
                else:
                    logger.warning(f"Transcription service returned {response.status_code}: {response.text}")
                    return {"success": False, "status_code": response.status_code, "error": response.text}
                    
        except Exception as e:
            logger.error(f"Error sending session completion to transcription service: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_session_complete_to_interview(self, event: SessionCompleteEvent) -> Dict[str, Any]:
        """Send session completion event to interview service."""
        try:
            url = f"{self.interview_service_url}/interview/session-complete"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=event.model_dump(),
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    logger.debug(f"Successfully notified interview service about session completion {event.session_id}")
                    return {"success": True, "response": response.json()}
                else:
                    logger.warning(f"Interview service returned {response.status_code}: {response.text}")
                    return {"success": False, "status_code": response.status_code, "error": response.text}
                    
        except Exception as e:
            logger.error(f"Error sending session completion to interview service: {e}")
            return {"success": False, "error": str(e)}


# Global event emission service instance
event_service = EventEmissionService()

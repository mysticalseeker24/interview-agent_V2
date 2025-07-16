"""
Event Service for inter-service communication.
"""
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
        self.resume_service_url = settings.resume_service_url
        
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
        """Emit chunk upload event to other services."""
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
        
        results = {}
        
        # Send to transcription service
        transcription_result = await self._send_to_transcription_service(event)
        results["transcription_service"] = transcription_result
        
        # Send to interview service
        interview_result = await self._send_to_interview_service(event)
        results["interview_service"] = interview_result
        
        logger.info(f"Emitted chunk upload event for session {session_id}, chunk {sequence_index}")
        return results
    
    async def emit_session_completed_event(
        self,
        session_id: str,
        total_chunks: int,
        total_duration_seconds: float
    ) -> Dict[str, Any]:
        """Emit session completion event to other services."""
        event = SessionCompleteEvent(
            session_id=session_id,
            total_chunks=total_chunks,
            total_duration_seconds=total_duration_seconds
        )
        
        results = {}
        
        # Send to transcription service
        transcription_result = await self._send_session_complete_to_transcription(event)
        results["transcription_service"] = transcription_result
        
        # Send to interview service
        interview_result = await self._send_session_complete_to_interview(event)
        results["interview_service"] = interview_result
        
        logger.info(f"Emitted session completion event for session {session_id}")
        return results
    
    async def _send_to_transcription_service(self, event: ChunkUploadEvent) -> Dict[str, Any]:
        """Send chunk upload event to transcription service."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.transcription_service_url}/api/v1/events/chunk-uploaded",
                    json=event.model_dump(),
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    logger.info(f"Successfully sent chunk upload event to transcription service")
                    return {"status": "success", "response": response.json()}
                else:
                    logger.warning(f"Transcription service returned {response.status_code}: {response.text}")
                    return {"status": "error", "status_code": response.status_code, "response": response.text}
                    
        except Exception as e:
            logger.error(f"Failed to send chunk upload event to transcription service: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _send_to_interview_service(self, event: ChunkUploadEvent) -> Dict[str, Any]:
        """Send chunk upload event to interview service."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.interview_service_url}/api/v1/events/chunk-uploaded",
                    json=event.model_dump(),
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    logger.info(f"Successfully sent chunk upload event to interview service")
                    return {"status": "success", "response": response.json()}
                else:
                    logger.warning(f"Interview service returned {response.status_code}: {response.text}")
                    return {"status": "error", "status_code": response.status_code, "response": response.text}
                    
        except Exception as e:
            logger.error(f"Failed to send chunk upload event to interview service: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _send_session_complete_to_transcription(self, event: SessionCompleteEvent) -> Dict[str, Any]:
        """Send session completion event to transcription service."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.transcription_service_url}/api/v1/events/session-completed",
                    json=event.model_dump(),
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    logger.info(f"Successfully sent session completion event to transcription service")
                    return {"status": "success", "response": response.json()}
                else:
                    logger.warning(f"Transcription service returned {response.status_code}: {response.text}")
                    return {"status": "error", "status_code": response.status_code, "response": response.text}
                    
        except Exception as e:
            logger.error(f"Failed to send session completion event to transcription service: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _send_session_complete_to_interview(self, event: SessionCompleteEvent) -> Dict[str, Any]:
        """Send session completion event to interview service."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.interview_service_url}/api/v1/events/session-completed",
                    json=event.model_dump(),
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    logger.info(f"Successfully sent session completion event to interview service")
                    return {"status": "success", "response": response.json()}
                else:
                    logger.warning(f"Interview service returned {response.status_code}: {response.text}")
                    return {"status": "error", "status_code": response.status_code, "response": response.text}
                    
        except Exception as e:
            logger.error(f"Failed to send session completion event to interview service: {e}")
            return {"status": "error", "error": str(e)}


# Global event service instance
event_service = EventEmissionService() 
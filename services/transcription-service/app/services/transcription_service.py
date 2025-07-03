"""Hybrid transcription service with OpenAI Whisper and AssemblyAI fallback."""
import logging
import os
import aiofiles
import asyncio
from typing import Dict, List, Optional, Any
from pathlib import Path
import httpx
from datetime import datetime

from app.core.config import get_settings
from app.schemas.transcription import TranscriptionResponse, TranscriptionSegment

logger = logging.getLogger(__name__)

settings = get_settings()


class TranscriptionService:
    """Service for hybrid audio transcription using OpenAI Whisper and AssemblyAI."""
    
    def __init__(self):
        """Initialize Transcription Service."""
        self.settings = settings
        self._ensure_upload_dir()
    
    def _ensure_upload_dir(self):
        """Ensure upload directory exists."""
        upload_dir = Path(self.settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_file_extension(self, filename: str) -> str:
        """Get file extension from filename."""
        return Path(filename).suffix.lower()
    
    def _is_allowed_file(self, filename: str) -> bool:
        """Check if file type is allowed."""
        extension = self._get_file_extension(filename)
        return extension in self.settings.ALLOWED_EXTENSIONS
    
    async def save_uploaded_file(self, file_content: bytes, filename: str, user_id: int) -> str:
        """
        Save uploaded file to disk.
        
        Args:
            file_content: File content bytes
            filename: Original filename
            user_id: User ID
            
        Returns:
            File path
        """
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        extension = self._get_file_extension(filename)
        safe_filename = f"{user_id}_{timestamp}_{filename}"
        file_path = Path(self.settings.UPLOAD_DIR) / safe_filename
        
        # Save file
        async with aiofiles.open(file_path, "wb") as buffer:
            await buffer.write(file_content)
        
        logger.info(f"Saved audio file: {file_path}")
        return str(file_path)
    
    async def transcribe_audio(self, file, language: str = None, user_id: int = None) -> Dict[str, Any]:
        """
        Transcribe audio using hybrid approach: OpenAI Whisper first, AssemblyAI fallback.
        
        Args:
            file: UploadFile object
            language: Language code (optional)
            user_id: User ID for file naming
            
        Returns:
            Transcription response with normalized format
        """
        logger.info(f"Starting transcription for file: {file.filename}")
        
        try:
            # Read file content
            file_content = await file.read()
            
            # Validate file type
            if not self._is_allowed_file(file.filename):
                raise ValueError(f"File type not supported: {file.filename}")
            
            # Save uploaded file
            file_path = await self.save_uploaded_file(file_content, file.filename, user_id or 1)
            
            try:
                # Try OpenAI Whisper first
                openai_result = await self._transcribe_with_openai(file_path)
                
                if openai_result:
                    # Check if confidence is acceptable
                    low_confidence = self._has_low_confidence(openai_result)
                    
                    if not low_confidence:
                        logger.info("OpenAI transcription successful with good confidence")
                        result = self._normalize_openai_response(openai_result)
                        return result.dict()
                    else:
                        logger.warning("OpenAI transcription has low confidence, using fallback")
                
                # Fallback to AssemblyAI
                assemblyai_result = await self._transcribe_with_assemblyai(file_path)
                
                if assemblyai_result:
                    logger.info("AssemblyAI fallback transcription successful")
                    result = self._normalize_assemblyai_response(assemblyai_result, fallback_used=True)
                    return result.dict()
                
                raise Exception("Both OpenAI and AssemblyAI transcription failed")
                
            finally:
                # Clean up uploaded file
                try:
                    os.remove(file_path)
                    logger.info(f"Cleaned up temporary file: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up file {file_path}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise
    
    async def _transcribe_with_openai(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Transcribe audio using OpenAI Whisper API.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            OpenAI transcription response or None if failed
        """
        try:
            logger.info("Attempting OpenAI Whisper transcription")
            
            async with httpx.AsyncClient(timeout=300.0) as client:
                with open(file_path, 'rb') as audio_file:
                    files = {
                        'file': (Path(file_path).name, audio_file, 'audio/mpeg'),
                        'model': (None, self.settings.WHISPER_MODEL),
                        'response_format': (None, 'verbose_json'),
                        'timestamp_granularities[]': (None, 'segment')
                    }
                    
                    headers = {
                        'Authorization': f'Bearer {self.settings.OPENAI_API_KEY}'
                    }
                    
                    response = await client.post(
                        'https://api.openai.com/v1/audio/transcriptions',
                        files=files,
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        logger.info("OpenAI transcription successful")
                        return result
                    else:
                        logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                        return None
                        
        except Exception as e:
            logger.error(f"OpenAI transcription error: {str(e)}")
            return None
    
    async def _transcribe_with_assemblyai(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Transcribe audio using AssemblyAI API.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            AssemblyAI transcription response or None if failed
        """
        try:
            logger.info("Attempting AssemblyAI transcription")
            
            # Step 1: Upload file to AssemblyAI
            upload_url = await self._upload_to_assemblyai(file_path)
            if not upload_url:
                return None
            
            # Step 2: Submit transcription request
            transcript_id = await self._submit_assemblyai_transcription(upload_url)
            if not transcript_id:
                return None
            
            # Step 3: Poll for completion
            result = await self._poll_assemblyai_transcription(transcript_id)
            return result
            
        except Exception as e:
            logger.error(f"AssemblyAI transcription error: {str(e)}")
            return None
    
    async def _upload_to_assemblyai(self, file_path: str) -> Optional[str]:
        """Upload file to AssemblyAI and get upload URL."""
        try:
            async with httpx.AsyncClient() as client:
                with open(file_path, 'rb') as audio_file:
                    headers = {
                        'authorization': self.settings.ASSEMBLYAI_API_KEY
                    }
                    
                    response = await client.post(
                        f'{self.settings.ASSEMBLYAI_BASE_URL}/upload',
                        files={'file': audio_file},
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        return result.get('upload_url')
                    else:
                        logger.error(f"AssemblyAI upload error: {response.status_code}")
                        return None
                        
        except Exception as e:
            logger.error(f"AssemblyAI upload error: {str(e)}")
            return None
    
    async def _submit_assemblyai_transcription(self, audio_url: str) -> Optional[str]:
        """Submit transcription request to AssemblyAI."""
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    'authorization': self.settings.ASSEMBLYAI_API_KEY,
                    'content-type': 'application/json'
                }
                
                data = {
                    'audio_url': audio_url,
                    'word_boost': [],
                    'boost_param': 'low'
                }
                
                response = await client.post(
                    f'{self.settings.ASSEMBLYAI_BASE_URL}/transcript',
                    json=data,
                    headers=headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get('id')
                else:
                    logger.error(f"AssemblyAI submit error: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"AssemblyAI submit error: {str(e)}")
            return None
    
    async def _poll_assemblyai_transcription(self, transcript_id: str) -> Optional[Dict[str, Any]]:
        """Poll AssemblyAI transcription until completed."""
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    'authorization': self.settings.ASSEMBLYAI_API_KEY
                }
                
                max_attempts = 60  # 5 minutes max
                attempt = 0
                
                while attempt < max_attempts:
                    response = await client.get(
                        f'{self.settings.ASSEMBLYAI_BASE_URL}/transcript/{transcript_id}',
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        status = result.get('status')
                        
                        if status == 'completed':
                            logger.info("AssemblyAI transcription completed")
                            return result
                        elif status == 'error':
                            logger.error(f"AssemblyAI transcription error: {result.get('error')}")
                            return None
                        else:
                            # Still processing, wait and retry
                            await asyncio.sleep(5)
                            attempt += 1
                    else:
                        logger.error(f"AssemblyAI poll error: {response.status_code}")
                        return None
                
                logger.error("AssemblyAI transcription timeout")
                return None
                
        except Exception as e:
            logger.error(f"AssemblyAI poll error: {str(e)}")
            return None
    
    def _has_low_confidence(self, openai_result: Dict[str, Any]) -> bool:
        """
        Check if OpenAI transcription has low confidence segments.
        
        Args:
            openai_result: OpenAI transcription response
            
        Returns:
            True if any segment has confidence below threshold
        """
        segments = openai_result.get('segments', [])
        if not segments:
            return True
        
        # Check if any segment has low confidence
        for segment in segments:
            confidence = segment.get('no_speech_prob', 0)
            # Note: no_speech_prob is inverse of confidence
            actual_confidence = 1.0 - confidence
            if actual_confidence < self.settings.CONFIDENCE_THRESHOLD:
                return True
        
        return False
    
    def _normalize_openai_response(self, openai_result: Dict[str, Any]) -> TranscriptionResponse:
        """Normalize OpenAI response to standard format."""
        text = openai_result.get('text', '')
        segments_data = openai_result.get('segments', [])
        
        segments = []
        total_confidence = 0
        
        for seg in segments_data:
            confidence = 1.0 - seg.get('no_speech_prob', 0)
            total_confidence += confidence
            
            segments.append(TranscriptionSegment(
                start=seg.get('start', 0),
                end=seg.get('end', 0),
                text=seg.get('text', ''),
                confidence=confidence
            ))
        
        avg_confidence = total_confidence / len(segments) if segments else 0
        
        return TranscriptionResponse(
            transcript=text,
            segments=segments,
            confidence_score=avg_confidence,
            provider="openai",
            fallback_used=False,
            duration_seconds=openai_result.get('duration')
        )
    
    def _normalize_assemblyai_response(
        self, 
        assemblyai_result: Dict[str, Any], 
        fallback_used: bool = True
    ) -> TranscriptionResponse:
        """Normalize AssemblyAI response to standard format."""
        text = assemblyai_result.get('text', '')
        words = assemblyai_result.get('words', [])
        
        # Group words into segments (every 10 words or by sentence)
        segments = []
        if words:
            current_segment = []
            segment_start = words[0].get('start', 0) / 1000.0  # Convert to seconds
            
            for i, word in enumerate(words):
                current_segment.append(word)
                
                # Create segment every 10 words or at sentence end
                if len(current_segment) >= 10 or i == len(words) - 1:
                    segment_end = word.get('end', 0) / 1000.0
                    segment_text = ' '.join([w.get('text', '') for w in current_segment])
                    segment_confidence = sum([w.get('confidence', 0) for w in current_segment]) / len(current_segment)
                    
                    segments.append(TranscriptionSegment(
                        start=segment_start,
                        end=segment_end,
                        text=segment_text,
                        confidence=segment_confidence
                    ))
                    
                    current_segment = []
                    if i < len(words) - 1:
                        segment_start = words[i + 1].get('start', 0) / 1000.0
        
        # Calculate average confidence
        avg_confidence = assemblyai_result.get('confidence', 0)
        
        return TranscriptionResponse(
            transcript=text,
            segments=segments,
            confidence_score=avg_confidence,
            provider="assemblyai",
            fallback_used=fallback_used,
            duration_seconds=assemblyai_result.get('audio_duration')
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Health check for external APIs.
        
        Returns:
            Health check result
        """
        try:
            health_status = {"healthy": True, "services": {}}
            
            # Check OpenAI API
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        "https://api.openai.com/v1/models",
                        headers={"Authorization": f"Bearer {self.settings.OPENAI_API_KEY}"},
                        timeout=10.0
                    )
                    if response.status_code == 200:
                        health_status["services"]["openai"] = {"status": "healthy", "message": "API accessible"}
                    else:
                        health_status["services"]["openai"] = {"status": "unhealthy", "message": f"API returned {response.status_code}"}
                        health_status["healthy"] = False
            except Exception as e:
                health_status["services"]["openai"] = {"status": "unhealthy", "message": f"API check failed: {str(e)}"}
                health_status["healthy"] = False
            
            # Check AssemblyAI API
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        "https://api.assemblyai.com/v2/transcript",
                        headers={"authorization": self.settings.ASSEMBLYAI_API_KEY},
                        timeout=10.0
                    )
                    if response.status_code in [200, 404]:  # 404 is expected for empty transcript list
                        health_status["services"]["assemblyai"] = {"status": "healthy", "message": "API accessible"}
                    else:
                        health_status["services"]["assemblyai"] = {"status": "unhealthy", "message": f"API returned {response.status_code}"}
                        health_status["healthy"] = False
            except Exception as e:
                health_status["services"]["assemblyai"] = {"status": "unhealthy", "message": f"API check failed: {str(e)}"}
                health_status["healthy"] = False
            
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {"healthy": False, "error": str(e)}

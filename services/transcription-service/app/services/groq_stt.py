import json
import logging
import base64
from typing import Dict, Any, Optional, List
import httpx
from ..core.config import settings

logger = logging.getLogger(__name__)


class GroqSTTClient:
    """Client for Groq Speech-to-Text API using Whisper model."""
    
    def __init__(self):
        self.api_key = settings.groq_api_key
        self.base_url = settings.groq_base_url
        self.model = settings.groq_stt_model
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def transcribe(
        self, 
        audio_bytes: bytes,
        language: Optional[str] = None,
        prompt: Optional[str] = None,
        response_format: str = "verbose_json"
    ) -> Dict[str, Any]:
        """
        Transcribe audio using Groq Whisper Large v3 API.
        
        Args:
            audio_bytes: Audio data as bytes
            language: Language code (optional, auto-detected if not provided)
            prompt: Optional prompt for context
            response_format: Response format (json, verbose_json, text, srt, vtt)
            
        Returns:
            Dictionary containing transcription results
        """
        try:
            # Prepare request payload according to Groq API docs
            # Make API request to Groq transcriptions endpoint
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Prepare form data for file upload
                files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
                data = {
                    "model": self.model,
                    "response_format": response_format,
                    "temperature": "0.0"
                }
                
                if prompt:
                    data["prompt"] = prompt
                
                response = await client.post(
                    f"{self.base_url}/audio/transcriptions",
                    headers=self.headers,
                    data=data,
                    files=files
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"STT transcription successful, text length: {len(result.get('text', ''))}")
                    
                    # Process response based on format
                    processed_result = self._process_response(result, response_format)
                    return processed_result
                else:
                    error_msg = f"Groq API error: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    raise Exception(error_msg)
                    
        except httpx.TimeoutException:
            error_msg = "Groq API request timed out"
            logger.error(error_msg)
            raise Exception(error_msg)
        except httpx.RequestError as e:
            error_msg = f"Groq API request failed: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"STT transcription failed: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def _process_response(self, response: Dict[str, Any], response_format: str) -> Dict[str, Any]:
        """Process the API response based on format."""
        if response_format == "verbose_json":
            # Extract text and segments
            text = response.get("text", "")
            segments = response.get("segments", [])
            
            # Calculate confidence from segments
            confidence = self._calculate_confidence(segments)
            
            return {
                "text": text,
                "segments": segments,
                "confidence": confidence,
                "language": response.get("language", "en"),
                "duration": response.get("duration", 0.0)
            }
        elif response_format == "json":
            # Simple JSON format
            return {
                "text": response.get("text", ""),
                "segments": [],
                "confidence": 0.0,
                "language": "en",
                "duration": 0.0
            }
        else:
            # Text format
            return {
                "text": response.get("text", ""),
                "segments": [],
                "confidence": 0.0,
                "language": "en",
                "duration": 0.0
            }
    
    def _calculate_confidence(self, segments: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence from segments."""
        if not segments:
            return 0.0
        
        total_confidence = 0.0
        total_duration = 0.0
        
        for segment in segments:
            confidence = segment.get("avg_logprob", 0.0)
            duration = segment.get("end", 0.0) - segment.get("start", 0.0)
            
            total_confidence += confidence * duration
            total_duration += duration
        
        if total_duration > 0:
            return total_confidence / total_duration
        else:
            return 0.0
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if Groq API is accessible."""
        try:
            # Test with a simple request
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    models = response.json()
                    available_models = [model.get("id") for model in models.get("data", [])]
                    
                    return {
                        "status": "healthy",
                        "message": "Groq API accessible",
                        "available_models": available_models,
                        "whisper_model_available": self.model in available_models
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "message": f"Groq API error: {response.status_code}",
                        "available_models": [],
                        "whisper_model_available": False
                    }
                    
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Groq API connection failed: {str(e)}",
                "available_models": [],
                "whisper_model_available": False
            }
    
    async def get_available_models(self) -> List[str]:
        """Get list of available Groq models."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    models_data = response.json()
                    return [model.get("id") for model in models_data.get("data", [])]
                else:
                    logger.error(f"Failed to get models: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting models: {str(e)}")
            return [] 
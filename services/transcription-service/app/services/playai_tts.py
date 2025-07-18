import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional
import httpx
from ..core.config import settings

logger = logging.getLogger(__name__)


class GroqTTSClient:
    """Client for Groq Text-to-Speech API using Play.ai TTS model."""
    
    def __init__(self):
        self.api_key = settings.groq_api_key
        self.base_url = settings.groq_base_url
        self.model = settings.groq_tts_model
        self.default_voice = settings.groq_default_voice
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.cache_dir = settings.tts_cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    async def synthesize(
        self, 
        text: str, 
        voice: str = None, 
        format: str = "wav"
    ) -> Dict[str, Any]:
        """
        Synthesize text to speech using Groq Play.ai TTS API.
        
        Args:
            text: Text to synthesize (max 10K characters)
            voice: Voice to use (defaults to configured default)
            format: Audio format (wav is the only supported format)
            
        Returns:
            Dictionary containing synthesis results
        """
        try:
            voice = voice or self.default_voice
            
            # Check cache first
            cache_key = self._generate_cache_key(text, voice, format)
            cached_result = await self._check_cache(cache_key)
            if cached_result:
                logger.info(f"TTS cache hit for text: {text[:50]}...")
                return cached_result
            
            # Prepare request payload according to Groq API docs
            payload = {
                "model": self.model,
                "input": text,
                "voice": voice,
                "response_format": format,
                "sample_rate": 48000,  # Default sample rate
                "speed": 1.0  # Normal speed
            }
            
            # Make API request to Groq speech endpoint
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/audio/speech",
                    headers=self.headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    # Groq returns audio data directly
                    audio_data = response.content
                    logger.info(f"TTS synthesis successful for text: {text[:50]}...")
                    
                    # Save to cache
                    cache_result = await self._save_to_cache(cache_key, audio_data, text, voice, format)
                    return cache_result
                else:
                    error_msg = f"Groq TTS API error: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    raise Exception(error_msg)
                    
        except httpx.TimeoutException:
            error_msg = "Groq TTS API request timed out"
            logger.error(error_msg)
            raise Exception(error_msg)
        except httpx.RequestError as e:
            error_msg = f"Groq TTS API request failed: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"TTS synthesis failed: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def _generate_cache_key(self, text: str, voice: str, format: str) -> str:
        """Generate a cache key for the TTS request."""
        import hashlib
        content = f"{text}:{voice}:{format}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def _check_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Check if result exists in cache."""
        try:
            cache_file = self.cache_dir / f"{cache_key}.json"
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                # Check if audio file still exists
                audio_file = Path(cache_data.get("file_path", ""))
                if audio_file.exists():
                    return {
                        "file_url": f"/tts/files/{cache_key}.{cache_data.get('format', 'wav')}",
                        "file_path": str(audio_file),
                        "file_size_bytes": audio_file.stat().st_size if audio_file.exists() else None,
                        "duration_seconds": cache_data.get("duration_seconds"),
                        "is_cached": True,
                        "cache_key": cache_key
                    }
        except Exception as e:
            logger.warning(f"Cache check failed: {str(e)}")
        
        return None
    
    async def _save_to_cache(
        self, 
        cache_key: str, 
        audio_data: bytes, 
        text: str, 
        voice: str, 
        format: str
    ) -> Dict[str, Any]:
        """Save TTS result to cache."""
        try:
            # Save audio file
            audio_file = self.cache_dir / f"{cache_key}.{format}"
            with open(audio_file, 'wb') as f:
                f.write(audio_data)
            
            # Estimate duration (rough calculation for WAV)
            # WAV at 44.1kHz, 16-bit, mono: ~176KB per second
            estimated_duration = len(audio_data) / 176000  # Rough estimate for WAV
            
            # Save metadata
            metadata = {
                "text": text,
                "voice": voice,
                "format": format,
                "file_path": str(audio_file),
                "duration_seconds": estimated_duration,
                "file_size_bytes": len(audio_data),
                "created_at": str(Path().stat().st_mtime)
            }
            
            metadata_file = self.cache_dir / f"{cache_key}.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f)
            
            return {
                "file_url": f"/tts/files/{cache_key}.{format}",
                "file_path": str(audio_file),
                "file_size_bytes": len(audio_data),
                "duration_seconds": estimated_duration,
                "is_cached": False,
                "cache_key": cache_key
            }
            
        except Exception as e:
            logger.error(f"Failed to save to cache: {str(e)}")
            raise
    
    async def get_cache_info(self) -> Dict[str, Any]:
        """Get information about TTS cache."""
        try:
            cache_files = list(self.cache_dir.glob("*.json"))
            total_requests = len(cache_files)
            
            total_size = 0
            total_duration = 0.0
            
            for cache_file in cache_files:
                try:
                    with open(cache_file, 'r') as f:
                        metadata = json.load(f)
                        total_size += metadata.get("file_size_bytes", 0)
                        total_duration += metadata.get("duration_seconds", 0.0)
                except Exception as e:
                    logger.warning(f"Failed to read cache file {cache_file}: {str(e)}")
            
            return {
                "total_requests": total_requests,
                "cache_hits": 0,  # Would need to track this separately
                "cache_misses": 0,  # Would need to track this separately
                "total_file_size": total_size,
                "average_duration": total_duration / total_requests if total_requests > 0 else 0.0
            }
            
        except Exception as e:
            logger.error(f"Failed to get cache info: {str(e)}")
            return {
                "total_requests": 0,
                "cache_hits": 0,
                "cache_misses": 0,
                "total_file_size": 0,
                "average_duration": 0.0
            }
    
    async def cleanup_old_files(self, max_age_days: int = 7) -> Dict[str, int]:
        """Clean up old cached files."""
        try:
            import time
            current_time = time.time()
            max_age_seconds = max_age_days * 24 * 60 * 60
            
            deleted_files = 0
            deleted_size = 0
            
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    file_age = current_time - cache_file.stat().st_mtime
                    if file_age > max_age_seconds:
                        # Read metadata to get audio file path
                        with open(cache_file, 'r') as f:
                            metadata = json.load(f)
                        
                        # Delete audio file
                        audio_file = Path(metadata.get("file_path", ""))
                        if audio_file.exists():
                            file_size = audio_file.stat().st_size
                            audio_file.unlink()
                            deleted_size += file_size
                        
                        # Delete metadata file
                        cache_file.unlink()
                        deleted_files += 1
                        
                except Exception as e:
                    logger.warning(f"Failed to clean up {cache_file}: {str(e)}")
            
            return {
                "deleted_files": deleted_files,
                "deleted_size_bytes": deleted_size
            }
            
        except Exception as e:
            logger.error(f"Failed to cleanup old files: {str(e)}")
            return {"deleted_files": 0, "deleted_size_bytes": 0}
    
    async def cleanup_cache(self) -> Dict[str, Any]:
        """
        Clean up TTS cache after interview sessions.
        
        This method removes old cached files to free up disk space
        and prevent accumulation of unused audio files.
        """
        try:
            # Clean up files older than 1 day (more aggressive for interview sessions)
            cleanup_result = await self.cleanup_old_files(max_age_days=1)
            
            # Also clean up files if cache is getting too large (>100MB)
            cache_info = await self.get_cache_info()
            if cache_info.get("total_file_size", 0) > 100 * 1024 * 1024:  # 100MB
                logger.info("Cache size exceeded 100MB, performing additional cleanup")
                additional_cleanup = await self.cleanup_old_files(max_age_days=0.5)  # 12 hours
                cleanup_result["deleted_files"] += additional_cleanup["deleted_files"]
                cleanup_result["deleted_size_bytes"] += additional_cleanup["deleted_size_bytes"]
            
            logger.info(f"TTS cache cleanup completed: {cleanup_result}")
            return {
                "status": "success",
                "message": "TTS cache cleaned successfully",
                "cleanup_result": cleanup_result
            }
            
        except Exception as e:
            logger.error(f"TTS cache cleanup failed: {str(e)}")
            return {
                "status": "error",
                "message": f"TTS cache cleanup failed: {str(e)}",
                "cleanup_result": {"deleted_files": 0, "deleted_size_bytes": 0}
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if Groq TTS API is accessible."""
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
                        "message": "Groq TTS API accessible",
                        "available_models": available_models,
                        "tts_model_available": self.model in available_models
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "message": f"Groq TTS API error: {response.status_code}",
                        "available_models": [],
                        "tts_model_available": False
                    }
                    
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Groq TTS API connection failed: {str(e)}",
                "available_models": [],
                "tts_model_available": False
            }
    
    async def get_available_voices(self) -> list[str]:
        """Get list of available voices for Groq TTS."""
        try:
            # According to Groq docs, these are the available English voices
            english_voices = [
                "Arista-PlayAI", "Atlas-PlayAI", "Basil-PlayAI", "Briggs-PlayAI", 
                "Calum-PlayAI", "Celeste-PlayAI", "Cheyenne-PlayAI", "Chip-PlayAI", 
                "Cillian-PlayAI", "Deedee-PlayAI", "Fritz-PlayAI", "Gail-PlayAI",
                "Indigo-PlayAI", "Mamaw-PlayAI", "Mason-PlayAI", "Mikail-PlayAI", 
                "Mitch-PlayAI", "Quinn-PlayAI", "Thunder-PlayAI"
            ]
            return english_voices
                    
        except Exception as e:
            logger.error(f"Error getting voices: {str(e)}")
            return [] 
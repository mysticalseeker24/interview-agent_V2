"""
Device Service for handling media device enumeration.
"""
import logging
import platform
from typing import Dict, List, Any

from app.schemas.media import MediaDevice, DeviceEnumerationResponse

logger = logging.getLogger(__name__)


class DeviceService:
    """Service for handling media device operations."""
    
    def __init__(self):
        self.platform = platform.system().lower()
    
    async def get_available_devices(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get available media devices."""
        try:
            devices = {
                "audio_inputs": await self._get_audio_input_devices(),
                "audio_outputs": await self._get_audio_output_devices(),
                "video_inputs": await self._get_video_input_devices()
            }
            
            logger.info(f"Retrieved {len(devices['audio_inputs'])} audio inputs, "
                       f"{len(devices['audio_outputs'])} audio outputs, "
                       f"{len(devices['video_inputs'])} video inputs")
            
            return devices
            
        except Exception as e:
            logger.error(f"Error getting available devices: {e}")
            return self._get_default_devices()
    
    async def _get_audio_input_devices(self) -> List[Dict[str, Any]]:
        """Get available audio input devices."""
        try:
            # This is a stub implementation
            # In a real implementation, you would use libraries like:
            # - pyaudio for cross-platform audio
            # - sounddevice for Python audio
            # - webrtc for browser-based audio
            
            devices = [
                {
                    "device_id": "default_mic",
                    "name": "Default Microphone",
                    "type": "audio_input",
                    "is_default": True,
                    "sample_rates": [8000, 16000, 22050, 44100, 48000],
                    "channels": [1, 2],
                    "formats": ["webm", "mp3", "wav"]
                },
                {
                    "device_id": "builtin_mic",
                    "name": "Built-in Microphone",
                    "type": "audio_input",
                    "is_default": False,
                    "sample_rates": [8000, 16000, 22050, 44100, 48000],
                    "channels": [1, 2],
                    "formats": ["webm", "mp3", "wav"]
                }
            ]
            
            return devices
            
        except Exception as e:
            logger.error(f"Error getting audio input devices: {e}")
            return self._get_default_audio_inputs()
    
    async def _get_audio_output_devices(self) -> List[Dict[str, Any]]:
        """Get available audio output devices."""
        try:
            # This is a stub implementation
            devices = [
                {
                    "device_id": "default_speaker",
                    "name": "Default Speaker",
                    "type": "audio_output",
                    "is_default": True,
                    "sample_rates": [8000, 16000, 22050, 44100, 48000],
                    "channels": [1, 2],
                    "formats": ["webm", "mp3", "wav"]
                },
                {
                    "device_id": "builtin_speaker",
                    "name": "Built-in Speaker",
                    "type": "audio_output",
                    "is_default": False,
                    "sample_rates": [8000, 16000, 22050, 44100, 48000],
                    "channels": [1, 2],
                    "formats": ["webm", "mp3", "wav"]
                }
            ]
            
            return devices
            
        except Exception as e:
            logger.error(f"Error getting audio output devices: {e}")
            return self._get_default_audio_outputs()
    
    async def _get_video_input_devices(self) -> List[Dict[str, Any]]:
        """Get available video input devices."""
        try:
            # This is a stub implementation
            # In a real implementation, you would use libraries like:
            # - opencv-python for video capture
            # - webrtc for browser-based video
            
            devices = [
                {
                    "device_id": "default_camera",
                    "name": "Default Camera",
                    "type": "video_input",
                    "is_default": True,
                    "resolutions": [
                        {"width": 640, "height": 480, "fps": [15, 30]},
                        {"width": 1280, "height": 720, "fps": [15, 30]},
                        {"width": 1920, "height": 1080, "fps": [15, 30]}
                    ],
                    "formats": ["webm", "mp4"]
                },
                {
                    "device_id": "front_camera",
                    "name": "Front Camera",
                    "type": "video_input",
                    "is_default": False,
                    "resolutions": [
                        {"width": 640, "height": 480, "fps": [15, 30]},
                        {"width": 1280, "height": 720, "fps": [15, 30]}
                    ],
                    "formats": ["webm", "mp4"]
                }
            ]
            
            return devices
            
        except Exception as e:
            logger.error(f"Error getting video input devices: {e}")
            return self._get_default_video_inputs()
    
    def _get_default_devices(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get default devices when enumeration fails."""
        return {
            "audio_inputs": self._get_default_audio_inputs(),
            "audio_outputs": self._get_default_audio_outputs(),
            "video_inputs": self._get_default_video_inputs()
        }
    
    def _get_default_audio_inputs(self) -> List[Dict[str, Any]]:
        """Get default audio input devices."""
        return [
            {
                "device_id": "default_mic",
                "name": "Default Microphone",
                "type": "audio_input",
                "is_default": True,
                "sample_rates": [8000, 16000, 22050, 44100, 48000],
                "channels": [1, 2],
                "formats": ["webm", "mp3", "wav"]
            }
        ]
    
    def _get_default_audio_outputs(self) -> List[Dict[str, Any]]:
        """Get default audio output devices."""
        return [
            {
                "device_id": "default_speaker",
                "name": "Default Speaker",
                "type": "audio_output",
                "is_default": True,
                "sample_rates": [8000, 16000, 22050, 44100, 48000],
                "channels": [1, 2],
                "formats": ["webm", "mp3", "wav"]
            }
        ]
    
    def _get_default_video_inputs(self) -> List[Dict[str, Any]]:
        """Get default video input devices."""
        return [
            {
                "device_id": "default_camera",
                "name": "Default Camera",
                "type": "video_input",
                "is_default": True,
                "resolutions": [
                    {"width": 640, "height": 480, "fps": [15, 30]},
                    {"width": 1280, "height": 720, "fps": [15, 30]}
                ],
                "formats": ["webm", "mp4"]
            }
        ]


# Global device service instance
device_service = DeviceService() 
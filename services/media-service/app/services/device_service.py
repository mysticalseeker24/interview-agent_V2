"""
Device enumeration service for Media Service.
"""
import logging
import platform
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class DeviceService:
    """Service for enumerating available media devices."""
    
    def __init__(self):
        self.platform = platform.system().lower()
    
    async def get_available_devices(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get available audio and video devices.
        
        Returns:
            Dict with 'audio_inputs', 'audio_outputs', and 'video_inputs' lists
        """
        try:
            devices = {
                "audio_inputs": await self._get_audio_input_devices(),
                "audio_outputs": await self._get_audio_output_devices(),
                "video_inputs": await self._get_video_input_devices(),
            }
            
            logger.info(f"Enumerated devices: {len(devices['audio_inputs'])} audio inputs, "
                       f"{len(devices['audio_outputs'])} audio outputs, "
                       f"{len(devices['video_inputs'])} video inputs")
            
            return devices
            
        except Exception as e:
            logger.error(f"Error enumerating devices: {e}")
            # Return default devices on error
            return self._get_default_devices()
    
    async def _get_audio_input_devices(self) -> List[Dict[str, Any]]:
        """Get available audio input devices (microphones)."""
        try:
            # For production, you would use libraries like pyaudio, sounddevice, or platform APIs
            # This is a mock implementation for demonstration
            if self.platform == "windows":
                return [
                    {
                        "device_id": "default_mic",
                        "name": "Default Microphone",
                        "type": "audio_input",
                        "is_default": True,
                        "sample_rates": [8000, 16000, 22050, 44100, 48000],
                        "channels": [1, 2]
                    },
                    {
                        "device_id": "builtin_mic",
                        "name": "Built-in Microphone",
                        "type": "audio_input",
                        "is_default": False,
                        "sample_rates": [16000, 44100],
                        "channels": [1, 2]
                    }
                ]
            else:
                return [
                    {
                        "device_id": "default_mic",
                        "name": "Default Audio Input",
                        "type": "audio_input",
                        "is_default": True,
                        "sample_rates": [8000, 16000, 22050, 44100, 48000],
                        "channels": [1, 2]
                    }
                ]
                
        except Exception as e:
            logger.error(f"Error getting audio input devices: {e}")
            return self._get_default_audio_inputs()
    
    async def _get_audio_output_devices(self) -> List[Dict[str, Any]]:
        """Get available audio output devices (speakers)."""
        try:
            if self.platform == "windows":
                return [
                    {
                        "device_id": "default_speakers",
                        "name": "Default Speakers",
                        "type": "audio_output",
                        "is_default": True,
                        "sample_rates": [8000, 16000, 22050, 44100, 48000],
                        "channels": [1, 2]
                    },
                    {
                        "device_id": "builtin_speakers",
                        "name": "Built-in Speakers",
                        "type": "audio_output",
                        "is_default": False,
                        "sample_rates": [16000, 44100],
                        "channels": [2]
                    }
                ]
            else:
                return [
                    {
                        "device_id": "default_speakers",
                        "name": "Default Audio Output",
                        "type": "audio_output",
                        "is_default": True,
                        "sample_rates": [8000, 16000, 22050, 44100, 48000],
                        "channels": [1, 2]
                    }
                ]
                
        except Exception as e:
            logger.error(f"Error getting audio output devices: {e}")
            return self._get_default_audio_outputs()
    
    async def _get_video_input_devices(self) -> List[Dict[str, Any]]:
        """Get available video input devices (cameras)."""
        try:
            if self.platform == "windows":
                return [
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
                        "formats": ["mjpeg", "yuy2", "nv12"]
                    },
                    {
                        "device_id": "builtin_camera",
                        "name": "Built-in Camera",
                        "type": "video_input",
                        "is_default": False,
                        "resolutions": [
                            {"width": 640, "height": 480, "fps": [15, 30]},
                            {"width": 1280, "height": 720, "fps": [30]}
                        ],
                        "formats": ["mjpeg", "yuy2"]
                    }
                ]
            else:
                return [
                    {
                        "device_id": "default_camera",
                        "name": "Default Video Input",
                        "type": "video_input",
                        "is_default": True,
                        "resolutions": [
                            {"width": 640, "height": 480, "fps": [15, 30]},
                            {"width": 1280, "height": 720, "fps": [30]}
                        ],
                        "formats": ["mjpeg", "yuy2"]
                    }
                ]
                
        except Exception as e:
            logger.error(f"Error getting video input devices: {e}")
            return self._get_default_video_inputs()
    
    def _get_default_devices(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get default devices when enumeration fails."""
        return {
            "audio_inputs": self._get_default_audio_inputs(),
            "audio_outputs": self._get_default_audio_outputs(),
            "video_inputs": self._get_default_video_inputs(),
        }
    
    def _get_default_audio_inputs(self) -> List[Dict[str, Any]]:
        """Get default audio input devices."""
        return [
            {
                "device_id": "default_mic",
                "name": "Default Microphone",
                "type": "audio_input",
                "is_default": True,
                "sample_rates": [16000, 44100],
                "channels": [1, 2]
            }
        ]
    
    def _get_default_audio_outputs(self) -> List[Dict[str, Any]]:
        """Get default audio output devices."""
        return [
            {
                "device_id": "default_speakers",
                "name": "Default Speakers",
                "type": "audio_output",
                "is_default": True,
                "sample_rates": [16000, 44100],
                "channels": [1, 2]
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
                    {"width": 1280, "height": 720, "fps": [30]}
                ],
                "formats": ["mjpeg"]
            }
        ]


# Global device service instance
device_service = DeviceService()

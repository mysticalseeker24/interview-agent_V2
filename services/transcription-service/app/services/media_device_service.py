"""Media device enumeration service."""
import logging
import platform
from typing import List, Dict, Any

from app.schemas.media import MediaDeviceInfo, MediaDeviceCapabilities

logger = logging.getLogger(__name__)


class MediaDeviceService:
    """Service for media device enumeration and management."""
    
    def __init__(self):
        """Initialize Media Device Service."""
        self.platform = platform.system().lower()
    
    async def get_media_devices(self) -> Dict[str, List[MediaDeviceInfo]]:
        """
        Get available media devices.
        
        Returns:
            Dictionary with audio and video device lists
        """
        try:
            audio_devices = await self._get_audio_devices()
            video_devices = await self._get_video_devices()
            
            logger.info(f"Found {len(audio_devices)} audio and {len(video_devices)} video devices")
            
            return {
                "audio_devices": audio_devices,
                "video_devices": video_devices,
                "total_devices": len(audio_devices) + len(video_devices)
            }
            
        except Exception as e:
            logger.error(f"Error enumerating devices: {str(e)}")
            # Return stub devices as fallback
            return await self._get_stub_devices()
    
    async def _get_audio_devices(self) -> List[MediaDeviceInfo]:
        """Get available audio input devices."""
        # This is a stub implementation
        # In production, you would use platform-specific APIs
        stub_devices = [
            MediaDeviceInfo(
                device_id="default_microphone",
                device_name="Default Microphone",
                device_type="audio",
                is_default=True,
                is_available=True,
                capabilities=MediaDeviceCapabilities(
                    sample_rates=[44100, 48000],
                    formats=["PCM", "MP3"],
                    channels=[1, 2]
                )
            ),
            MediaDeviceInfo(
                device_id="built_in_microphone",
                device_name="Built-in Microphone",
                device_type="audio",
                is_default=False,
                is_available=True,
                capabilities=MediaDeviceCapabilities(
                    sample_rates=[44100],
                    formats=["PCM"],
                    channels=[1, 2]
                )
            )
        ]
        
        if self.platform == "windows":
            stub_devices.append(
                MediaDeviceInfo(
                    device_id="realtek_audio",
                    device_name="Realtek HD Audio",
                    device_type="audio",
                    is_default=False,
                    is_available=True,
                    capabilities=MediaDeviceCapabilities(
                        sample_rates=[44100, 48000, 96000],
                        formats=["PCM", "MP3", "AAC"],
                        channels=[1, 2, 4, 6, 8]
                    )
                )
            )
        elif self.platform == "darwin":  # macOS
            stub_devices.append(
                MediaDeviceInfo(
                    device_id="coreaudio_input",
                    device_name="Core Audio Input",
                    device_type="audio",
                    is_default=False,
                    is_available=True,
                    capabilities=MediaDeviceCapabilities(
                        sample_rates=[44100, 48000, 96000],
                        formats=["PCM", "AAC"],
                        channels=[1, 2]
                    )
                )
            )
        elif self.platform == "linux":
            stub_devices.append(
                MediaDeviceInfo(
                    device_id="pulse_audio",
                    device_name="PulseAudio Input",
                    device_type="audio",
                    is_default=False,
                    is_available=True,
                    capabilities=MediaDeviceCapabilities(
                        sample_rates=[44100, 48000],
                        formats=["PCM"],
                        channels=[1, 2]
                    )
                )
            )
        
        return stub_devices
    
    async def _get_video_devices(self) -> List[MediaDeviceInfo]:
        """Get available video input devices."""
        # This is a stub implementation
        # In production, you would use platform-specific APIs
        stub_devices = [
            MediaDeviceInfo(
                device_id="default_camera",
                device_name="Default Camera",
                device_type="video",
                is_default=True,
                is_available=True,
                capabilities=MediaDeviceCapabilities(
                    sample_rates=[30, 60],  # FPS
                    formats=["H264", "VP8", "VP9"],
                    channels=[1]  # Single video stream
                )
            ),
            MediaDeviceInfo(
                device_id="built_in_camera",
                device_name="Built-in Camera",
                device_type="video",
                is_default=False,
                is_available=True,
                capabilities=MediaDeviceCapabilities(
                    sample_rates=[30],
                    formats=["H264"],
                    channels=[1]
                )
            )
        ]
        
        if self.platform == "windows":
            stub_devices.append(
                MediaDeviceInfo(
                    device_id="usb_camera",
                    device_name="USB Camera",
                    device_type="video",
                    is_default=False,
                    is_available=True,
                    capabilities=MediaDeviceCapabilities(
                        sample_rates=[15, 30, 60],
                        formats=["H264", "MJPEG"],
                        channels=[1]
                    )
                )
            )
        
        return stub_devices
    
    async def _get_stub_devices(self) -> Dict[str, List[MediaDeviceInfo]]:
        """Get stub devices when enumeration fails."""
        logger.warning("Using stub device list")
        
        return {
            "audio_devices": [
                MediaDeviceInfo(
                    device_id="stub_microphone",
                    device_name="Default Audio Input",
                    device_type="audio",
                    is_default=True,
                    is_available=True
                )
            ],
            "video_devices": [
                MediaDeviceInfo(
                    device_id="stub_camera",
                    device_name="Default Video Input",
                    device_type="video",
                    is_default=True,
                    is_available=True
                )
            ],
            "total_devices": 2
        }
    
    async def test_device_access(self, device_id: str) -> bool:
        """
        Test if a device is accessible.
        
        Args:
            device_id: Device ID to test
            
        Returns:
            True if device is accessible
        """
        # Stub implementation - always return True
        logger.info(f"Testing access to device: {device_id}")
        return True
    
    async def get_available_devices(self, device_type: str = None) -> List[Dict[str, Any]]:
        """
        Get available media devices in the format expected by the router.
        
        Args:
            device_type: Optional filter for device type
            
        Returns:
            List of device dictionaries
        """
        try:
            devices_data = await self.get_media_devices()
            
            all_devices = []
            
            # Convert audio devices
            if device_type is None or device_type == "audio":
                for device in devices_data["audio_devices"]:
                    all_devices.append({
                        "id": device.device_id,
                        "label": device.device_name,
                        "device_type": device.device_type,
                        "capabilities": device.capabilities.dict() if device.capabilities else {},
                        "is_default": device.is_default
                    })
            
            # Convert video devices
            if device_type is None or device_type == "video":
                for device in devices_data["video_devices"]:
                    all_devices.append({
                        "id": device.device_id,
                        "label": device.device_name,
                        "device_type": device.device_type,
                        "capabilities": device.capabilities.dict() if device.capabilities else {},
                        "is_default": device.is_default
                    })
            
            return all_devices
            
        except Exception as e:
            logger.error(f"Error getting available devices: {str(e)}")
            return []
    
    async def refresh_devices(self) -> List[Dict[str, Any]]:
        """
        Refresh and get available devices.
        
        Returns:
            List of device dictionaries
        """
        # For now, this does the same as get_available_devices
        # In a real implementation, this would clear cache and re-enumerate
        return await self.get_available_devices()
    
    async def get_device_details(self, device_id: str) -> Dict[str, Any]:
        """
        Get details for a specific device.
        
        Args:
            device_id: Device ID
            
        Returns:
            Device details dictionary or None if not found
        """
        devices = await self.get_available_devices()
        
        for device in devices:
            if device["id"] == device_id:
                return device
        
        return None

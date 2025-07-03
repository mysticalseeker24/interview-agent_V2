"""Media device schema definitions."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class MediaDeviceCapabilities(BaseModel):
    """Media device capabilities schema."""
    sample_rates: List[int] = []
    formats: List[str] = []
    channels: List[int] = []


class MediaDeviceInfo(BaseModel):
    """Media device information schema."""
    device_id: str
    device_name: str
    device_type: str  # audio, video
    is_default: bool = False
    is_available: bool = True
    capabilities: Optional[MediaDeviceCapabilities] = None


class MediaDeviceList(BaseModel):
    """Media device list response schema."""
    audio_devices: List[MediaDeviceInfo]
    video_devices: List[MediaDeviceInfo]
    total_devices: int


class MediaDeviceRequest(BaseModel):
    """Media device detection request."""
    include_capabilities: bool = False
    device_types: List[str] = ["audio", "video"]


class MediaDeviceRead(BaseModel):
    """Media device read schema."""
    id: int
    user_id: int
    device_id: str
    device_name: str
    device_type: str
    capabilities: Optional[Dict[str, Any]] = None
    is_default: bool = False
    is_available: bool = True
    detected_at: datetime
    last_used_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class MediaDeviceResponse(BaseModel):
    """Media device response schema."""
    id: str
    label: str
    device_type: str
    capabilities: Dict[str, Any]
    is_default: bool = False


class MediaDeviceListResponse(BaseModel):
    """Media device list response schema."""
    devices: List[MediaDeviceResponse]
    total: int

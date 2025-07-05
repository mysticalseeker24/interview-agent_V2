"""
Media device endpoints for the Transcription Service.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from ..core.database import get_db
from ..core.security import get_current_user
from ..schemas.media import MediaDeviceResponse, MediaDeviceListResponse
from ..schemas.user import UserRead
from ..services.media_device_service import MediaDeviceService
from ..services.database_service import DatabaseService

router = APIRouter(
    prefix="/media",
    tags=["media"],
    responses={404: {"description": "Not found"}},
)

logger = logging.getLogger(__name__)


@router.post("/devices", response_model=MediaDeviceListResponse)
async def get_media_devices(
    device_type: str = None,  # "audio" or "video"
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """
    Get available media devices for the current user.
    
    Returns audio and video devices with their capabilities.
    Results are cached and updated periodically.
    """
    try:
        media_service = MediaDeviceService()
        database_service = DatabaseService()
        
        # Get devices from the service
        devices = await media_service.get_available_devices(device_type=device_type)
        
        # Store/update device info in database for analytics
        await database_service.update_user_devices(
            user_id=current_user.id,
            devices=devices,
            db=db
        )
        
        logger.info(f"Retrieved {len(devices)} media devices for user {current_user.id}")
        
        return MediaDeviceListResponse(
            devices=[
                MediaDeviceResponse(
                    id=device["id"],
                    label=device["label"],
                    device_type=device["device_type"],
                    capabilities=device["capabilities"],
                    is_default=device["is_default"]
                )
                for device in devices
            ],
            total=len(devices)
        )
        
    except Exception as e:
        logger.error(f"Error fetching media devices: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch media devices: {str(e)}"
        )


@router.post("/devices/refresh", response_model=MediaDeviceListResponse)
async def refresh_media_devices(
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """
    Force refresh of available media devices.
    
    Clears cache and re-enumerates devices.
    """
    try:
        media_service = MediaDeviceService()
        database_service = DatabaseService()
        
        # Force refresh devices
        devices = await media_service.refresh_devices()
        
        # Update database
        await database_service.update_user_devices(
            user_id=current_user.id,
            devices=devices,
            db=db
        )
        
        logger.info(f"Refreshed {len(devices)} media devices for user {current_user.id}")
        
        return MediaDeviceListResponse(
            devices=[
                MediaDeviceResponse(
                    id=device["id"],
                    label=device["label"],
                    device_type=device["device_type"],
                    capabilities=device["capabilities"],
                    is_default=device["is_default"]
                )
                for device in devices
            ],
            total=len(devices)
        )
        
    except Exception as e:
        logger.error(f"Error refreshing media devices: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh media devices: {str(e)}"
        )


@router.get("/devices/{device_id}", response_model=MediaDeviceResponse)
async def get_media_device(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """
    Get details for a specific media device.
    """
    try:
        media_service = MediaDeviceService()
        
        device = await media_service.get_device_details(device_id=device_id)
        
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media device not found"
            )
        
        return MediaDeviceResponse(
            id=device["id"],
            label=device["label"],
            device_type=device["device_type"],
            capabilities=device["capabilities"],
            is_default=device["is_default"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching device {device_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch device details: {str(e)}"
        )

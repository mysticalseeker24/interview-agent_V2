"""
Users router for TalentSync Auth Gateway Service.

Provides high-performance user management endpoints for profile
operations with proper authentication and authorization.
"""
import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, status, Depends

from app.core.settings import settings
from app.schemas.auth import (
    UserResponse,
    UserProfileUpdateRequest,
    ErrorResponse,
)
from app.dependencies import get_current_user, get_current_admin_user, get_supabase_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    description="Get the profile of the currently authenticated user",
    responses={
        200: {"description": "User profile retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Invalid token"},
        403: {"model": ErrorResponse, "description": "Account inactive"},
        404: {"model": ErrorResponse, "description": "User profile not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_my_profile(
    current_user: UserResponse = Depends(get_current_user),
    supabase_service = Depends(get_supabase_service)
) -> UserResponse:
    """
    Get current user's profile information.
    
    Args:
        current_user: Current authenticated user from dependency
        supabase_service: Supabase service instance
        
    Returns:
        UserResponse: Current user's profile information
        
    Raises:
        HTTPException: If profile retrieval fails
    """
    try:
        # Get fresh user data from database
        success, user_data, error_message = await supabase_service.get_user_profile(
            current_user.id
        )
        
        if not success or not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found",
            )
        
        # Create user response
        user = UserResponse(**user_data)
        logger.debug(f"Retrieved profile for user: {user.email}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.put(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update current user profile",
    description="Update the profile of the currently authenticated user",
    responses={
        200: {"description": "User profile updated successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request data"},
        401: {"model": ErrorResponse, "description": "Invalid token"},
        403: {"model": ErrorResponse, "description": "Account inactive"},
        404: {"model": ErrorResponse, "description": "User profile not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def update_my_profile(
    request: UserProfileUpdateRequest,
    current_user: UserResponse = Depends(get_current_user),
    supabase_service = Depends(get_supabase_service)
) -> UserResponse:
    """
    Update current user's profile information.
    
    Args:
        request: Profile update data
        current_user: Current authenticated user from dependency
        supabase_service: Supabase service instance
        
    Returns:
        UserResponse: Updated user profile information
        
    Raises:
        HTTPException: If profile update fails
    """
    try:
        # Prepare updates (only include non-None values)
        updates = {}
        if request.full_name is not None:
            updates["full_name"] = request.full_name
        if request.is_active is not None:
            updates["is_active"] = request.is_active
        
        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid updates provided",
            )
        
        # Update user profile
        success, user_data, error_message = await supabase_service.update_user_profile(
            current_user.id, updates
        )
        
        if not success or not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found or update failed",
            )
        
        # Create user response
        user = UserResponse(**user_data)
        logger.info(f"Updated profile for user: {user.email}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user profile by ID",
    description="Get user profile by ID (admin only)",
    responses={
        200: {"description": "User profile retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Invalid token"},
        403: {"model": ErrorResponse, "description": "Admin privileges required"},
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_user_by_id(
    user_id: str,
    current_admin: UserResponse = Depends(get_current_admin_user),
    supabase_service = Depends(get_supabase_service)
) -> UserResponse:
    """
    Get user profile by ID (admin only).
    
    Args:
        user_id: User ID to retrieve
        current_admin: Current authenticated admin user from dependency
        supabase_service: Supabase service instance
        
    Returns:
        UserResponse: User profile information
        
    Raises:
        HTTPException: If user retrieval fails
    """
    try:
        # Get user profile
        success, user_data, error_message = await supabase_service.get_user_profile(
            user_id
        )
        
        if not success or not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        # Create user response
        user = UserResponse(**user_data)
        logger.info(f"Admin {current_admin.email} retrieved profile for user: {user.email}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting user by ID: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update user profile by ID",
    description="Update user profile by ID (admin only)",
    responses={
        200: {"description": "User profile updated successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request data"},
        401: {"model": ErrorResponse, "description": "Invalid token"},
        403: {"model": ErrorResponse, "description": "Admin privileges required"},
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def update_user_by_id(
    user_id: str,
    request: UserProfileUpdateRequest,
    current_admin: UserResponse = Depends(get_current_admin_user),
    supabase_service = Depends(get_supabase_service)
) -> UserResponse:
    """
    Update user profile by ID (admin only).
    
    Args:
        user_id: User ID to update
        request: Profile update data
        current_admin: Current authenticated admin user from dependency
        supabase_service: Supabase service instance
        
    Returns:
        UserResponse: Updated user profile information
        
    Raises:
        HTTPException: If profile update fails
    """
    try:
        # Prepare updates (only include non-None values)
        updates = {}
        if request.full_name is not None:
            updates["full_name"] = request.full_name
        if request.is_active is not None:
            updates["is_active"] = request.is_active
        
        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid updates provided",
            )
        
        # Update user profile
        success, user_data, error_message = await supabase_service.update_user_profile(
            user_id, updates
        )
        
        if not success or not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found or update failed",
            )
        
        # Create user response
        user = UserResponse(**user_data)
        logger.info(f"Admin {current_admin.email} updated profile for user: {user.email}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating user by ID: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) 
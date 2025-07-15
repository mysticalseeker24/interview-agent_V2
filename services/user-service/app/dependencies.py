"""
Dependencies for TalentSync Auth Gateway Service.

Provides FastAPI dependencies for authentication, authorization,
and other common functionality with high-performance patterns.
"""
import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.settings import settings
from app.services.supabase_service import supabase_service
from app.schemas.auth import UserResponse

logger = logging.getLogger(__name__)

# Security scheme for Bearer token authentication
security = HTTPBearer(auto_error=False)


def get_supabase_service():
    """
    Get Supabase service instance.
    
    This dependency function allows for easy mocking in tests
    by using FastAPI's dependency override system.
    
    Returns:
        SupabaseService: Supabase service instance
    """
    return supabase_service


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> UserResponse:
    """
    Get current authenticated user from JWT token.
    
    Validates the Bearer token using Supabase JWKs and returns
    the authenticated user information.
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        UserResponse: Authenticated user information
        
    Raises:
        HTTPException: If authentication fails (401 Unauthorized)
    """
    if not credentials:
        logger.warning("No authentication credentials provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    # Validate token with Supabase
    success, user_data, error_message = await supabase_service.validate_token(token)
    
    if not success or not user_data:
        logger.warning(f"Token validation failed: {error_message}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user_data.get("is_active", True):
        logger.warning(f"Inactive user attempted access: {user_data.get('email')}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    
    # Convert to UserResponse model
    try:
        user = UserResponse(**user_data)
        logger.debug(f"Authenticated user: {user.email}")
        return user
    except Exception as e:
        logger.error(f"Failed to create UserResponse: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


async def get_current_admin_user(
    current_user: UserResponse = Depends(get_current_user)
) -> UserResponse:
    """
    Get current authenticated admin user.
    
    Validates that the authenticated user has admin privileges.
    
    Args:
        current_user: Current authenticated user from get_current_user
        
    Returns:
        UserResponse: Authenticated admin user information
        
    Raises:
        HTTPException: If user is not an admin (403 Forbidden)
    """
    if not current_user.is_admin:
        logger.warning(f"Non-admin user attempted admin access: {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    
    return current_user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[UserResponse]:
    """
    Get current user if authenticated, otherwise return None.
    
    This dependency is useful for endpoints that can work with or without
    authentication (e.g., public endpoints with optional user features).
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        Optional[UserResponse]: Authenticated user or None
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None 
"""Security utilities for interview service."""
import logging
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
from app.core.config import get_settings

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> dict:
    """
    Get current user from authentication token.
    
    Args:
        credentials: Bearer token credentials
        
    Returns:
        User information
        
    Raises:
        HTTPException: If authentication fails
    """
    # For testing purposes, return a mock user if no credentials are provided
    if credentials is None:
        logger.warning("No authentication provided. Using mock user for development.")
        return {
            "id": "mock-user-id",
            "email": "test@example.com",
            "username": "testuser",
            "is_active": True,
            "is_superuser": True,
            "first_name": "Test",
            "last_name": "User"
        }
    
    try:
        settings = get_settings()
        # In production, this would validate the JWT token
        # For now, we'll make a call to the user service
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.USER_SERVICE_URL}/users/me",
                headers={"Authorization": f"Bearer {credentials.credentials}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return response.json()
            
    except httpx.RequestError as e:
        logger.error(f"Error validating token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable"
        )
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

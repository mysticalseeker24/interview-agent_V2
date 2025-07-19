"""Authentication dependencies for TalentSync Interview Service."""
import asyncio
import json
import logging
from typing import Optional
from uuid import UUID

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from app.core.settings import settings

logger = logging.getLogger(__name__)

# HTTP Bearer token security
security = HTTPBearer(auto_error=False)


class User(BaseModel):
    """User model for authenticated users."""
    id: UUID
    email: str
    role: str = "user"
    is_active: bool = True


class SupabaseAuth:
    """Supabase authentication handler with caching for performance."""
    
    def __init__(self):
        self.supabase_url = str(settings.SUPABASE_URL)
        self.jwks_url = f"{self.supabase_url}/rest/v1/auth/jwks"
        self._jwks_cache = {}
        self._cache_ttl = 3600  # 1 hour cache
        self._last_cache_update = 0
    
    async def get_jwks(self) -> dict:
        """Get JWKS from Supabase with caching."""
        current_time = asyncio.get_event_loop().time()
        
        # Return cached JWKS if still valid
        if (current_time - self._last_cache_update) < self._cache_ttl:
            return self._jwks_cache
        
        try:
            async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT) as client:
                response = await client.get(self.jwks_url)
                response.raise_for_status()
                self._jwks_cache = response.json()
                self._last_cache_update = current_time
                logger.info("Updated JWKS cache from Supabase")
                return self._jwks_cache
        except Exception as e:
            logger.error(f"Failed to fetch JWKS: {e}")
            # Return cached version if available, otherwise raise
            if self._jwks_cache:
                return self._jwks_cache
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service unavailable"
            )
    
    async def verify_token(self, token: str) -> dict:
        """Verify JWT token with Supabase."""
        try:
            # For production, implement proper JWT verification
            # For now, we'll use a simple token validation approach
            # In a real implementation, you would:
            # 1. Decode the JWT header to get the key ID
            # 2. Fetch the corresponding public key from JWKS
            # 3. Verify the token signature
            # 4. Validate claims (exp, iss, aud, etc.)
            
            # Simple token validation for development
            if not token or len(token) < 10:
                raise ValueError("Invalid token format")
            
            # Mock user data for development
            # In production, decode the actual JWT and extract user info
            user_data = {
                "id": "mock-user-id",
                "email": "user@example.com",
                "role": "user",
                "is_active": True
            }
            
            return user_data
            
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )


# Global auth instance
auth_handler = SupabaseAuth()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> User:
    """
    Get current authenticated user from JWT token.
    
    Args:
        credentials: Bearer token credentials
        
    Returns:
        User object with id, email, and role
        
    Raises:
        HTTPException: If authentication fails
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Verify token with timeout
        user_data = await asyncio.wait_for(
            auth_handler.verify_token(credentials.credentials),
            timeout=settings.REQUEST_TIMEOUT
        )
        
        return User(**user_data)
        
    except asyncio.TimeoutError:
        logger.error("Authentication timeout")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service timeout"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Active user object
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current admin user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Admin user object
        
    Raises:
        HTTPException: If user is not admin
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user 
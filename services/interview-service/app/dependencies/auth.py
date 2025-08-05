"""Mock authentication dependencies for TalentSync Interview Service (Development Mode)."""
import logging
from typing import Optional
from uuid import UUID, uuid4
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class User(BaseModel):
    """Mock user model for development/testing."""
    id: UUID
    email: str = "dev@talentsync.local"
    role: str = "user"
    is_active: bool = True


# Global mock user for development
MOCK_USER_ID = UUID('00000000-0000-0000-0000-000000000001')


async def get_current_user() -> User:
    """
    Get mock user for development/testing (no authentication required).
        
    Returns:
        Mock user object with default development ID
    """
    return User(
        id=MOCK_USER_ID,
        email="dev@talentsync.local",
        role="user",
        is_active=True
        )


async def get_current_active_user(
    current_user: User = None
) -> User:
    """
    Get current active user (always returns mock user in dev mode).
    
    Args:
        current_user: Current user (mock)
        
    Returns:
        Active user object
    """
    return current_user


async def get_current_admin_user(
    current_user: User = None
) -> User:
    """
    Get current admin user (always returns mock user in dev mode).
    
    Args:
        current_user: Current user (mock)
        
    Returns:
        Admin user object (mock)
    """
    return current_user 
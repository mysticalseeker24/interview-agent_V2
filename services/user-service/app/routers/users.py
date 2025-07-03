"""User management router for User Service."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.user import UserRead, UserUpdate
from app.services.user_service import UserService
from app.services.auth_service import AuthService

router = APIRouter()


@router.get("/me", response_model=UserRead)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's profile information with roles.
    
    Args:
        current_user: Authenticated user
        db: Database session
        
    Returns:
        UserRead: Current user's profile with roles
    """
    auth_service = AuthService(db)
    user_with_roles = await auth_service.get_user_with_roles(current_user.id)
    return UserRead.from_orm(user_with_roles)


@router.put("/me", response_model=UserRead)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user's profile information.
    Re-validates updated fields.
    
    Args:
        user_update: Updated user data
        current_user: Authenticated user
        db: Database session
        
    Returns:
        UserRead: Updated user profile with roles
    """
    user_service = UserService(db)
    auth_service = AuthService(db)
    
    # Update user
    updated_user = await user_service.update_user(current_user.id, user_update)
    
    # Return user with roles
    user_with_roles = await auth_service.get_user_with_roles(updated_user.id)
    return UserRead.from_orm(user_with_roles)


@router.get("/{user_id}", response_model=UserRead)
async def get_user_by_id(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get user by ID (admin only or own profile).
    
    Args:
        user_id: User ID to retrieve
        db: Database session
        current_user: Authenticated user
        
    Returns:
        UserRead: User profile with roles
        
    Raises:
        HTTPException: If user not found or unauthorized
    """
    # Check if user is requesting their own profile or is admin
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this user's profile"
        )
    
    auth_service = AuthService(db)
    user_with_roles = await auth_service.get_user_with_roles(user_id)
    if not user_with_roles:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserRead.from_orm(user_with_roles)

"""User management router for User Service."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's profile information.
    
    Args:
        current_user: Authenticated user
        
    Returns:
        UserResponse: Current user's profile
    """
    return UserResponse.from_orm(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user's profile information.
    
    Args:
        user_update: Updated user data
        current_user: Authenticated user
        db: Database session
        
    Returns:
        UserResponse: Updated user profile
    """
    user_service = UserService(db)
    updated_user = await user_service.update_user(current_user.id, user_update)
    return UserResponse.from_orm(updated_user)


@router.get("/{user_id}", response_model=UserResponse)
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
        UserResponse: User profile
        
    Raises:
        HTTPException: If user not found or unauthorized
    """
    user_service = UserService(db)
    
    # Check if user is requesting their own profile or is admin
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this user's profile"
        )
    
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.from_orm(user)

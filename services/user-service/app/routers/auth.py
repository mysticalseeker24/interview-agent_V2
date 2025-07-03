"""Authentication router for User Service."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.auth import Token, UserCreate, UserLogin, UserRead
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/signup", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def signup(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user account with candidate role.
    
    Args:
        user_data: User registration data
        db: Database session
        
    Returns:
        UserRead: Created user information with roles
        
    Raises:
        HTTPException: If email already exists
    """
    auth_service = AuthService(db)
    return await auth_service.signup(user_data)


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user with OAuth2 form and return access token.
    
    Args:
        form_data: OAuth2 login credentials (username=email, password)
        db: Database session
        
    Returns:
        Token: JWT access token with 15-minute expiry
        
    Raises:
        HTTPException: If credentials are invalid
    """
    auth_service = AuthService(db)
    return await auth_service.login(form_data)


@router.post("/login-direct", response_model=Token)
async def login_direct(
    user_login: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user with direct email/password and return access token.
    
    Args:
        user_login: Direct login credentials
        db: Database session
        
    Returns:
        Token: JWT access token with 15-minute expiry
        
    Raises:
        HTTPException: If credentials are invalid
    """
    auth_service = AuthService(db)
    return await auth_service.login_direct(user_login)


@router.get("/profile", response_model=UserRead)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's profile information with roles.
    Protected endpoint requiring valid JWT token.
    
    Args:
        current_user: Authenticated user from JWT token
        db: Database session
        
    Returns:
        UserRead: Current user's profile with roles
    """
    auth_service = AuthService(db)
    user_with_roles = await auth_service.get_user_with_roles(current_user.id)
    return UserRead.from_orm(user_with_roles)

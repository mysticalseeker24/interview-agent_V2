"""
Authentication router for TalentSync Auth Gateway Service.

Provides high-performance authentication endpoints for user registration,
login, and logout with proper error handling and validation.
"""
import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials

from app.core.settings import settings
from app.schemas.auth import (
    UserSignupRequest,
    UserLoginRequest,
    AuthResponse,
    UserResponse,
    ErrorResponse,
)
from app.services.supabase_service import supabase_service
from app.dependencies import security

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email, password, and full name",
    responses={
        201: {"description": "User registered successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request data"},
        409: {"model": ErrorResponse, "description": "User already exists"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def signup_user(request: UserSignupRequest) -> AuthResponse:
    """
    Register a new user account.
    
    Creates a new user in Supabase Auth and initializes their profile
    with the provided information.
    
    Args:
        request: User registration data
        
    Returns:
        AuthResponse: Authentication token and user information
        
    Raises:
        HTTPException: If registration fails
    """
    try:
        # Register user with Supabase
        success, user_data, error_message = await supabase_service.signup_user(
            email=request.email,
            password=request.password,
            full_name=request.full_name,
        )
        
        if not success:
            if "already registered" in error_message.lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User with this email already exists",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_message,
                )
        
        # Create user response
        user = UserResponse(**user_data)
        
        # For signup, we need to login the user to get a token
        login_success, auth_data, login_error = await supabase_service.login_user(
            email=request.email,
            password=request.password,
        )
        
        if not login_success:
            logger.error(f"Failed to login user after signup: {login_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Account created but login failed",
            )
        
        # Return authentication response
        response = AuthResponse(
            access_token=auth_data["access_token"],
            token_type=auth_data["token_type"],
            expires_in=auth_data["expires_in"],
            user=user,
        )
        
        logger.info(f"User registered successfully: {request.email}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during user signup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during registration",
        )


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user",
    description="Login with email and password to get authentication token",
    responses={
        200: {"description": "Login successful"},
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
        403: {"model": ErrorResponse, "description": "Account inactive"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def login_user(request: UserLoginRequest) -> AuthResponse:
    """
    Authenticate user with email and password.
    
    Validates user credentials and returns a JWT token for API access.
    
    Args:
        request: User login credentials
        
    Returns:
        AuthResponse: Authentication token and user information
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Authenticate with Supabase
        success, auth_data, error_message = await supabase_service.login_user(
            email=request.email,
            password=request.password,
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user is active
        if not auth_data["user"].get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive",
            )
        
        # Create response
        user = UserResponse(**auth_data["user"])
        response = AuthResponse(
            access_token=auth_data["access_token"],
            token_type=auth_data["token_type"],
            expires_in=auth_data["expires_in"],
            user=user,
        )
        
        logger.info(f"User logged in successfully: {request.email}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during user login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during authentication",
        )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Logout user",
    description="Invalidate the current authentication token",
    responses={
        200: {"description": "Logout successful"},
        401: {"model": ErrorResponse, "description": "Invalid token"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def logout_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, str]:
    """
    Logout user by invalidating the current token.
    
    Args:
        credentials: Current authentication credentials
        
    Returns:
        Dict[str, str]: Success message
        
    Raises:
        HTTPException: If logout fails
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Logout with Supabase
        success, error_message = await supabase_service.logout_user(
            credentials.credentials
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_message,
            )
        
        logger.info("User logged out successfully")
        return {"message": "Logout successful"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during logout: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during logout",
        )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user",
    description="Get information about the currently authenticated user",
    responses={
        200: {"description": "User information retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Invalid token"},
        403: {"model": ErrorResponse, "description": "Account inactive"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_current_user_info(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserResponse:
    """
    Get current authenticated user information.
    
    Args:
        credentials: Current authentication credentials
        
    Returns:
        UserResponse: Current user information
        
    Raises:
        HTTPException: If authentication fails
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Validate token and get user info
        success, user_data, error_message = await supabase_service.validate_token(
            credentials.credentials
        )
        
        if not success or not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user is active
        if not user_data.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive",
            )
        
        # Create user response
        user = UserResponse(**user_data)
        logger.debug(f"Retrieved user info: {user.email}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting user info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) 
"""
Authentication schemas for TalentSync Auth Gateway Service.

Defines Pydantic models for authentication requests and responses
with proper validation and type safety.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, validator


class UserSignupRequest(BaseModel):
    """
    User registration request schema.
    
    Validates user input for account creation with proper email and password requirements.
    """
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password (min 8 characters)")
    full_name: str = Field(..., min_length=1, max_length=100, description="User full name")
    
    @validator("password")
    def validate_password_strength(cls, v: str) -> str:
        """
        Validate password strength requirements.
        
        Args:
            v: Password string
            
        Returns:
            str: Validated password
            
        Raises:
            ValueError: If password doesn't meet strength requirements
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        # Check for at least one uppercase letter
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        
        # Check for at least one lowercase letter
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        
        # Check for at least one digit
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        
        return v


class UserLoginRequest(BaseModel):
    """
    User login request schema.
    
    Validates login credentials with proper email format.
    """
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class AuthResponse(BaseModel):
    """
    Authentication response schema.
    
    Returns JWT token and user information after successful authentication.
    """
    
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiry time in seconds")
    user: "UserResponse" = Field(..., description="User information")


class UserResponse(BaseModel):
    """
    User response schema.
    
    Returns user information without sensitive data like passwords.
    """
    
    id: str = Field(..., description="User unique identifier")
    email: EmailStr = Field(..., description="User email address")
    full_name: str = Field(..., description="User full name")
    is_active: bool = Field(default=True, description="User account status")
    is_admin: bool = Field(default=False, description="User admin status")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserProfileUpdateRequest(BaseModel):
    """
    User profile update request schema.
    
    Allows users to update their profile information.
    """
    
    full_name: Optional[str] = Field(None, min_length=1, max_length=100, description="User full name")
    is_active: Optional[bool] = Field(None, description="User account status")
    
    @validator("full_name")
    def validate_full_name(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate full name if provided.
        
        Args:
            v: Full name string
            
        Returns:
            Optional[str]: Validated full name
        """
        if v is not None and len(v.strip()) == 0:
            raise ValueError("Full name cannot be empty")
        return v


class ErrorResponse(BaseModel):
    """
    Error response schema.
    
    Standardized error responses for API endpoints.
    """
    
    error: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")
    details: Optional[dict] = Field(None, description="Additional error details")


# Update forward references
AuthResponse.model_rebuild()
UserResponse.model_rebuild() 
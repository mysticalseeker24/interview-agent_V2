"""Authentication schema definitions."""
from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    """JWT token response schema."""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token payload data schema."""
    email: str


class UserCreate(BaseModel):
    """User creation schema."""
    email: EmailStr
    password: str
    first_name: str
    last_name: str


class UserResponse(BaseModel):
    """User response schema."""
    id: int
    email: str
    first_name: str
    last_name: str
    is_active: bool
    is_admin: bool
    
    class Config:
        from_attributes = True

"""Authentication schema definitions."""
from typing import List, Optional
from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    """JWT token response schema."""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token payload data schema."""
    email: str
    user_id: Optional[int] = None


class UserCreate(BaseModel):
    """User creation schema."""
    email: EmailStr
    password: str
    first_name: str
    last_name: str


class UserLogin(BaseModel):
    """User login schema."""
    email: EmailStr
    password: str


class RoleRead(BaseModel):
    """Role read schema."""
    id: int
    name: str
    description: Optional[str] = None
    
    class Config:
        from_attributes = True


class UserRead(BaseModel):
    """User response schema."""
    id: int
    email: str
    first_name: str
    last_name: str
    is_active: bool
    is_admin: bool
    roles: List[RoleRead] = []
    
    class Config:
        from_attributes = True

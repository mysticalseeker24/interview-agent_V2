"""User schema definitions."""
from typing import List, Optional
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    first_name: str
    last_name: str


class UserCreate(UserBase):
    """User creation schema."""
    password: str


class UserUpdate(BaseModel):
    """User update schema."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None


class RoleRead(BaseModel):
    """Role read schema."""
    id: int
    name: str
    description: Optional[str] = None
    
    class Config:
        from_attributes = True


class UserRead(UserBase):
    """User response schema."""
    id: int
    is_active: bool
    is_admin: bool
    roles: List[RoleRead] = []
    
    class Config:
        from_attributes = True

"""Authentication service for business logic."""
from datetime import timedelta
from typing import Optional
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models import User, Role, UserRole
from app.schemas.auth import Token, UserCreate, UserLogin, UserRead

settings = get_settings()


class AuthService:
    """Service class for authentication operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def signup(self, user_data: UserCreate) -> UserRead:
        """
        Register a new user and assign candidate role.
        
        Args:
            user_data: User registration data
            
        Returns:
            UserRead: Created user information
            
        Raises:
            HTTPException: If email already exists
        """
        # Check if user already exists
        existing_user = await self.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password
        hashed_password = get_password_hash(user_data.password)
        
        # Create new user
        user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
        )
        
        self.db.add(user)
        await self.db.flush()  # Get user ID
        
        # Assign "candidate" role
        candidate_role = await self.get_role_by_name("candidate")
        if not candidate_role:
            # Create candidate role if it doesn't exist
            candidate_role = Role(name="candidate", description="Default candidate role")
            self.db.add(candidate_role)
            await self.db.flush()
        
        # Create user-role association
        user_role = UserRole(user_id=user.id, role_id=candidate_role.id)
        self.db.add(user_role)
        
        await self.db.commit()
        await self.db.refresh(user)
        
        # Load user with roles for response
        user_with_roles = await self.get_user_with_roles(user.id)
        return UserRead.from_orm(user_with_roles)
    
    async def login(self, form_data: OAuth2PasswordRequestForm) -> Token:
        """
        Authenticate user and return JWT token.
        
        Args:
            form_data: Login credentials
            
        Returns:
            Token: JWT access token
            
        Raises:
            HTTPException: If credentials are invalid
        """
        # Get user by email
        user = await self.get_user_by_email(form_data.username)
        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is disabled"
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id}, 
            expires_delta=access_token_expires
        )
        
        return Token(access_token=access_token, token_type="bearer")
    
    async def login_direct(self, user_login: UserLogin) -> Token:
        """
        Authenticate user with direct email/password and return JWT token.
        
        Args:
            user_login: Login credentials
            
        Returns:
            Token: JWT access token
        """
        # Get user by email
        user = await self.get_user_by_email(user_login.email)
        if not user or not verify_password(user_login.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is disabled"
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id}, 
            expires_delta=access_token_expires
        )
        
        return Token(access_token=access_token, token_type="bearer")
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email.
        
        Args:
            email: User email
            
        Returns:
            User or None if not found
        """
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    async def get_user_with_roles(self, user_id: int) -> Optional[User]:
        """
        Get user with roles loaded.
        
        Args:
            user_id: User ID
            
        Returns:
            User with roles or None if not found
        """
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.roles).selectinload(UserRole.role))
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_role_by_name(self, name: str) -> Optional[Role]:
        """
        Get role by name.
        
        Args:
            name: Role name
            
        Returns:
            Role or None if not found
        """
        result = await self.db.execute(select(Role).where(Role.name == name))
        return result.scalar_one_or_none()

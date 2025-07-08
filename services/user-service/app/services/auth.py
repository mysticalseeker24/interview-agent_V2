from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token
from app.schemas.user import UserCreate


class AuthService:

    @staticmethod
    async def signup(user_in: UserCreate, db: AsyncSession):
        # Check if user already exists
        result = await db.execute(select(User).where(User.email == user_in.email))
        if result.scalars().first():
            raise HTTPException(400, "Email already registered")
        
        # Create new user
        hashed = hash_password(user_in.password)
        new_user = User(
            email=user_in.email, 
            hashed_password=hashed, 
            full_name=user_in.full_name
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user

    @staticmethod
    async def login(email: str, password: str, db: AsyncSession):
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalars().first()
        
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(401, "Incorrect email or password")
        
        if not user.is_active:
            raise HTTPException(401, "User account is inactive")
            
        token = create_access_token(sub=str(user.id))
        return {"access_token": token, "token_type": "bearer"}

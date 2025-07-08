from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user import UserCreate, UserRead, Token
from app.services.auth import AuthService
from app.core.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=UserRead)
async def signup(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    return await AuthService.signup(user_in, db)


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """Login and get access token."""
    return await AuthService.login(form_data.username, form_data.password, db)

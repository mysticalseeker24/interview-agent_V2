from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from .config import settings


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.database_echo,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables."""
    async with engine.begin() as conn:
        # Import all models to ensure they are registered
        from ..models import Transcription, TTSCache, MediaChunk, ProcessingTask
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose() 
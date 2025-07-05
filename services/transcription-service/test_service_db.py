#!/usr/bin/env python3
"""
Test the exact database connection used by the service.
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

async def test_service_database():
    """Test the database connection as used by the service."""
    
    database_url = "postgresql+asyncpg://talentsync:secret@localhost:5432/talentsync"
    
    print(f"Testing connection: {database_url}")
    
    try:
        engine = create_async_engine(database_url)
        
        async with engine.begin() as conn:
            result = await conn.execute("SELECT 1")
            print("✓ Successfully connected to database!")
            print(f"✓ Test query result: {result.scalar()}")
        
        await engine.dispose()
        return True
        
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_service_database())
    if not success:
        print("\nTrying to create database and user...")
        # If we can't connect, let's try to create the setup
        print("Please run the setup manually or check PostgreSQL installation.")

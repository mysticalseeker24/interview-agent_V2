#!/usr/bin/env python3
"""
Try Windows authentication for PostgreSQL.
"""
import asyncio
import asyncpg
import os
import getpass

async def test_windows_auth():
    """Test PostgreSQL connection with Windows authentication."""
    
    current_user = getpass.getuser()
    print(f"Current Windows user: {current_user}")
    
    # Try different authentication methods
    auth_methods = [
        # Windows user without password
        {"host": "localhost", "port": 5432, "user": current_user, "database": "postgres"},
        # Try with different ports for different PostgreSQL versions
        {"host": "localhost", "port": 5433, "user": current_user, "database": "postgres"},
        {"host": "localhost", "port": 5434, "user": current_user, "database": "postgres"},
        # Try postgres user with no password (trust auth)
        {"host": "localhost", "port": 5432, "user": "postgres", "database": "postgres"},
        {"host": "localhost", "port": 5433, "user": "postgres", "database": "postgres"},
        {"host": "localhost", "port": 5434, "user": "postgres", "database": "postgres"},
    ]
    
    for i, config in enumerate(auth_methods, 1):
        try:
            print(f"Trying method {i}: {config}")
            conn = await asyncpg.connect(**config)
            
            # Test the connection
            result = await conn.fetchval("SELECT current_user, version()")
            print(f"  ✓ Connected! Current user: {await conn.fetchval('SELECT current_user')}")
            print(f"  ✓ PostgreSQL version: {await conn.fetchval('SELECT version()')}")
            
            await conn.close()
            return config
            
        except Exception as e:
            print(f"  ✗ Failed: {e}")
    
    return None

if __name__ == "__main__":
    working_config = asyncio.run(test_windows_auth())
    if working_config:
        print(f"\n✓ Working configuration found: {working_config}")
    else:
        print("\n✗ No working authentication method found.")

#!/usr/bin/env python3
"""
Setup script to create the TalentSync database and user.
"""
import asyncio
import asyncpg
from sqlalchemy import create_engine, text
import sys

async def create_database_and_user():
    """Create the database and user if they don't exist."""
    
    # First, connect to the default postgres database to create our database and user
    try:
        # Try different connection methods for postgres
        conn = None
        
        # Try connecting without password first
        try:
            conn = await asyncpg.connect(
                host='localhost',
                port=5432,
                user='postgres',
                database='postgres'
            )
            print("✓ Connected to PostgreSQL without password")
        except:
            # Try with common default passwords
            for password in ['', 'postgres', 'admin', 'password']:
                try:
                    conn = await asyncpg.connect(
                        host='localhost',
                        port=5432,
                        user='postgres',
                        password=password,
                        database='postgres'
                    )
                    print(f"✓ Connected to PostgreSQL with password: {password or '(empty)'}")
                    break
                except:
                    continue
        
        if not conn:
            print("✗ Could not connect to PostgreSQL with any common credentials")
            print("Please check PostgreSQL installation and credentials")
            sys.exit(1)
        
        # Check if database exists
        db_exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = 'talentsync'"
        )
        
        if not db_exists:
            # Create database
            await conn.execute("CREATE DATABASE talentsync")
            print("✓ Created database 'talentsync'")
        else:
            print("✓ Database 'talentsync' already exists")
        
        # Check if user exists
        user_exists = await conn.fetchval(
            "SELECT 1 FROM pg_user WHERE usename = 'talentsync'"
        )
        
        if not user_exists:
            # Create user
            await conn.execute("CREATE USER talentsync WITH PASSWORD 'secret'")
            print("✓ Created user 'talentsync'")
        else:
            print("✓ User 'talentsync' already exists")
        
        # Grant privileges
        await conn.execute("GRANT ALL PRIVILEGES ON DATABASE talentsync TO talentsync")
        print("✓ Granted privileges to user 'talentsync'")
        
        await conn.close()
        
        # Now connect to the talentsync database to set up schema
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            user='talentsync',
            password='secret',
            database='talentsync'
        )
        
        # Grant schema privileges
        await conn.execute("GRANT ALL ON SCHEMA public TO talentsync")
        await conn.execute("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO talentsync")
        await conn.execute("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO talentsync")
        
        await conn.close()
        print("✓ Database setup completed successfully!")
        
    except Exception as e:
        print(f"✗ Error setting up database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(create_database_and_user())

#!/usr/bin/env python3
"""
Test PostgreSQL connection with different methods.
"""
import asyncio
import asyncpg
import psycopg2
import sys

async def test_postgres_connection():
    """Test different ways to connect to PostgreSQL."""
    
    print("Testing PostgreSQL connection methods...")
    
    # Test with asyncpg
    print("\n1. Testing asyncpg connections:")
    
    connection_configs = [
        {"host": "localhost", "port": 5432, "user": "postgres", "database": "postgres"},
        {"host": "localhost", "port": 5432, "user": "postgres", "password": "", "database": "postgres"},
        {"host": "localhost", "port": 5432, "user": "postgres", "password": "postgres", "database": "postgres"},
        {"host": "localhost", "port": 5432, "user": "postgres", "password": "admin", "database": "postgres"},
        {"host": "localhost", "port": 5432, "user": "postgres", "password": "password", "database": "postgres"},
        {"host": "localhost", "port": 5432, "user": "talentsync", "password": "secret", "database": "talentsync"},
        {"host": "localhost", "port": 5432, "user": "talentsync", "password": "secret", "database": "postgres"},
    ]
    
    for i, config in enumerate(connection_configs, 1):
        try:
            conn = await asyncpg.connect(**config)
            await conn.close()
            print(f"  ✓ Config {i}: {config}")
            return config
        except Exception as e:
            print(f"  ✗ Config {i}: {config} - {e}")
    
    # Test with psycopg2
    print("\n2. Testing psycopg2 connections:")
    
    for i, config in enumerate(connection_configs, 1):
        try:
            # Convert asyncpg config to psycopg2 format
            psycopg2_config = config.copy()
            if 'password' not in psycopg2_config:
                psycopg2_config['password'] = None
            
            conn = psycopg2.connect(**psycopg2_config)
            conn.close()
            print(f"  ✓ Config {i}: {config}")
            return config
        except Exception as e:
            print(f"  ✗ Config {i}: {config} - {e}")
    
    print("\n✗ No working PostgreSQL connection found!")
    return None

if __name__ == "__main__":
    working_config = asyncio.run(test_postgres_connection())
    if working_config:
        print(f"\n✓ Use this configuration: {working_config}")
    else:
        print("\n✗ No working configuration found. Please check PostgreSQL setup.")

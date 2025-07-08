#!/usr/bin/env python

"""
TalentSync Interview Service Runner Script

This script helps set up and run the interview service without Docker.
It creates the database tables, loads initial data, and starts the FastAPI server.
"""

import asyncio
import os
import sys
import subprocess
from pathlib import Path

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.core.database import create_tables
    from app.core.config import get_settings
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Make sure you're running this script from the interview-service directory.")
    sys.exit(1)

settings = get_settings()

def check_database_dir():
    """Check if the data directory exists, create if not."""
    data_dir = Path("./data").resolve()
    if not data_dir.exists():
        print(f"Creating data directory: {data_dir}")
        data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

def setup_sqlite_database():
    """Set up the SQLite database file."""
    data_dir = check_database_dir()
    db_path = data_dir / "interview_service.db"
    print(f"Using SQLite database: {db_path}")
    return str(db_path)

def start_server():
    """Start the FastAPI server."""
    try:
        print(f"Starting Interview Service on port {settings.PORT}...")
        uvicorn_cmd = [
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--host", "0.0.0.0", 
            "--port", str(settings.PORT),
            "--reload"
        ]
        
        subprocess.run(uvicorn_cmd)
        return True
    except Exception as e:
        print(f"Error starting server: {e}")
        return False

async def setup_database():
    """Set up the database tables."""
    try:
        print("Creating database tables...")
        await create_tables()
        print("Database tables created successfully.")
        return True
    except Exception as e:
        print(f"Error creating database tables: {e}")
        return False

async def import_datasets():
    """Import question datasets."""
    try:
        print("Importing question datasets...")
        import_script_path = Path("./app/scripts/import_datasets.py").resolve()
        if import_script_path.exists():
            cmd = [sys.executable, str(import_script_path)]
            subprocess.run(cmd)
            print("Datasets imported successfully.")
        else:
            print(f"Import script not found at {import_script_path}")
            print("Skipping dataset import.")
        return True
    except Exception as e:
        print(f"Error importing datasets: {e}")
        print("Continuing without dataset import...")
        return True

async def main():
    """Main function to run the service."""
    print("TalentSync Interview Service Runner")
    print("==================================")
    
    # Set up the database directory
    setup_sqlite_database()
    
    # Set up the database
    if not await setup_database():
        sys.exit(1)
    
    # Import datasets
    await import_datasets()
    
    # Start the server
    if not start_server():
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

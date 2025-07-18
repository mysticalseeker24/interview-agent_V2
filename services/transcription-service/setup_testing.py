#!/usr/bin/env python3
"""
Setup script for TalentSync Transcription Service Testing

This script helps set up the testing environment by:
1. Installing required testing dependencies
2. Checking environment configuration
3. Validating service connectivity
4. Setting up test directories

Usage:
    python setup_testing.py
"""

import os
import sys
import subprocess
import asyncio
from pathlib import Path
import httpx
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def print_header(title: str):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_info(message: str):
    """Print an info message."""
    print(f"ℹ️  {message}")

def print_success(message: str):
    """Print a success message."""
    print(f"✅ {message}")

def print_error(message: str):
    """Print an error message."""
    print(f"❌ {message}")

def print_warning(message: str):
    """Print a warning message."""
    print(f"⚠️  {message}")

def check_python_version():
    """Check if Python version is compatible."""
    print_header("Python Version Check")
    
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        print_success(f"Python {version.major}.{version.minor}.{version.micro} is compatible")
        return True
    else:
        print_error(f"Python {version.major}.{version.minor}.{version.micro} is not compatible. Need Python 3.9+")
        return False

def install_test_dependencies():
    """Install testing dependencies."""
    print_header("Installing Test Dependencies")
    
    try:
        # Check if test_requirements.txt exists
        requirements_file = Path("test_requirements.txt")
        if not requirements_file.exists():
            print_error("test_requirements.txt not found")
            return False
        
        print_info("Installing testing dependencies...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "test_requirements.txt"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print_success("Test dependencies installed successfully")
            return True
        else:
            print_error(f"Failed to install dependencies: {result.stderr}")
            return False
            
    except Exception as e:
        print_error(f"Error installing dependencies: {str(e)}")
        return False

def check_environment_variables():
    """Check required environment variables."""
    print_header("Environment Variables Check")
    
    required_vars = [
        "GROQ_API_KEY",
        "GROQ_STT_MODEL",
        "GROQ_TTS_MODEL", 
        "GROQ_DEFAULT_VOICE"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print_error(f"Missing environment variables: {', '.join(missing_vars)}")
        print_info("Please set these variables in your .env file or environment")
        return False
    
    print_success("All required environment variables are set")
    return True

async def check_service_connectivity():
    """Check if transcription service is running."""
    print_header("Service Connectivity Check")
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8005/health")
            if response.status_code == 200:
                print_success("Transcription service is running and accessible")
                return True
            else:
                print_error(f"Service health check failed: {response.status_code}")
                return False
    except Exception as e:
        print_error(f"Cannot connect to transcription service: {str(e)}")
        print_info("Please start the service with: uvicorn app.main:app --reload --port 8005")
        return False

def setup_test_directories():
    """Set up test directories."""
    print_header("Test Directories Setup")
    
    directories = [
        "uploads",
        "tts_cache", 
        "test_outputs"
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print_success(f"Created directory: {directory}")
        else:
            print_info(f"Directory exists: {directory}")
    
    return True

def check_audio_dependencies():
    """Check audio processing dependencies."""
    print_header("Audio Dependencies Check")
    
    try:
        import sounddevice
        import soundfile
        import numpy
        print_success("Audio processing libraries are available")
        return True
    except ImportError as e:
        print_warning(f"Audio libraries not available: {str(e)}")
        print_info("Live mock interview will use simulated responses")
        return False

def show_testing_instructions():
    """Show instructions for running tests."""
    print_header("Testing Instructions")
    
    print("🚀 To run comprehensive tests:")
    print("   python test_comprehensive_service.py")
    print()
    
    print("🎭 To run live mock interview:")
    print("   python test_live_mock_interview.py")
    print()
    
    print("🧪 To run pytest tests:")
    print("   pytest test_*.py -v")
    print()
    
    print("📊 To run with coverage:")
    print("   pytest test_*.py --cov=app --cov-report=html")
    print()
    
    print("🔧 To start the service for testing:")
    print("   uvicorn app.main:app --reload --port 8005")
    print()

async def main():
    """Main setup function."""
    print_header("TalentSync Transcription Service Testing Setup")
    print_info("Setting up testing environment...")
    
    # Run all checks
    checks = [
        ("Python Version", check_python_version),
        ("Test Dependencies", install_test_dependencies),
        ("Environment Variables", check_environment_variables),
        ("Service Connectivity", check_service_connectivity),
        ("Test Directories", setup_test_directories),
        ("Audio Dependencies", check_audio_dependencies)
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            if asyncio.iscoroutinefunction(check_func):
                result = await check_func()
            else:
                result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print_error(f"{check_name} check failed: {str(e)}")
            results.append((check_name, False))
    
    # Summary
    print_header("Setup Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"📊 Checks passed: {passed}/{total}")
    
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} | {check_name}")
    
    if passed == total:
        print_success("All checks passed! Testing environment is ready.")
        show_testing_instructions()
    else:
        print_warning(f"{total - passed} checks failed. Please address the issues above.")
        print_info("You can still run tests, but some features may not work properly.")

if __name__ == "__main__":
    asyncio.run(main()) 
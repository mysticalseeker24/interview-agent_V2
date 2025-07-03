"""
Test script for the Transcription Service endpoints.
This script tests both the media devices and transcription endpoints.
"""

import asyncio
import httpx
import json
from pathlib import Path


async def test_media_devices():
    """Test the media devices endpoint."""
    print("Testing media devices endpoint...")
    
    async with httpx.AsyncClient() as client:
        # Test POST /media/devices
        response = await client.post(
            "http://localhost:8005/media/devices",
            headers={"Authorization": "Bearer test-token"}
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        return response.status_code == 200


async def test_transcription():
    """Test the transcription endpoint."""
    print("\nTesting transcription endpoint...")
    
    # Create a dummy audio file for testing
    test_file_path = Path("test_audio.mp3")
    test_file_path.write_bytes(b"dummy audio content")
    
    try:
        async with httpx.AsyncClient() as client:
            # Test POST /transcribe
            with open(test_file_path, "rb") as f:
                files = {"file": ("test_audio.mp3", f, "audio/mpeg")}
                response = await client.post(
                    "http://localhost:8005/transcribe",
                    files=files,
                    headers={"Authorization": "Bearer test-token"}
                )
            
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
            
            return response.status_code == 200
            
    finally:
        # Clean up test file
        if test_file_path.exists():
            test_file_path.unlink()


async def test_health():
    """Test the health endpoint."""
    print("\nTesting health endpoint...")
    
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8005/health")
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        return response.status_code == 200


async def main():
    """Run all tests."""
    print("Starting Transcription Service tests...")
    print("=" * 50)
    
    # Test health first
    health_ok = await test_health()
    
    # Test media devices
    media_ok = await test_media_devices()
    
    # Test transcription (this will fail without real API keys)
    transcription_ok = await test_transcription()
    
    print("\n" + "=" * 50)
    print("Test Results:")
    print(f"Health: {'✓' if health_ok else '✗'}")
    print(f"Media Devices: {'✓' if media_ok else '✗'}")
    print(f"Transcription: {'✓' if transcription_ok else '✗'}")
    
    if all([health_ok, media_ok]):
        print("\nCore endpoints are working! 🎉")
    else:
        print("\nSome endpoints need attention 🔧")


if __name__ == "__main__":
    asyncio.run(main())

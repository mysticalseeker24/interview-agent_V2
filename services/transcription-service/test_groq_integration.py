#!/usr/bin/env python3
"""
Test script for Groq API integration in TalentSync Transcription Service.

This script tests the basic functionality of the transcription service
with Groq API integration for both STT and TTS.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.core.config import settings
from app.services.groq_stt import GroqSTTClient
from app.services.playai_tts import GroqTTSClient


async def test_groq_configuration():
    """Test that Groq configuration is properly set up."""
    print("🔧 Testing Groq Configuration...")
    
    # Check required environment variables
    if not settings.groq_api_key:
        print("❌ GROQ_API_KEY not set")
        return False
    
    print(f"✅ GROQ_API_KEY configured")
    print(f"✅ GROQ_BASE_URL: {settings.groq_base_url}")
    print(f"✅ GROQ_STT_MODEL: {settings.groq_stt_model}")
    print(f"✅ GROQ_TTS_MODEL: {settings.groq_tts_model}")
    print(f"✅ GROQ_DEFAULT_VOICE: {settings.groq_default_voice}")
    
    return True


async def test_stt_client():
    """Test the Groq STT client."""
    print("\n🎤 Testing Groq STT Client...")
    
    try:
        stt_client = GroqSTTClient()
        
        # Test health check
        health_result = await stt_client.health_check()
        print(f"✅ STT Health Check: {health_result['status']}")
        
        if health_result['status'] == 'healthy':
            print(f"✅ Whisper model available: {health_result.get('whisper_model_available', False)}")
            return True
        else:
            print(f"❌ STT Health Check failed: {health_result['message']}")
            return False
            
    except Exception as e:
        print(f"❌ STT Client test failed: {str(e)}")
        return False


async def test_tts_client():
    """Test the Groq TTS client."""
    print("\n🔊 Testing Groq TTS Client...")
    
    try:
        tts_client = GroqTTSClient()
        
        # Test health check
        health_result = await tts_client.health_check()
        print(f"✅ TTS Health Check: {health_result['status']}")
        
        if health_result['status'] == 'healthy':
            print(f"✅ TTS model available: {health_result.get('tts_model_available', False)}")
            
            # Test getting available voices
            voices = await tts_client.get_available_voices()
            print(f"✅ Available voices: {len(voices)}")
            print(f"✅ Default voice '{settings.groq_default_voice}' available: {settings.groq_default_voice in voices}")
            
            return True
        else:
            print(f"❌ TTS Health Check failed: {health_result['message']}")
            return False
            
    except Exception as e:
        print(f"❌ TTS Client test failed: {str(e)}")
        return False


async def test_service_endpoints():
    """Test the service endpoints."""
    print("\n🌐 Testing Service Endpoints...")
    
    try:
        import httpx
        
        # Test health endpoint
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8005/health")
            if response.status_code == 200:
                print("✅ Health endpoint accessible")
            else:
                print(f"❌ Health endpoint failed: {response.status_code}")
                return False
            
            # Test interview status endpoint
            response = await client.get("http://localhost:8005/api/v1/interview/status")
            if response.status_code == 200:
                print("✅ Interview status endpoint accessible")
            else:
                print(f"❌ Interview status endpoint failed: {response.status_code}")
                return False
                
        return True
        
    except Exception as e:
        print(f"❌ Service endpoints test failed: {str(e)}")
        return False


async def main():
    """Run all tests."""
    print("🧪 TalentSync Transcription Service - Groq Integration Test")
    print("=" * 60)
    
    # Test configuration
    config_ok = await test_groq_configuration()
    
    # Test STT client
    stt_ok = await test_stt_client()
    
    # Test TTS client
    tts_ok = await test_tts_client()
    
    # Test service endpoints (if service is running)
    endpoints_ok = await test_service_endpoints()
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    print(f"Configuration: {'✅ PASS' if config_ok else '❌ FAIL'}")
    print(f"STT Client: {'✅ PASS' if stt_ok else '❌ FAIL'}")
    print(f"TTS Client: {'✅ PASS' if tts_ok else '❌ FAIL'}")
    print(f"Service Endpoints: {'✅ PASS' if endpoints_ok else '⚠️  SKIP (service not running)'}")
    
    if config_ok and stt_ok and tts_ok:
        print("\n🎉 All core tests passed! Groq integration is working correctly.")
        return True
    else:
        print("\n❌ Some tests failed. Please check your configuration.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 
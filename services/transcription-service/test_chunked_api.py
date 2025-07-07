#!/usr/bin/env python3

"""
Test script for chunked transcription API endpoints.

This script tests:
1. POST /transcribe/chunk/{media_chunk_id} - Individual chunk transcription
2. POST /transcribe/session-complete/{session_id} - Session aggregation
3. GET /transcribe/session/{session_id}/chunks - Chunk retrieval
4. GET /transcribe/session/{session_id}/transcript - Transcript retrieval
"""

import asyncio
import base64
import json
import os
import sys
from pathlib import Path
import httpx

# Test configuration
BASE_URL = "http://localhost:8000"
API_PREFIX = "/transcribe"

async def test_chunked_api_endpoints():
    """Test the chunked transcription API endpoints."""
    print("🔧 Testing Chunked Transcription API Endpoints...")
    
    # Test audio file
    test_audio_path = Path(__file__).parent / "test-assets" / "audio" / "output2.mp3"
    
    if not test_audio_path.exists():
        print(f"❌ Test audio file not found at {test_audio_path}")
        return False
    
    # Read and encode the test audio
    with open(test_audio_path, "rb") as f:
        audio_data = f.read()
    
    # Convert to base64
    audio_b64 = base64.b64encode(audio_data).decode('utf-8')
    
    # Test session parameters
    session_id = "test_api_session_001"
    
    # Create test chunks
    test_chunks = [
        {
            "media_chunk_id": f"api_chunk_{session_id}_001",
            "sequence_index": 1,
            "audio_data": audio_b64[:len(audio_b64)//2],  # First half
        },
        {
            "media_chunk_id": f"api_chunk_{session_id}_002", 
            "sequence_index": 2,
            "audio_data": audio_b64[len(audio_b64)//2:],  # Second half
        }
    ]
    
    async with httpx.AsyncClient() as client:
        try:
            # Test 1: Individual chunk transcription
            print(f"\n📝 Testing individual chunk transcription...")
            
            chunk_results = []
            for i, chunk_data in enumerate(test_chunks):
                print(f"Processing chunk {i+1}: {chunk_data['media_chunk_id']}")
                
                # Prepare request
                request_data = {
                    "session_id": session_id,
                    "media_chunk_id": chunk_data['media_chunk_id'],
                    "sequence_index": chunk_data['sequence_index'],
                    "audio_data": chunk_data['audio_data'],
                    "question_id": "test_question_001"
                }
                
                # Make API call
                response = await client.post(
                    f"{BASE_URL}{API_PREFIX}/chunk/{chunk_data['media_chunk_id']}",
                    json=request_data,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    chunk_results.append(result)
                    print(f"✅ Chunk {i+1} transcribed successfully!")
                    print(f"   ID: {result['id']}")
                    print(f"   Text: {result['transcript_text'][:100]}...")
                    print(f"   Confidence: {result.get('confidence_score', 'N/A')}")
                    print(f"   Segments: {len(result.get('segments', []))}")
                else:
                    print(f"❌ Chunk {i+1} failed with status {response.status_code}: {response.text}")
                    return False
            
            # Test 2: Session completion
            print(f"\n🔗 Testing session completion...")
            
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/session-complete/{session_id}",
                json={"session_id": session_id},
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Session completion successful!")
                print(f"   Session ID: {result['session_id']}")
                print(f"   Total chunks: {result['total_chunks']}")
                print(f"   Confidence: {result.get('confidence_score', 'N/A')}")
                print(f"   Full transcript: {result['full_transcript'][:200]}...")
                print(f"   Segments: {len(result.get('segments', []))}")
            else:
                print(f"❌ Session completion failed with status {response.status_code}: {response.text}")
                return False
            
            # Test 3: Retrieve session chunks
            print(f"\n🔍 Testing session chunk retrieval...")
            
            response = await client.get(f"{BASE_URL}{API_PREFIX}/session/{session_id}/chunks")
            
            if response.status_code == 200:
                chunks = response.json()
                print(f"✅ Retrieved {len(chunks)} chunks!")
                for chunk in chunks:
                    print(f"   Chunk {chunk['sequence_index']}: {chunk['media_chunk_id']}")
            else:
                print(f"❌ Chunk retrieval failed with status {response.status_code}: {response.text}")
                return False
            
            # Test 4: Retrieve session transcript
            print(f"\n📄 Testing session transcript retrieval...")
            
            response = await client.get(f"{BASE_URL}{API_PREFIX}/session/{session_id}/transcript")
            
            if response.status_code == 200:
                transcript = response.json()
                print(f"✅ Retrieved session transcript!")
                print(f"   Total chunks: {transcript['total_chunks']}")
                print(f"   Confidence: {transcript.get('confidence_score', 'N/A')}")
                print(f"   Segments: {len(transcript.get('segments', []))}")
                print(f"   Full transcript: {transcript['full_transcript'][:200]}...")
            else:
                print(f"❌ Transcript retrieval failed with status {response.status_code}: {response.text}")
                return False
            
            return True
            
        except httpx.RequestError as e:
            print(f"❌ HTTP request error: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False

async def test_service_health():
    """Test if the transcription service is running."""
    print("🔧 Testing Service Health...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/health", timeout=5.0)
            if response.status_code == 200:
                print("✅ Service is healthy!")
                return True
            else:
                print(f"❌ Service health check failed with status {response.status_code}")
                return False
        except httpx.ConnectError:
            print("❌ Cannot connect to the service. Is it running?")
            print(f"   Expected service at: {BASE_URL}")
            return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False

async def test_openai_config():
    """Test if OpenAI configuration is working."""
    print("🔧 Testing OpenAI Configuration...")
    
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY environment variable not set")
        return False
    
    # Test with a simple transcription call
    async with httpx.AsyncClient() as client:
        try:
            # Create a simple transcription request
            simple_request = {
                "session_id": "test_openai_config",
                "question_id": "test_question",
                "transcript_text": "This is a test transcription"
            }
            
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/",
                json=simple_request,
                timeout=10.0
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ OpenAI configuration test passed!")
                print(f"   Created transcription ID: {result['id']}")
                return True
            else:
                print(f"❌ OpenAI configuration test failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ OpenAI configuration test error: {e}")
            return False

async def main():
    """Run all API tests."""
    print("🚀 Starting Chunked Transcription API Tests...")
    
    tests = [
        ("Service Health", test_service_health),
        ("OpenAI Configuration", test_openai_config),
        ("Chunked API Endpoints", test_chunked_api_endpoints),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Running: {test_name}")
        print(f"{'='*60}")
        
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("API TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Total: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All API tests passed! Service is ready for chunked transcription.")
    else:
        print("⚠️  Some tests failed. Please check the service and try again.")

if __name__ == "__main__":
    asyncio.run(main())

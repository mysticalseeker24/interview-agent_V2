#!/usr/bin/env python3
"""
Simple test script to test the Media Service chunk upload endpoint.
"""
import requests

def test_chunk_upload():
    url = "http://localhost:8003/media/chunk-upload"
    
    # Test data
    data = {
        'session_id': 'test_session_123',
        'sequence_index': '0',
        'total_chunks': '3',
        'overlap_seconds': '2.0'
    }
    
    # Mock file content
    files = {
        'file': ('test_audio.webm', b'mock audio content for testing', 'audio/webm')
    }
    
    try:
        print("Testing chunk upload endpoint...")
        response = requests.post(url, data=data, files=files)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Chunk upload successful!")
        else:
            print("❌ Chunk upload failed!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_session_summary():
    url = "http://localhost:8003/media/session/test_session_123/summary"
    
    try:
        print("\nTesting session summary endpoint...")
        response = requests.get(url)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Session summary successful!")
        else:
            print("❌ Session summary failed!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_metrics():
    url = "http://localhost:8003/metrics"
    
    try:
        print("\nTesting metrics endpoint...")
        response = requests.get(url)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Metrics endpoint successful!")
        else:
            print("❌ Metrics endpoint failed!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🔧 Testing Media Service Endpoints")
    print("=" * 50)
    
    test_chunk_upload()
    test_session_summary()
    test_metrics()
    
    print("\n" + "=" * 50)
    print("✅ Testing completed!")

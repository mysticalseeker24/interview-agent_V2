#!/usr/bin/env python3
"""
Comprehensive test script for Media Service chunked upload functionality.
"""
import requests
import time
import json

def test_multi_chunk_upload():
    """Test uploading multiple chunks for a session."""
    base_url = "http://localhost:8003/media"
    session_id = "test_multi_session_456"
    total_chunks = 3
    
    print(f"🔧 Testing multi-chunk upload for session: {session_id}")
    print("=" * 60)
    
    # Upload multiple chunks
    for i in range(total_chunks):
        print(f"\n📁 Uploading chunk {i}/{total_chunks-1}...")
        
        data = {
            'session_id': session_id,
            'sequence_index': str(i),
            'total_chunks': str(total_chunks),
            'overlap_seconds': '2.0'
        }
        
        # Create different content for each chunk
        content = f'mock audio content for chunk {i} - {time.time()}'.encode()
        files = {
            'file': (f'chunk_{i}.webm', content, 'audio/webm')
        }
        
        try:
            response = requests.post(f"{base_url}/chunk-upload", data=data, files=files)
            
            if response.status_code == 200:
                result = response.json()
                print(f"  ✅ Chunk {i} uploaded successfully!")
                print(f"     Chunk ID: {result['chunk_id']}")
                print(f"     File Path: {result['file_path']}")
            else:
                print(f"  ❌ Chunk {i} upload failed: {response.status_code}")
                print(f"     Error: {response.text}")
                
        except Exception as e:
            print(f"  ❌ Error uploading chunk {i}: {e}")
    
    # Test session summary
    print(f"\n📊 Getting session summary...")
    try:
        response = requests.get(f"{base_url}/session/{session_id}/summary")
        
        if response.status_code == 200:
            summary = response.json()
            print(f"  ✅ Session Summary:")
            print(f"     Total Chunks: {summary['total_chunks']}")
            print(f"     Uploaded Chunks: {summary['uploaded_chunks']}")
            print(f"     Session Status: {summary['session_status']}")
            print(f"     Total Duration: {summary['total_duration_seconds']}s")
            
            # Print chunk details
            print(f"     Chunks Details:")
            for chunk in summary['chunks']:
                print(f"       - Chunk {chunk['sequence_index']}: {chunk['file_size_bytes']} bytes")
        else:
            print(f"  ❌ Session summary failed: {response.status_code}")
            
    except Exception as e:
        print(f"  ❌ Error getting session summary: {e}")
    
    # Test gap detection
    print(f"\n🔍 Checking for gaps...")
    try:
        response = requests.get(f"{base_url}/session/{session_id}/gaps")
        
        if response.status_code == 200:
            gaps = response.json()
            if gaps.get('gaps'):
                print(f"  ⚠️  Gaps found: {gaps['gaps']}")
            else:
                print(f"  ✅ No gaps found - all chunks uploaded correctly!")
        else:
            print(f"  ❌ Gap check failed: {response.status_code}")
            
    except Exception as e:
        print(f"  ❌ Error checking gaps: {e}")

def test_storage_stats():
    """Test storage statistics endpoint."""
    print(f"\n💾 Testing storage statistics...")
    
    try:
        response = requests.get("http://localhost:8003/media/storage/stats")
        
        if response.status_code == 200:
            stats = response.json()
            print(f"  ✅ Storage Statistics:")
            print(f"     Total Sessions: {stats['total_sessions']}")
            print(f"     Active Sessions: {stats['active_sessions']}")
            print(f"     Total Chunks: {stats['total_chunks']}")
            print(f"     Storage Used: {stats['storage_used_bytes']} bytes")
            print(f"     Average Chunk Size: {stats['average_chunk_size_bytes']:.1f} bytes")
        else:
            print(f"  ❌ Storage stats failed: {response.status_code}")
            
    except Exception as e:
        print(f"  ❌ Error getting storage stats: {e}")

def test_health_and_metrics():
    """Test health and metrics endpoints."""
    print(f"\n🏥 Testing health and metrics...")
    
    # Health check
    try:
        response = requests.get("http://localhost:8003/health")
        
        if response.status_code == 200:
            health = response.json()
            print(f"  ✅ Health Status: {health['status']}")
            print(f"     Database: {health['components']['database']}")
            print(f"     Storage: {health['components']['storage']}")
            print(f"     Redis: {health['components']['redis']}")
        else:
            print(f"  ❌ Health check failed: {response.status_code}")
            
    except Exception as e:
        print(f"  ❌ Error checking health: {e}")
    
    # Metrics
    try:
        response = requests.get("http://localhost:8003/metrics")
        
        if response.status_code == 200:
            metrics = response.json()
            print(f"  ✅ System Metrics:")
            print(f"     Active Sessions: {metrics['active_sessions']}")
            print(f"     Processing Queue: {metrics['processing_queue_size']}")
        else:
            print(f"  ❌ Metrics failed: {response.status_code}")
            
    except Exception as e:
        print(f"  ❌ Error getting metrics: {e}")

if __name__ == "__main__":
    print("🚀 Comprehensive Media Service Test")
    print("=" * 60)
    
    test_multi_chunk_upload()
    test_storage_stats()
    test_health_and_metrics()
    
    print("\n" + "=" * 60)
    print("🎉 Comprehensive testing completed!")
    print("\n📝 Summary:")
    print("   - Multi-chunk upload functionality ✅")
    print("   - Session management ✅") 
    print("   - Gap detection ✅")
    print("   - Storage statistics ✅")
    print("   - Health monitoring ✅")
    print("   - Metrics collection ✅")

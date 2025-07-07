#!/usr/bin/env python3

"""
Test script for chunked transcription functionality.

This script tests:
1. Individual chunk transcription
2. Session-level aggregation
3. Segment deduplication
4. Confidence scoring
5. Integration with OpenAI Whisper
"""

import asyncio
import base64
import json
import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session, engine
from app.services.transcription_service import TranscriptionService
from app.schemas.transcription import TranscriptionChunkRequest

async def test_audio_chunking():
    """Test the chunked transcription pipeline."""
    print("🔧 Testing Chunked Transcription Pipeline...")
    
    # Initialize the transcription service
    transcription_service = TranscriptionService()
    
    # Create test audio data (simulate base64 encoded audio)
    # Use the same test audio file we used before
    test_audio_path = Path(__file__).parent.parent / "interview-pilot-ai" / "conversational-dialog" / "test-files" / "output2.mp3"
    
    if not test_audio_path.exists():
        print(f"❌ Test audio file not found at {test_audio_path}")
        return False
    
    # Read and encode the test audio
    with open(test_audio_path, "rb") as f:
        audio_data = f.read()
    
    # Convert to base64
    audio_b64 = base64.b64encode(audio_data).decode('utf-8')
    
    # Test session parameters
    session_id = "test_session_chunked_001"
    
    # Create test chunks (simulate splitting audio)
    test_chunks = [
        {
            "media_chunk_id": f"chunk_{session_id}_001",
            "sequence_index": 1,
            "audio_data": audio_b64[:len(audio_b64)//2],  # First half
        },
        {
            "media_chunk_id": f"chunk_{session_id}_002", 
            "sequence_index": 2,
            "audio_data": audio_b64[len(audio_b64)//2:],  # Second half
        }
    ]
    
    try:
        # Get database session
        async with engine.begin() as conn:
            from app.core.database import Base
            await conn.run_sync(Base.metadata.create_all)
        
        async for session in get_session():
            transcription_results = []
            
            # Process each chunk
            for i, chunk_data in enumerate(test_chunks):
                print(f"📝 Processing chunk {i+1}/{len(test_chunks)}: {chunk_data['media_chunk_id']}")
                
                try:
                    # Decode the chunk audio
                    chunk_audio = base64.b64decode(chunk_data['audio_data'])
                    
                    # Transcribe the chunk
                    transcript_result = await transcription_service.transcribe_audio_chunk(chunk_audio)
                    print(f"✅ Chunk {i+1} transcribed: {transcript_result['text'][:100]}...")
                    
                    # Save the chunk
                    transcription = await transcription_service.save_transcription_chunk(
                        session=session,
                        session_id=session_id,
                        media_chunk_id=chunk_data['media_chunk_id'],
                        sequence_index=chunk_data['sequence_index'],
                        transcript_text=transcript_result['text'],
                        segments=transcript_result['segments'],
                        confidence_score=transcript_result['confidence_score']
                    )
                    
                    transcription_results.append(transcription)
                    print(f"💾 Chunk {i+1} saved to database with ID: {transcription.id}")
                    
                except Exception as e:
                    print(f"❌ Error processing chunk {i+1}: {e}")
                    continue
            
            # Test session aggregation
            print(f"\n🔗 Testing session aggregation for session: {session_id}")
            
            try:
                aggregated_result = await transcription_service.aggregate_session_transcript(
                    session=session,
                    session_id=session_id
                )
                
                print(f"✅ Session aggregation successful!")
                print(f"📊 Total chunks: {aggregated_result['total_chunks']}")
                print(f"📊 Average confidence: {aggregated_result.get('confidence_score', 'N/A')}")
                print(f"📊 Total segments: {len(aggregated_result.get('segments', []))}")
                print(f"📝 Full transcript: {aggregated_result['full_transcript'][:200]}...")
                
                # Test chunk retrieval
                chunks = await transcription_service.get_session_chunks(session, session_id)
                print(f"🔍 Retrieved {len(chunks)} chunks from database")
                
                return True
                
            except Exception as e:
                print(f"❌ Error in session aggregation: {e}")
                return False
    
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

async def test_segment_deduplication():
    """Test segment deduplication logic."""
    print("\n🔧 Testing Segment Deduplication...")
    
    transcription_service = TranscriptionService()
    
    # Create test segments with overlaps
    test_segments = [
        {"start": 0.0, "end": 2.0, "text": "Hello world"},
        {"start": 1.5, "end": 3.5, "text": "Hello world"},  # Overlap - should be deduplicated
        {"start": 3.0, "end": 5.0, "text": "This is a test"},
        {"start": 4.5, "end": 6.5, "text": "This is different"},  # Different text - should be kept
        {"start": 6.0, "end": 8.0, "text": "Final segment"}
    ]
    
    deduplicated = transcription_service._deduplicate_segments(test_segments)
    
    print(f"📊 Original segments: {len(test_segments)}")
    print(f"📊 Deduplicated segments: {len(deduplicated)}")
    
    for i, segment in enumerate(deduplicated):
        print(f"  {i+1}. {segment['start']:.1f}s - {segment['end']:.1f}s: {segment['text']}")
    
    # Should have 4 segments (one duplicate removed)
    expected_count = 4
    if len(deduplicated) == expected_count:
        print(f"✅ Deduplication test passed! Expected {expected_count}, got {len(deduplicated)}")
        return True
    else:
        print(f"❌ Deduplication test failed! Expected {expected_count}, got {len(deduplicated)}")
        return False

async def test_confidence_scoring():
    """Test confidence scoring calculation."""
    print("\n🔧 Testing Confidence Scoring...")
    
    # This test requires actual OpenAI API call
    transcription_service = TranscriptionService()
    
    # Use a small test audio file
    test_audio_path = Path(__file__).parent.parent / "interview-pilot-ai" / "conversational-dialog" / "test-files" / "output2.mp3"
    
    if not test_audio_path.exists():
        print(f"❌ Test audio file not found at {test_audio_path}")
        return False
    
    try:
        with open(test_audio_path, "rb") as f:
            audio_data = f.read()
        
        # Test with verbose_json to get confidence scores
        result = await transcription_service.transcribe_audio_chunk(audio_data, use_verbose=True)
        
        print(f"📊 Transcription: {result['text'][:100]}...")
        print(f"📊 Confidence Score: {result.get('confidence_score', 'N/A')}")
        print(f"📊 Segments Count: {len(result.get('segments', []))}")
        
        if result.get('confidence_score') is not None:
            print("✅ Confidence scoring test passed!")
            return True
        else:
            print("❌ Confidence scoring test failed - no confidence score returned")
            return False
            
    except Exception as e:
        print(f"❌ Error in confidence scoring test: {e}")
        return False

async def main():
    """Run all tests."""
    print("🚀 Starting Chunked Transcription Tests...")
    
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY environment variable not set")
        return
    
    tests = [
        ("Segment Deduplication", test_segment_deduplication),
        ("Confidence Scoring", test_confidence_scoring),
        ("Audio Chunking Pipeline", test_audio_chunking),
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
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Total: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Chunked transcription is ready.")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")

if __name__ == "__main__":
    asyncio.run(main())

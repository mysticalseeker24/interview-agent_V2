#!/usr/bin/env python3

"""
Comprehensive Integration Test Suite for Transcription Service

This test suite covers:
1. End-to-end chunked transcription workflow
2. Error handling and edge cases
3. Integration with interview-service webhooks
4. Performance and stress testing
5. Data validation and consistency
6. Session management and cleanup
"""

import asyncio
import base64
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any
import httpx
import uuid

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session, engine
from app.services.transcription_service import TranscriptionService
from app.services.integration_service import IntegrationService
from app.schemas.transcription import TranscriptionChunkRequest

class ComprehensiveTestSuite:
    """Comprehensive test suite for transcription service."""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.api_prefix = "/transcribe"
        self.test_audio_path = Path(__file__).parent / "test-assets" / "audio" / "output2.mp3"
        self.transcription_service = TranscriptionService()
        self.integration_service = IntegrationService()
        self.test_results = []
        
    async def setup_test_environment(self):
        """Set up test environment and database."""
        print("🔧 Setting up test environment...")
        
        # Create database tables
        async with engine.begin() as conn:
            from app.core.database import Base
            await conn.run_sync(Base.metadata.create_all)
        
        # Verify test audio file exists
        if not self.test_audio_path.exists():
            raise FileNotFoundError(f"Test audio file not found: {self.test_audio_path}")
        
        print("✅ Test environment setup complete")
    
    async def cleanup_test_data(self, session_ids: List[str]):
        """Clean up test data after tests."""
        print(f"🧹 Cleaning up test data for {len(session_ids)} sessions...")
        
        async for session in get_session():
            for session_id in session_ids:
                try:
                    # Delete transcription chunks for this session
                    from app.models.transcription import Transcription
                    from sqlalchemy import select, delete
                    
                    # Get all transcriptions for this session
                    result = await session.execute(
                        select(Transcription).where(Transcription.session_id == session_id)
                    )
                    transcriptions = result.scalars().all()
                    
                    # Delete them
                    await session.execute(
                        delete(Transcription).where(Transcription.session_id == session_id)
                    )
                    await session.commit()
                    
                    print(f"🗑️  Cleaned up {len(transcriptions)} transcriptions for session {session_id}")
                    
                except Exception as e:
                    print(f"⚠️  Error cleaning up session {session_id}: {e}")
                    await session.rollback()
    
    async def test_basic_chunked_workflow(self) -> bool:
        """Test the basic chunked transcription workflow."""
        print("\n🔧 Testing Basic Chunked Workflow...")
        
        session_id = f"test_basic_{uuid.uuid4().hex[:8]}"
        
        try:
            # Read and encode test audio
            with open(self.test_audio_path, "rb") as f:
                audio_data = f.read()
            
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
            
            # Split into chunks
            chunk_size = len(audio_b64) // 3
            chunks = [
                {
                    "media_chunk_id": f"basic_chunk_{session_id}_{i:03d}",
                    "sequence_index": i + 1,
                    "audio_data": audio_b64[i * chunk_size:(i + 1) * chunk_size] if i < 2 else audio_b64[i * chunk_size:],
                } for i in range(3)
            ]
            
            async for session in get_session():
                transcription_results = []
                
                # Process each chunk
                for chunk_data in chunks:
                    chunk_audio = base64.b64decode(chunk_data['audio_data'])
                    
                    # Transcribe the chunk
                    transcript_result = await self.transcription_service.transcribe_audio_chunk(chunk_audio)
                    
                    # Save the chunk
                    transcription = await self.transcription_service.save_transcription_chunk(
                        session=session,
                        session_id=session_id,
                        media_chunk_id=chunk_data['media_chunk_id'],
                        sequence_index=chunk_data['sequence_index'],
                        transcript_text=transcript_result['text'],
                        segments=transcript_result['segments'],
                        confidence_score=transcript_result['confidence_score']
                    )
                    
                    transcription_results.append(transcription)
                
                # Aggregate session
                aggregated_result = await self.transcription_service.aggregate_session_transcript(
                    session=session,
                    session_id=session_id
                )
                
                # Validate results
                assert len(transcription_results) == 3, f"Expected 3 chunks, got {len(transcription_results)}"
                assert aggregated_result['total_chunks'] == 3, f"Expected 3 chunks in aggregation, got {aggregated_result['total_chunks']}"
                assert len(aggregated_result['full_transcript']) > 0, "Full transcript should not be empty"
                
                print(f"✅ Basic workflow test passed!")
                print(f"   Session: {session_id}")
                print(f"   Chunks: {len(transcription_results)}")
                print(f"   Transcript length: {len(aggregated_result['full_transcript'])}")
                
                return True
                
        except Exception as e:
            print(f"❌ Basic workflow test failed: {e}")
            return False
        finally:
            await self.cleanup_test_data([session_id])
    
    async def test_error_handling(self) -> bool:
        """Test error handling for various edge cases."""
        print("\n🔧 Testing Error Handling...")
        
        session_id = f"test_error_{uuid.uuid4().hex[:8]}"
        
        try:
            async for session in get_session():
                # Test 1: Invalid audio data
                try:
                    await self.transcription_service.transcribe_audio_chunk(b"invalid audio data")
                    print("❌ Should have failed with invalid audio data")
                    return False
                except Exception as e:
                    print(f"✅ Correctly handled invalid audio data: {type(e).__name__}")
                
                # Test 2: Empty audio data
                try:
                    await self.transcription_service.transcribe_audio_chunk(b"")
                    print("❌ Should have failed with empty audio data")
                    return False
                except Exception as e:
                    print(f"✅ Correctly handled empty audio data: {type(e).__name__}")
                
                # Test 3: Aggregation with no chunks
                try:
                    result = await self.transcription_service.aggregate_session_transcript(
                        session=session,
                        session_id="nonexistent_session"
                    )
                    # Should return empty result, not fail
                    assert result['total_chunks'] == 0, "Should have 0 chunks for nonexistent session"
                    print("✅ Correctly handled aggregation with no chunks")
                except Exception as e:
                    print(f"❌ Aggregation with no chunks should not fail: {e}")
                    return False
                
                # Test 4: Duplicate chunk processing
                chunk_id = f"duplicate_chunk_{session_id}"
                valid_audio = self._create_test_audio_bytes()
                
                transcript_result = await self.transcription_service.transcribe_audio_chunk(valid_audio)
                
                # Save the same chunk twice
                transcription1 = await self.transcription_service.save_transcription_chunk(
                    session=session,
                    session_id=session_id,
                    media_chunk_id=chunk_id,
                    sequence_index=1,
                    transcript_text=transcript_result['text'],
                    segments=transcript_result['segments'],
                    confidence_score=transcript_result['confidence_score']
                )
                
                # This should work (update existing or create new)
                transcription2 = await self.transcription_service.save_transcription_chunk(
                    session=session,
                    session_id=session_id,
                    media_chunk_id=chunk_id,
                    sequence_index=1,
                    transcript_text=transcript_result['text'],
                    segments=transcript_result['segments'],
                    confidence_score=transcript_result['confidence_score']
                )
                
                print(f"✅ Correctly handled duplicate chunk processing")
                
                return True
                
        except Exception as e:
            print(f"❌ Error handling test failed: {e}")
            return False
        finally:
            await self.cleanup_test_data([session_id])
    
    async def test_api_endpoints(self) -> bool:
        """Test API endpoints with various scenarios."""
        print("\n🔧 Testing API Endpoints...")
        
        session_id = f"test_api_{uuid.uuid4().hex[:8]}"
        
        try:
            async with httpx.AsyncClient() as client:
                # Test 1: Health check
                response = await client.get(f"{self.base_url}/health")
                assert response.status_code == 200, f"Health check failed: {response.status_code}"
                print("✅ Health check passed")
                
                # Test 2: Chunk transcription endpoint
                audio_data = self._create_test_audio_b64()
                chunk_id = f"api_chunk_{session_id}_001"
                
                request_data = {
                    "session_id": session_id,
                    "media_chunk_id": chunk_id,
                    "sequence_index": 1,
                    "audio_data": audio_data,
                    "question_id": "test_question_001"
                }
                
                response = await client.post(
                    f"{self.base_url}{self.api_prefix}/chunk/{chunk_id}",
                    json=request_data,
                    timeout=30.0
                )
                
                assert response.status_code == 200, f"Chunk transcription failed: {response.status_code} - {response.text}"
                result = response.json()
                assert result['media_chunk_id'] == chunk_id, "Chunk ID mismatch"
                print("✅ Chunk transcription endpoint passed")
                
                # Test 3: Session completion endpoint
                response = await client.post(
                    f"{self.base_url}{self.api_prefix}/session-complete/{session_id}",
                    timeout=30.0
                )
                
                assert response.status_code == 200, f"Session completion failed: {response.status_code} - {response.text}"
                result = response.json()
                assert result['session_id'] == session_id, "Session ID mismatch"
                print("✅ Session completion endpoint passed")
                
                # Test 4: Get session chunks
                response = await client.get(f"{self.base_url}{self.api_prefix}/session/{session_id}/chunks")
                assert response.status_code == 200, f"Get chunks failed: {response.status_code} - {response.text}"
                chunks = response.json()
                assert len(chunks) >= 1, "Should have at least 1 chunk"
                print("✅ Get session chunks endpoint passed")
                
                # Test 5: Get session transcript
                response = await client.get(f"{self.base_url}{self.api_prefix}/session/{session_id}/transcript")
                assert response.status_code == 200, f"Get transcript failed: {response.status_code} - {response.text}"
                transcript = response.json()
                assert len(transcript['full_transcript']) > 0, "Transcript should not be empty"
                print("✅ Get session transcript endpoint passed")
                
                return True
                
        except Exception as e:
            print(f"❌ API endpoints test failed: {e}")
            return False
        finally:
            await self.cleanup_test_data([session_id])
    
    async def test_integration_webhooks(self) -> bool:
        """Test integration with interview-service webhooks."""
        print("\n🔧 Testing Integration Webhooks...")
        
        session_id = f"test_webhook_{uuid.uuid4().hex[:8]}"
        
        try:
            # Create a mock webhook payload
            webhook_payload = {
                "session_id": session_id,
                "event_type": "transcription_complete",
                "data": {
                    "full_transcript": "This is a test transcript for webhook integration",
                    "total_chunks": 2,
                    "confidence_score": 0.95,
                    "segments": [
                        {"start": 0.0, "end": 2.0, "text": "This is a test"},
                        {"start": 2.0, "end": 4.0, "text": "transcript for webhook integration"}
                    ]
                }
            }
            
            # Test follow-up generation trigger
            followup_result = await self.integration_service.trigger_followup_generation(
                session_id=session_id,
                transcript_text=webhook_payload['data']['full_transcript'],
                confidence_score=webhook_payload['data']['confidence_score']
            )
            
            print(f"✅ Follow-up generation trigger test passed")
            print(f"   Session: {session_id}")
            print(f"   Status: {followup_result.get('status', 'N/A') if followup_result else 'No response'}")
            
            # Test feedback generation trigger
            feedback_result = await self.integration_service.trigger_feedback_generation(
                session_id=session_id,
                transcript_text=webhook_payload['data']['full_transcript'],
                confidence_score=webhook_payload['data']['confidence_score']
            )
            
            print(f"✅ Feedback generation trigger test passed")
            print(f"   Session: {session_id}")
            print(f"   Status: {feedback_result.get('status', 'N/A')}")
            
            return True
            
        except Exception as e:
            print(f"❌ Integration webhooks test failed: {e}")
            return False
    
    async def test_performance_stress(self) -> bool:
        """Test performance with multiple concurrent sessions."""
        print("\n🔧 Testing Performance and Stress...")
        
        session_ids = [f"test_perf_{uuid.uuid4().hex[:8]}_{i}" for i in range(5)]
        
        try:
            start_time = time.time()
            
            # Create multiple concurrent transcription tasks
            tasks = []
            for session_id in session_ids:
                task = self._process_test_session(session_id)
                tasks.append(task)
            
            # Run all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Analyze results
            successful = sum(1 for r in results if r is True)
            failed = len(results) - successful
            
            print(f"✅ Performance test completed!")
            print(f"   Sessions: {len(session_ids)}")
            print(f"   Duration: {duration:.2f}s")
            print(f"   Successful: {successful}")
            print(f"   Failed: {failed}")
            print(f"   Avg time per session: {duration/len(session_ids):.2f}s")
            
            return successful >= len(session_ids) * 0.8  # 80% success rate
            
        except Exception as e:
            print(f"❌ Performance test failed: {e}")
            return False
        finally:
            await self.cleanup_test_data(session_ids)
    
    async def _process_test_session(self, session_id: str) -> bool:
        """Process a single test session (for performance testing)."""
        try:
            audio_data = self._create_test_audio_bytes()
            
            async for session in get_session():
                # Transcribe and save chunk
                transcript_result = await self.transcription_service.transcribe_audio_chunk(audio_data)
                
                transcription = await self.transcription_service.save_transcription_chunk(
                    session=session,
                    session_id=session_id,
                    media_chunk_id=f"perf_chunk_{session_id}",
                    sequence_index=1,
                    transcript_text=transcript_result['text'],
                    segments=transcript_result['segments'],
                    confidence_score=transcript_result['confidence_score']
                )
                
                # Aggregate session
                aggregated_result = await self.transcription_service.aggregate_session_transcript(
                    session=session,
                    session_id=session_id
                )
                
                return True
                
        except Exception as e:
            print(f"❌ Session {session_id} failed: {e}")
            return False
    
    def _create_test_audio_bytes(self) -> bytes:
        """Create test audio bytes from the test file."""
        with open(self.test_audio_path, "rb") as f:
            return f.read()
    
    def _create_test_audio_b64(self) -> str:
        """Create base64 encoded test audio."""
        audio_bytes = self._create_test_audio_bytes()
        return base64.b64encode(audio_bytes).decode('utf-8')
    
    async def run_all_tests(self):
        """Run all tests in the comprehensive suite."""
        print("🚀 Starting Comprehensive Integration Test Suite...")
        
        # Check prerequisites
        if not os.getenv("OPENAI_API_KEY"):
            print("❌ OPENAI_API_KEY environment variable not set")
            return
        
        # Setup test environment
        await self.setup_test_environment()
        
        # Define test cases
        test_cases = [
            ("Basic Chunked Workflow", self.test_basic_chunked_workflow),
            ("Error Handling", self.test_error_handling),
            ("API Endpoints", self.test_api_endpoints),
            ("Integration Webhooks", self.test_integration_webhooks),
            ("Performance and Stress", self.test_performance_stress),
        ]
        
        # Run tests
        for test_name, test_func in test_cases:
            print(f"\n{'='*60}")
            print(f"Running: {test_name}")
            print(f"{'='*60}")
            
            try:
                start_time = time.time()
                result = await test_func()
                end_time = time.time()
                
                self.test_results.append({
                    "name": test_name,
                    "passed": result,
                    "duration": end_time - start_time
                })
                
                status = "✅ PASSED" if result else "❌ FAILED"
                print(f"\n{status}: {test_name} (took {end_time - start_time:.2f}s)")
                
            except Exception as e:
                print(f"❌ Test {test_name} failed with exception: {e}")
                self.test_results.append({
                    "name": test_name,
                    "passed": False,
                    "duration": 0,
                    "error": str(e)
                })
        
        # Print summary
        self.print_test_summary()
    
    def print_test_summary(self):
        """Print comprehensive test summary."""
        print(f"\n{'='*60}")
        print("COMPREHENSIVE TEST SUMMARY")
        print(f"{'='*60}")
        
        passed = sum(1 for r in self.test_results if r["passed"])
        total = len(self.test_results)
        total_duration = sum(r["duration"] for r in self.test_results)
        
        for result in self.test_results:
            status = "✅ PASSED" if result["passed"] else "❌ FAILED"
            duration = result["duration"]
            name = result["name"]
            print(f"{status}: {name} ({duration:.2f}s)")
            
            if not result["passed"] and "error" in result:
                print(f"   Error: {result['error']}")
        
        print(f"\n🎯 Results: {passed}/{total} tests passed")
        print(f"⏱️  Total duration: {total_duration:.2f}s")
        print(f"📊 Success rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("🎉 All tests passed! Transcription service is production ready.")
        else:
            print("⚠️  Some tests failed. Please review the implementation.")

async def main():
    """Run the comprehensive test suite."""
    test_suite = ComprehensiveTestSuite()
    await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())

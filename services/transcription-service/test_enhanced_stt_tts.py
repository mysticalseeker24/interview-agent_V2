#!/usr/bin/env python3

"""
Comprehensive Test for Enhanced STT and TTS functionality

This script tests:
1. Enhanced Speech-to-Text with better word detection
2. Text-to-Speech with caching and database storage
3. Integration between STT and TTS
4. Performance and accuracy measurements
5. Various audio scenarios and edge cases
"""

import asyncio
import json
import time
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session, engine
from app.services.transcription_service import TranscriptionService
from app.services.tts_service import TTSService
from app.schemas.transcription import TTSRequestIn
from app.models.transcription import Base

class EnhancedSTTTTSTest:
    """Comprehensive testing for enhanced STT and TTS functionality."""
    
    def __init__(self):
        self.transcription_service = TranscriptionService()
        self.tts_service = TTSService()
        self.test_results = []
        self.performance_metrics = {}
        
    async def setup_database(self):
        """Initialize database tables."""
        async with engine.begin() as conn:
            # Create all tables including new TTS table
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Database tables created/verified")
    
    async def test_enhanced_stt_accuracy(self):
        """Test enhanced STT with various speech scenarios."""
        print("\n🎤 Testing Enhanced Speech-to-Text Accuracy")
        print("=" * 60)
        
        test_scenarios = [
            {
                "name": "Technical Interview Response",
                "description": "Testing technical vocabulary recognition",
                "instructions": "Say: 'I implemented microservices using Docker and Kubernetes with CI/CD pipelines'"
            },
            {
                "name": "Company Names",
                "description": "Testing proper noun recognition",
                "instructions": "Say: 'I worked at Google, Microsoft, and Amazon Web Services'"
            },
            {
                "name": "Short Response",
                "description": "Testing brief answers",
                "instructions": "Say: 'Yes, exactly'"
            },
            {
                "name": "Complex Technical Terms",
                "description": "Testing advanced technical vocabulary",
                "instructions": "Say: 'I used TensorFlow and PyTorch for machine learning model training and deployment'"
            },
            {
                "name": "Conversational Filler",
                "description": "Testing natural speech patterns",
                "instructions": "Say: 'Well, um, I think the main challenge was, you know, optimizing the algorithm'"
            }
        ]
        
        stt_results = []
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n--- Test {i}: {scenario['name']} ---")
            print(f"📝 {scenario['description']}")
            print(f"🗣️ {scenario['instructions']}")
            
            input("Press Enter when ready to speak...")
            
            try:
                # Record and transcribe with timing
                start_time = time.time()
                audio_data = await self.transcription_service.record_audio()
                record_time = time.time() - start_time
                
                start_time = time.time()
                result = await self.transcription_service.transcribe_audio_chunk(audio_data)
                transcribe_time = time.time() - start_time
                
                # Analyze results
                transcript = result.get('text', '')
                confidence = result.get('confidence_score', 0)
                segments = result.get('segments', [])
                words = result.get('words', [])
                
                test_result = {
                    "scenario": scenario['name'],
                    "transcript": transcript,
                    "confidence": confidence,
                    "segment_count": len(segments),
                    "word_count": len(words),
                    "recording_time": record_time,
                    "transcription_time": transcribe_time,
                    "enhanced_features": result.get('enhanced_settings', False),
                    "language": result.get('language', 'unknown')
                }
                
                stt_results.append(test_result)
                
                print(f"✅ Transcript: '{transcript}'")
                print(f"📊 Confidence: {confidence:.3f}")
                print(f"🔢 Segments: {len(segments)}, Words: {len(words)}")
                print(f"⏱️ Record: {record_time:.2f}s, Transcribe: {transcribe_time:.2f}s")
                
                if confidence < 0.5:
                    print("⚠️ Low confidence - consider re-recording")
                
            except Exception as e:
                print(f"❌ Error in scenario '{scenario['name']}': {e}")
                stt_results.append({
                    "scenario": scenario['name'],
                    "error": str(e),
                    "success": False
                })
        
        self.test_results.append({"test_type": "enhanced_stt", "results": stt_results})
        
        # Calculate STT metrics
        successful_tests = [r for r in stt_results if 'error' not in r]
        if successful_tests:
            avg_confidence = sum(r['confidence'] for r in successful_tests) / len(successful_tests)
            avg_transcribe_time = sum(r['transcription_time'] for r in successful_tests) / len(successful_tests)
            
            print(f"\n📊 STT Performance Summary:")
            print(f"   Success Rate: {len(successful_tests)}/{len(stt_results)} ({len(successful_tests)/len(stt_results)*100:.1f}%)")
            print(f"   Average Confidence: {avg_confidence:.3f}")
            print(f"   Average Transcription Time: {avg_transcribe_time:.2f}s")
            
            self.performance_metrics['stt'] = {
                "success_rate": len(successful_tests) / len(stt_results),
                "average_confidence": avg_confidence,
                "average_transcription_time": avg_transcribe_time
            }
    
    async def test_tts_functionality(self, session: AsyncSession):
        """Test TTS generation with various scenarios."""
        print("\n🔊 Testing Text-to-Speech Functionality")
        print("=" * 60)
        
        tts_test_cases = [
            {
                "name": "Short Technical Question",
                "text": "Can you explain your experience with Python?",
                "voice": "alloy",
                "format": "mp3"
            },
            {
                "name": "Long Technical Question",
                "text": "Tell me about a complex software architecture you designed. What were the key components, how did they interact, and what challenges did you face during implementation?",
                "voice": "echo",
                "format": "mp3"
            },
            {
                "name": "Behavioral Question",
                "text": "Describe a time when you had to work with a difficult team member. How did you handle the situation?",
                "voice": "nova",
                "format": "mp3"
            },
            {
                "name": "Follow-up Question",
                "text": "That's interesting. Can you elaborate on the specific technologies you used?",
                "voice": "fable",
                "format": "mp3"
            },
            {
                "name": "Technical Deep Dive",
                "text": "How would you optimize a database query that's running slowly? Walk me through your debugging process.",
                "voice": "shimmer",
                "format": "mp3"
            }
        ]
        
        tts_results = []
        
        for i, test_case in enumerate(tts_test_cases, 1):
            print(f"\n--- TTS Test {i}: {test_case['name']} ---")
            print(f"📝 Text: '{test_case['text'][:80]}...'")
            print(f"🎭 Voice: {test_case['voice']}")
            
            try:
                start_time = time.time()
                
                # Create TTS request
                request = TTSRequestIn(
                    text=test_case['text'],
                    voice=test_case['voice'],
                    format=test_case['format']
                )
                
                # Generate TTS
                result = await self.tts_service.generate_tts(session, request)
                
                generation_time = time.time() - start_time
                
                test_result = {
                    "test_case": test_case['name'],
                    "text_length": len(test_case['text']),
                    "voice": test_case['voice'],
                    "format": test_case['format'],
                    "generation_time": generation_time,
                    "file_size": result.file_size,
                    "duration": result.duration,
                    "file_path": result.file_path,
                    "success": True
                }
                
                tts_results.append(test_result)
                
                print(f"✅ Generated: {result.file_path}")
                print(f"📊 Size: {result.file_size} bytes, Duration: {result.duration:.1f}s")
                print(f"⏱️ Generation Time: {generation_time:.2f}s")
                
                # Test file existence
                file_path = Path(result.file_path)
                if file_path.exists():
                    print(f"✅ File exists and accessible")
                else:
                    print(f"❌ File not found at {file_path}")
                
            except Exception as e:
                print(f"❌ Error generating TTS: {e}")
                tts_results.append({
                    "test_case": test_case['name'],
                    "error": str(e),
                    "success": False
                })
        
        self.test_results.append({"test_type": "tts_generation", "results": tts_results})
        
        # Calculate TTS metrics
        successful_tts = [r for r in tts_results if r.get('success', False)]
        if successful_tts:
            avg_generation_time = sum(r['generation_time'] for r in successful_tts) / len(successful_tts)
            total_file_size = sum(r['file_size'] for r in successful_tts)
            total_duration = sum(r['duration'] for r in successful_tts)
            
            print(f"\n📊 TTS Performance Summary:")
            print(f"   Success Rate: {len(successful_tts)}/{len(tts_results)} ({len(successful_tts)/len(tts_results)*100:.1f}%)")
            print(f"   Average Generation Time: {avg_generation_time:.2f}s")
            print(f"   Total File Size: {total_file_size:,} bytes")
            print(f"   Total Audio Duration: {total_duration:.1f}s")
            
            self.performance_metrics['tts'] = {
                "success_rate": len(successful_tts) / len(tts_results),
                "average_generation_time": avg_generation_time,
                "total_file_size": total_file_size,
                "total_duration": total_duration
            }
    
    async def test_tts_caching(self, session: AsyncSession):
        """Test TTS caching functionality."""
        print("\n🗄️ Testing TTS Caching")
        print("=" * 60)
        
        cache_test_text = "This is a test message for caching functionality."
        
        # First generation (cache miss)
        print("🔄 First generation (cache miss)...")
        start_time = time.time()
        request1 = TTSRequestIn(text=cache_test_text, voice="alloy", format="mp3")
        result1 = await self.tts_service.generate_tts(session, request1)
        first_gen_time = time.time() - start_time
        
        # Second generation (cache hit)
        print("🔄 Second generation (cache hit)...")
        start_time = time.time()
        request2 = TTSRequestIn(text=cache_test_text, voice="alloy", format="mp3")
        result2 = await self.tts_service.generate_tts(session, request2)
        second_gen_time = time.time() - start_time
        
        # Verify caching worked
        cache_worked = result1.file_path == result2.file_path and second_gen_time < first_gen_time
        
        print(f"✅ First generation: {first_gen_time:.3f}s")
        print(f"✅ Second generation: {second_gen_time:.3f}s")
        print(f"🎯 Cache {'WORKED' if cache_worked else 'FAILED'}")
        print(f"⚡ Speed improvement: {((first_gen_time - second_gen_time) / first_gen_time * 100):.1f}%")
        
        # Get cache stats
        cache_stats = await self.tts_service.get_cache_stats(session)
        print(f"\n📊 Cache Statistics:")
        for key, value in cache_stats.items():
            print(f"   {key}: {value}")
        
        self.performance_metrics['caching'] = {
            "cache_worked": cache_worked,
            "first_generation_time": first_gen_time,
            "second_generation_time": second_gen_time,
            "speed_improvement": (first_gen_time - second_gen_time) / first_gen_time
        }
    
    async def test_integrated_conversation(self, session: AsyncSession):
        """Test integrated STT + TTS conversation flow."""
        print("\n💬 Testing Integrated STT + TTS Conversation")
        print("=" * 60)
        
        conversation_prompts = [
            "Hello! Please introduce yourself.",
            "What programming languages do you specialize in?",
            "Thank you for that information."
        ]
        
        conversation_results = []
        
        for i, prompt in enumerate(conversation_prompts, 1):
            print(f"\n--- Conversation Turn {i} ---")
            
            # Generate TTS for prompt
            print(f"🤖 AI: {prompt}")
            tts_result = await self.tts_service.generate_tts(
                session=session,
                text=prompt,
                voice="alloy",
                format="mp3"
            )
            print(f"🔊 TTS generated: {tts_result.file_path}")
            
            # Wait for user response
            print("🎤 Your turn to speak...")
            input("Press Enter when ready to speak...")
            
            # Capture STT
            try:
                audio_data = await self.transcription_service.record_audio()
                stt_result = await self.transcription_service.transcribe_audio_chunk(audio_data)
                
                conversation_turn = {
                    "turn": i,
                    "ai_prompt": prompt,
                    "tts_file": tts_result.file_path,
                    "user_response": stt_result.get('text', ''),
                    "confidence": stt_result.get('confidence_score', 0),
                    "success": True
                }
                
                print(f"✅ You said: '{conversation_turn['user_response']}'")
                print(f"📊 Confidence: {conversation_turn['confidence']:.3f}")
                
            except Exception as e:
                conversation_turn = {
                    "turn": i,
                    "ai_prompt": prompt,
                    "error": str(e),
                    "success": False
                }
                print(f"❌ Error: {e}")
            
            conversation_results.append(conversation_turn)
            
            if i < len(conversation_prompts):
                print("\nContinuing to next turn...")
                time.sleep(1)
        
        self.test_results.append({"test_type": "integrated_conversation", "results": conversation_results})
        
        successful_turns = [r for r in conversation_results if r.get('success', False)]
        print(f"\n📊 Conversation Summary:")
        print(f"   Successful turns: {len(successful_turns)}/{len(conversation_results)}")
        if successful_turns:
            avg_confidence = sum(r['confidence'] for r in successful_turns) / len(successful_turns)
            print(f"   Average confidence: {avg_confidence:.3f}")
    
    def generate_test_report(self):
        """Generate comprehensive test report."""
        print("\n📋 COMPREHENSIVE TEST REPORT")
        print("=" * 80)
        
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        report = {
            "test_timestamp": timestamp,
            "test_results": self.test_results,
            "performance_metrics": self.performance_metrics,
            "summary": {}
        }
        
        # Calculate overall metrics
        total_tests = sum(len(test_group['results']) for test_group in self.test_results)
        successful_tests = 0
        
        for test_group in self.test_results:
            for result in test_group['results']:
                if result.get('success', True) and 'error' not in result:
                    successful_tests += 1
        
        report['summary'] = {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": successful_tests / total_tests if total_tests > 0 else 0,
            "features_tested": ["enhanced_stt", "tts_generation", "caching", "integration"]
        }
        
        # Save report
        report_file = f"enhanced_stt_tts_test_report_{int(time.time())}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"📊 Overall Test Results:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Successful: {successful_tests}")
        print(f"   Success Rate: {report['summary']['success_rate']*100:.1f}%")
        print(f"\n💾 Detailed report saved to: {report_file}")
        
        # Performance highlights
        if 'stt' in self.performance_metrics:
            stt_metrics = self.performance_metrics['stt']
            print(f"\n🎤 STT Performance:")
            print(f"   Avg Confidence: {stt_metrics['average_confidence']:.3f}")
            print(f"   Avg Speed: {stt_metrics['average_transcription_time']:.2f}s")
        
        if 'tts' in self.performance_metrics:
            tts_metrics = self.performance_metrics['tts']
            print(f"\n🔊 TTS Performance:")
            print(f"   Avg Generation: {tts_metrics['average_generation_time']:.2f}s")
            print(f"   Total Duration: {tts_metrics['total_duration']:.1f}s")
        
        if 'caching' in self.performance_metrics:
            cache_metrics = self.performance_metrics['caching']
            print(f"\n🗄️ Caching Performance:")
            print(f"   Cache Working: {'✅' if cache_metrics['cache_worked'] else '❌'}")
            print(f"   Speed Improvement: {cache_metrics['speed_improvement']*100:.1f}%")

async def main():
    """Main test execution function."""
    print("🚀 Enhanced STT and TTS Comprehensive Test Suite")
    print("=" * 80)
    print("This test will evaluate:")
    print("✅ Enhanced Speech-to-Text accuracy and responsiveness")
    print("✅ Text-to-Speech generation and caching")
    print("✅ Database integration and persistence")
    print("✅ Integrated conversation flow")
    print("=" * 80)
    
    test_suite = EnhancedSTTTTSTest()
    
    try:
        # Setup
        await test_suite.setup_database()
        
        # Get database session
        async for session in get_session():
            # Run all tests
            await test_suite.test_enhanced_stt_accuracy()
            await test_suite.test_tts_functionality(session)
            await test_suite.test_tts_caching(session)
            await test_suite.test_integrated_conversation(session)
            break
        
        # Generate report
        test_suite.generate_test_report()
        
        print("\n🎉 All tests completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        raise

if __name__ == "__main__":
    print("🎤🔊 Enhanced STT/TTS Test Suite Starting...")
    asyncio.run(main())

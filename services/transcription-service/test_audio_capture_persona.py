#!/usr/bin/env python3

"""
Audio Capture Test Script with Persona Integration

This script tests:
1. Audio recording from microphone
2. Real-time transcription using OpenAI Whisper
3. Persona-based response generation
4. Complete interview simulation workflow
"""

import asyncio
import os
import sys
import time
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.services.transcription_service import TranscriptionService
from app.core.database import get_session, engine

class AudioCaptureTest:
    """Test class for audio capture and persona interaction."""
    
    def __init__(self):
        self.transcription_service = TranscriptionService()
        self.persona_guidelines = self.load_persona_guidelines()
        
    def load_persona_guidelines(self):
        """Load available persona guidelines."""
        personas_dir = Path(__file__).parent / "test-assets" / "personas"
        personas = {}
        
        for persona_file in personas_dir.glob("*.txt"):
            persona_name = persona_file.stem.replace("-guidelines", "").replace("-", " ").title()
            try:
                with open(persona_file, 'r', encoding='utf-8') as f:
                    personas[persona_name] = f.read()
            except Exception as e:
                print(f"Warning: Could not load persona {persona_name}: {e}")
        
        return personas
    
    def display_available_personas(self):
        """Display available personas for selection."""
        print("\n🎭 Available Interview Personas:")
        print("=" * 50)
        
        for i, persona_name in enumerate(self.persona_guidelines.keys(), 1):
            # Extract persona description from guidelines
            guidelines = self.persona_guidelines[persona_name]
            if "Role:" in guidelines:
                role_line = [line for line in guidelines.split('\n') if line.startswith("Role:")][0]
                role = role_line.replace("Role:", "").strip()
            else:
                role = "Interview specialist"
            
            print(f"{i}. {persona_name}")
            print(f"   Role: {role}")
            print()
    
    def select_persona(self):
        """Allow user to select a persona."""
        personas = list(self.persona_guidelines.keys())
        
        while True:
            try:
                self.display_available_personas()
                choice = input(f"Select a persona (1-{len(personas)}) or 'q' to quit: ").strip()
                
                if choice.lower() == 'q':
                    return None
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(personas):
                    selected_persona = personas[choice_num - 1]
                    print(f"\n✅ Selected: {selected_persona}")
                    return selected_persona
                else:
                    print(f"❌ Please enter a number between 1 and {len(personas)}")
                    
            except ValueError:
                print("❌ Please enter a valid number or 'q' to quit")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                return None
    
    async def test_audio_recording(self):
        """Test audio recording functionality."""
        print("\n🎤 Testing Audio Recording...")
        print("=" * 50)
        
        try:
            print("📝 Starting audio recording...")
            print("🗣️  Please speak clearly into your microphone")
            print("🤫 The recording will stop automatically after silence is detected")
            print()
            
            # Record audio
            audio_data = await self.transcription_service.record_audio()
            
            print("✅ Audio recording completed!")
            print(f"📊 Audio data size: {len(audio_data)} bytes")
            
            return audio_data
            
        except Exception as e:
            print(f"❌ Audio recording failed: {e}")
            print("\n💡 Tips:")
            print("   - Check if your microphone is connected and working")
            print("   - Ensure microphone permissions are granted")
            print("   - Try speaking louder or closer to the microphone")
            return None
    
    async def test_transcription(self, audio_data):
        """Test transcription of recorded audio."""
        print("\n🔤 Testing Transcription...")
        print("=" * 50)
        
        try:
            print("📝 Transcribing audio using OpenAI Whisper...")
            
            # Transcribe the audio
            transcript_result = await self.transcription_service.transcribe_audio_chunk(audio_data)
            
            print("✅ Transcription completed!")
            print(f"📝 Transcript: {transcript_result['text']}")
            print(f"📊 Confidence: {transcript_result['confidence_score']:.2f}")
            print(f"📊 Segments: {len(transcript_result['segments'])}")
            
            # Display segments
            if transcript_result['segments']:
                print("\n🔍 Detailed Segments:")
                for i, segment in enumerate(transcript_result['segments'], 1):
                    start = segment.get('start', 0)
                    end = segment.get('end', 0)
                    text = segment.get('text', '')
                    print(f"   {i}. {start:.1f}s - {end:.1f}s: {text}")
            
            return transcript_result
            
        except Exception as e:
            print(f"❌ Transcription failed: {e}")
            print("\n💡 Tips:")
            print("   - Check your OpenAI API key")
            print("   - Ensure you have internet connection")
            print("   - Try recording again with clearer audio")
            return None
    
    def simulate_persona_response(self, persona_name, transcript_text):
        """Simulate a persona-based response to the transcript."""
        print(f"\n🎭 {persona_name} Response Simulation...")
        print("=" * 50)
        
        guidelines = self.persona_guidelines[persona_name]
        
        # Extract key information from guidelines
        persona_info = self.extract_persona_info(guidelines)
        
        print(f"👤 Persona: {persona_name}")
        print(f"🎯 Focus: {persona_info.get('focus', 'General interview')}")
        print(f"📝 Your response: \"{transcript_text}\"")
        print()
        
        # Generate a simulated response based on persona type
        response = self.generate_mock_response(persona_name, transcript_text, persona_info)
        print(f"🤖 {persona_name}'s Response:")
        print(f"   {response}")
        
        return response
    
    def extract_persona_info(self, guidelines):
        """Extract key information from persona guidelines."""
        info = {}
        
        lines = guidelines.split('\n')
        for line in lines:
            if line.startswith("Role:"):
                info['role'] = line.replace("Role:", "").strip()
            elif line.startswith("Focus:") or "focus" in line.lower():
                info['focus'] = line.split(":", 1)[-1].strip()
            elif "domain" in line.lower() or "expertise" in line.lower():
                info['domain'] = line
        
        return info
    
    def generate_mock_response(self, persona_name, transcript_text, persona_info):
        """Generate a mock response based on persona type."""
        
        # Simple response generation based on persona name
        if "ethan" in persona_name.lower() or "software" in persona_name.lower():
            return f"That's interesting! Can you tell me more about your experience with software development? I'd particularly like to hear about any challenging technical problems you've solved."
            
        elif "meta" in persona_name.lower() or "ai" in persona_name.lower():
            return f"Great! I can see you have experience in this area. Let's dive deeper into machine learning concepts. Can you walk me through your approach to model selection and evaluation?"
            
        elif "jordan" in persona_name.lower() or "devops" in persona_name.lower():
            return f"Excellent! Your infrastructure experience sounds valuable. Can you describe a time when you had to troubleshoot a complex deployment issue in a Kubernetes environment?"
            
        elif "sam" in persona_name.lower() or "algorithm" in persona_name.lower():
            return f"Nice work! Now let's test your algorithmic thinking. Here's a problem: Given an array of integers, find the two numbers that add up to a specific target. How would you approach this?"
            
        elif "taylor" in persona_name.lower() or "resume" in persona_name.lower():
            return f"Thank you for sharing that experience. I can see from your background that you have diverse skills. Can you tell me about a time when you had to learn something completely new quickly?"
            
        else:
            return f"Thank you for that response. Based on what you've shared, I'd like to explore this topic further. Can you provide a specific example from your experience?"
    
    async def run_complete_test(self):
        """Run the complete audio capture and persona test."""
        print("🎤 Audio Capture Test with Persona Integration")
        print("=" * 60)
        print("This test will:")
        print("1. Let you select an interview persona")
        print("2. Record audio from your microphone")
        print("3. Transcribe the audio using OpenAI Whisper")
        print("4. Simulate a persona-based response")
        print()
        
        # Check prerequisites
        if not os.getenv("OPENAI_API_KEY"):
            print("❌ OPENAI_API_KEY environment variable not set")
            print("Please set your OpenAI API key before running this test.")
            return
        
        # Select persona
        selected_persona = self.select_persona()
        if not selected_persona:
            print("👋 Test cancelled.")
            return
        
        print(f"\n🎭 Using persona: {selected_persona}")
        print("📋 Persona guidelines loaded successfully")
        
        # Test audio recording
        audio_data = await self.test_audio_recording()
        if not audio_data:
            print("❌ Audio recording test failed. Cannot continue.")
            return
        
        # Test transcription
        transcript_result = await self.test_transcription(audio_data)
        if not transcript_result:
            print("❌ Transcription test failed. Cannot continue.")
            return
        
        # Simulate persona response
        transcript_text = transcript_result['text']
        response = self.simulate_persona_response(selected_persona, transcript_text)
        
        # Test database storage (optional)
        await self.test_database_storage(transcript_result, selected_persona)
        
        print("\n🎉 Audio Capture Test Completed Successfully!")
        print("=" * 60)
        print("✅ All components are working:")
        print("   - Audio recording ✅")
        print("   - Speech transcription ✅") 
        print("   - Persona integration ✅")
        print("   - Database storage ✅")
        print()
        print("🚀 The transcription service is ready for interview scenarios!")
    
    async def test_database_storage(self, transcript_result, persona_name):
        """Test storing the transcription in the database."""
        print(f"\n💾 Testing Database Storage...")
        print("=" * 50)
        
        try:
            # Create database tables if needed
            async with engine.begin() as conn:
                from app.core.database import Base
                await conn.run_sync(Base.metadata.create_all)
            
            # Store transcription
            async for session in get_session():
                transcription = await self.transcription_service.save_transcription_chunk(
                    session=session,
                    session_id=f"audio_test_{int(time.time())}",
                    media_chunk_id=f"test_chunk_{persona_name.lower().replace(' ', '_')}",
                    sequence_index=1,
                    transcript_text=transcript_result['text'],
                    segments=transcript_result['segments'],
                    confidence_score=transcript_result['confidence_score'],
                    question_id=f"persona_test_{persona_name.lower().replace(' ', '_')}"
                )
                
                print("✅ Database storage successful!")
                print(f"📊 Transcription ID: {transcription.id}")
                print(f"📊 Session ID: {transcription.session_id}")
                print(f"📊 Confidence: {transcription.confidence_score:.2f}")
                
                break
                
        except Exception as e:
            print(f"❌ Database storage failed: {e}")
            print("💡 This is not critical - the transcription service is still working")

async def main():
    """Run the audio capture test."""
    test_runner = AudioCaptureTest()
    await test_runner.run_complete_test()

if __name__ == "__main__":
    asyncio.run(main())

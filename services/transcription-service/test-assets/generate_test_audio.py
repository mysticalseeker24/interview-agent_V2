#!/usr/bin/env python3

"""
Test audio generator for creating synthetic audio samples for testing.

This utility can generate:
1. Synthetic audio with text-to-speech
2. Audio chunks of different durations
3. Multi-speaker audio scenarios
4. Audio with varying quality/noise levels
"""

import os
import sys
from pathlib import Path
from typing import Optional

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

def create_synthetic_audio_with_tts(
    text: str, 
    output_path: str,
    voice: str = "alloy"
) -> bool:
    """
    Create synthetic audio using OpenAI TTS for testing.
    
    Args:
        text: Text to convert to speech
        output_path: Output audio file path
        voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        from openai import OpenAI
        from app.core.config import settings
        
        client = OpenAI(api_key=settings.openai_api_key)
        
        # Generate speech
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )
        
        # Save to file
        with open(output_path, "wb") as f:
            f.write(response.content)
        
        print(f"✅ Created synthetic audio: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating synthetic audio: {e}")
        return False

def create_test_audio_samples():
    """Create a variety of test audio samples for testing."""
    
    audio_dir = Path(__file__).parent / "audio"
    audio_dir.mkdir(exist_ok=True)
    
    # Test scenarios
    test_samples = [
        {
            "name": "short_answer.mp3",
            "text": "Yes, I have experience with Python and JavaScript.",
            "voice": "alloy"
        },
        {
            "name": "technical_answer.mp3", 
            "text": "I implemented a RESTful API using FastAPI with SQLAlchemy for the ORM. The service handles user authentication through JWT tokens and integrates with a PostgreSQL database for persistence.",
            "voice": "echo"
        },
        {
            "name": "behavioral_answer.mp3",
            "text": "When I faced a challenging deadline, I first broke down the project into smaller tasks, prioritized the critical components, and communicated with my team about the timeline. We managed to deliver on time by focusing on the MVP features first.",
            "voice": "nova"
        },
        {
            "name": "follow_up_response.mp3",
            "text": "That's a great question. In that specific case, I used React hooks for state management, particularly useState and useEffect. I also implemented custom hooks to encapsulate reusable logic across components.",
            "voice": "fable"
        },
        {
            "name": "clarification.mp3",
            "text": "Could you please clarify what aspect of the architecture you'd like me to focus on? Are you interested in the database design, the API structure, or the frontend implementation?",
            "voice": "shimmer"
        }
    ]
    
    print("🎤 Creating test audio samples...")
    
    success_count = 0
    for sample in test_samples:
        output_path = audio_dir / sample["name"]
        
        if create_synthetic_audio_with_tts(
            text=sample["text"],
            output_path=str(output_path),
            voice=sample["voice"]
        ):
            success_count += 1
    
    print(f"\n✅ Created {success_count}/{len(test_samples)} test audio samples")
    
    return success_count == len(test_samples)

def create_chunked_audio_scenario():
    """Create a scenario with multiple audio chunks for session testing."""
    
    audio_dir = Path(__file__).parent / "audio"
    
    # Multi-chunk interview scenario
    interview_chunks = [
        {
            "name": "chunk_01_intro.mp3",
            "text": "Hi, I'm excited to be here today. I'm a software engineer with five years of experience in full-stack development.",
            "voice": "alloy"
        },
        {
            "name": "chunk_02_experience.mp3", 
            "text": "I've worked primarily with Python, JavaScript, and React. I've built several web applications using Django and FastAPI for the backend.",
            "voice": "alloy"
        },
        {
            "name": "chunk_03_projects.mp3",
            "text": "One of my key projects was developing a real-time analytics dashboard for our e-commerce platform. It processed over 10,000 transactions per minute.",
            "voice": "alloy"
        },
        {
            "name": "chunk_04_challenges.mp3",
            "text": "The biggest challenge was optimizing the database queries and implementing efficient caching strategies to handle the high volume of data.",
            "voice": "alloy"
        },
        {
            "name": "chunk_05_solution.mp3",
            "text": "I solved this by implementing Redis for caching, optimizing our SQL queries, and setting up database indexing. This reduced response times by 60 percent.",
            "voice": "alloy"
        }
    ]
    
    print("🎯 Creating chunked interview scenario...")
    
    success_count = 0
    for chunk in interview_chunks:
        output_path = audio_dir / chunk["name"]
        
        if create_synthetic_audio_with_tts(
            text=chunk["text"],
            output_path=str(output_path),
            voice=chunk["voice"]
        ):
            success_count += 1
    
    print(f"✅ Created {success_count}/{len(interview_chunks)} interview chunks")
    
    return success_count == len(interview_chunks)

def main():
    """Main function to generate test audio samples."""
    
    print("🚀 Test Audio Generator")
    print("=" * 40)
    
    # Check if OpenAI API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key in the .env file")
        return
    
    print("📁 Setting up audio directory...")
    
    # Create various test scenarios
    scenarios = [
        ("General Test Samples", create_test_audio_samples),
        ("Chunked Interview Scenario", create_chunked_audio_scenario)
    ]
    
    results = []
    for scenario_name, scenario_func in scenarios:
        print(f"\n🎬 {scenario_name}")
        print("-" * 30)
        
        try:
            result = scenario_func()
            results.append((scenario_name, result))
        except Exception as e:
            print(f"❌ Error in {scenario_name}: {e}")
            results.append((scenario_name, False))
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 SUMMARY")
    print("=" * 40)
    
    for scenario_name, result in results:
        status = "✅ SUCCESS" if result else "❌ FAILED"
        print(f"{status}: {scenario_name}")
    
    total_success = sum(1 for _, result in results if result)
    print(f"\n🎯 {total_success}/{len(results)} scenarios completed successfully")
    
    if total_success == len(results):
        print("🎉 All test audio samples generated successfully!")
        print("\nYou can now run the transcription tests with:")
        print("python test_chunked_transcription.py")
    else:
        print("⚠️  Some audio generation failed. Check the errors above.")

if __name__ == "__main__":
    main()

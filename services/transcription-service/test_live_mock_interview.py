#!/usr/bin/env python3
"""
Live Mock Interview Test for TalentSync Transcription Service

This script provides an interactive terminal-based interface to test the
transcription service through a mock interview scenario. It simulates:
- Agent asking questions (TTS)
- User responding (STT simulation)
- Persona selection and voice assignment
- Complete interview flow

Usage:
    python test_live_mock_interview.py
"""

import asyncio
import json
import logging
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import httpx
import sounddevice as sd
import soundfile as sf
import numpy as np
from datetime import datetime

# Add the service directory to the path
service_dir = Path(__file__).parent
sys.path.insert(0, str(service_dir))

from app.core.config import settings
from app.services.persona_service import PersonaService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LiveMockInterview:
    """Interactive mock interview system for testing the transcription service."""
    
    def __init__(self):
        self.base_url = f"http://localhost:{settings.port}"
        self.session_id = f"mock_interview_{int(time.time())}"
        self.round_number = 1
        self.persona_service = PersonaService()
        self.selected_persona = None
        self.interview_history = []
        
        # Audio recording settings
        self.sample_rate = 16000
        self.channels = 1
        self.duration = 5  # seconds per recording
        
        # Interview questions by domain
        self.interview_questions = {
            "software-engineering": [
                "Tell me about your experience with full-stack development.",
                "How do you handle debugging complex issues?",
                "What's your approach to code review?",
                "Describe a challenging project you've worked on.",
                "How do you stay updated with new technologies?"
            ],
            "ai-engineering": [
                "What machine learning frameworks are you most comfortable with?",
                "Tell me about a model you've trained from scratch.",
                "How do you handle overfitting in your models?",
                "What's your experience with deployment of ML models?",
                "How do you evaluate model performance?"
            ],
            "devops": [
                "What CI/CD tools have you worked with?",
                "How do you handle infrastructure as code?",
                "Tell me about your experience with containerization.",
                "How do you monitor production systems?",
                "What's your approach to security in DevOps?"
            ],
            "data-analyst": [
                "What data analysis tools do you prefer?",
                "How do you handle missing data in your analysis?",
                "Tell me about a data visualization project.",
                "How do you ensure data quality?",
                "What's your experience with SQL and databases?"
            ],
            "dsa": [
                "What's your favorite data structure and why?",
                "How do you approach algorithm optimization?",
                "Tell me about a time you solved a complex algorithmic problem.",
                "What's your experience with dynamic programming?",
                "How do you analyze time and space complexity?"
            ]
        }
    
    def print_header(self, title: str):
        """Print a formatted header."""
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
    
    def print_info(self, message: str):
        """Print an info message."""
        print(f"ℹ️  {message}")
    
    def print_success(self, message: str):
        """Print a success message."""
        print(f"✅ {message}")
    
    def print_error(self, message: str):
        """Print an error message."""
        print(f"❌ {message}")
    
    def print_warning(self, message: str):
        """Print a warning message."""
        print(f"⚠️  {message}")
    
    async def check_service_health(self) -> bool:
        """Check if the transcription service is running."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                if response.status_code == 200:
                    self.print_success("Transcription service is running")
                    return True
                else:
                    self.print_error(f"Service health check failed: {response.status_code}")
                    return False
        except Exception as e:
            self.print_error(f"Cannot connect to transcription service: {str(e)}")
            return False
    
    def display_personas(self):
        """Display available personas for selection."""
        self.print_header("Available Interviewer Personas")
        
        personas = self.persona_service.get_available_personas()
        
        print("🎭 Select an interviewer persona:")
        print()
        
        persona_options = []
        option_number = 1
        
        for domain, persona_names in personas.items():
            print(f"📁 {domain.upper()}:")
            for persona_name in persona_names:
                persona = self.persona_service.get_persona(domain, persona_name)
                if persona:
                    voice = getattr(persona, 'voice', 'Unknown')
                    print(f"   {option_number}. {persona.name} ({voice})")
                    print(f"      Personality: {persona.personality}")
                    print(f"      Expertise: {', '.join(persona.expertise[:3])}")
                    print()
                    persona_options.append((domain, persona_name, persona))
                    option_number += 1
        
        return persona_options
    
    def select_persona(self) -> Optional[Any]:
        """Let user select a persona."""
        persona_options = self.display_personas()
        
        if not persona_options:
            self.print_error("No personas available")
            return None
        
        while True:
            try:
                choice = input(f"Enter persona number (1-{len(persona_options)}): ").strip()
                choice_num = int(choice)
                
                if 1 <= choice_num <= len(persona_options):
                    domain, persona_name, persona = persona_options[choice_num - 1]
                    self.print_success(f"Selected: {persona.name} ({persona.voice})")
                    return persona
                else:
                    self.print_warning(f"Please enter a number between 1 and {len(persona_options)}")
            except ValueError:
                self.print_warning("Please enter a valid number")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                return None
    
    def get_questions_for_persona(self, persona) -> List[str]:
        """Get appropriate questions for the selected persona."""
        domain = persona.domain
        
        if domain in self.interview_questions:
            return self.interview_questions[domain]
        else:
            # Generic questions for unknown domains
            return [
                "Tell me about your background and experience.",
                "What are your strengths and weaknesses?",
                "Where do you see yourself in 5 years?",
                "Why are you interested in this role?",
                "Do you have any questions for me?"
            ]
    
    async def generate_agent_question_audio(self, question: str, persona) -> Optional[str]:
        """Generate TTS audio for agent question."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                tts_data = {
                    "text": question,
                    "voice": persona.voice
                }
                
                response = await client.post(
                    f"{self.base_url}/api/v1/tts/generate",
                    json=tts_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    audio_url = result.get("file_url")
                    if audio_url:
                        return f"{self.base_url}{audio_url}"
                    else:
                        self.print_error("No audio URL in TTS response")
                        return None
                else:
                    self.print_error(f"TTS generation failed: {response.status_code}")
                    return None
                    
        except Exception as e:
            self.print_error(f"TTS generation error: {str(e)}")
            return None
    
    def record_user_response(self) -> Optional[bytes]:
        """Record user audio response."""
        try:
            self.print_info("🎤 Recording your response... (Press Ctrl+C to stop)")
            self.print_info(f"Recording for {self.duration} seconds...")
            
            # Record audio
            recording = sd.rec(
                int(self.duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=np.int16
            )
            sd.wait()
            
            # Convert to bytes
            audio_bytes = recording.tobytes()
            self.print_success(f"Recorded {len(audio_bytes)} bytes of audio")
            return audio_bytes
            
        except KeyboardInterrupt:
            self.print_warning("Recording stopped by user")
            return None
        except Exception as e:
            self.print_error(f"Recording failed: {str(e)}")
            return None
    
    async def transcribe_user_response(self, audio_bytes: bytes) -> Optional[str]:
        """Transcribe user audio response."""
        try:
            # Create a temporary file for the audio
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                # Write WAV header and audio data
                import struct
                
                # WAV header
                header = struct.pack('<4sI4s4sIHHIIHH4sI',
                    b'RIFF',
                    36 + len(audio_bytes),
                    b'WAVE',
                    b'fmt ',
                    16,  # fmt chunk size
                    1,   # PCM format
                    self.channels,
                    self.sample_rate,
                    self.sample_rate * self.channels * 2,  # byte rate
                    self.channels * 2,  # block align
                    16,  # bits per sample
                    b'data',
                    len(audio_bytes)
                )
                
                temp_file.write(header)
                temp_file.write(audio_bytes)
                temp_file_path = temp_file.name
            
            # Upload and transcribe
            async with httpx.AsyncClient(timeout=30.0) as client:
                with open(temp_file_path, 'rb') as f:
                    files = {'file': ('response.wav', f, 'audio/wav')}
                    data = {
                        'chunk_id': f'chunk_{self.round_number}',
                        'session_id': self.session_id,
                        'sequence_index': self.round_number
                    }
                    
                    response = await client.post(
                        f"{self.base_url}/api/v1/transcribe/",
                        files=files,
                        data=data
                    )
                
                # Clean up temp file
                os.unlink(temp_file_path)
                
                if response.status_code == 200:
                    result = response.json()
                    transcript = result.get("transcript", "")
                    confidence = result.get("confidence", 0.0)
                    
                    self.print_success(f"Transcription: {transcript}")
                    self.print_info(f"Confidence: {confidence:.2f}")
                    
                    return transcript
                else:
                    self.print_error(f"Transcription failed: {response.status_code}")
                    return None
                    
        except Exception as e:
            self.print_error(f"Transcription error: {str(e)}")
            return None
    
    async def generate_agent_reply(self, question: str, user_response: str, persona) -> Optional[str]:
        """Generate agent reply based on user response."""
        try:
            # Simple reply generation based on response length and content
            if len(user_response) < 10:
                reply = "Could you please elaborate on that? I'd like to hear more details about your experience."
            elif "experience" in user_response.lower():
                reply = "That's interesting! Can you tell me about a specific project where you applied that experience?"
            elif "challenge" in user_response.lower() or "problem" in user_response.lower():
                reply = "Great! How did you approach solving that challenge? What was your methodology?"
            elif "technology" in user_response.lower() or "tool" in user_response.lower():
                reply = "Excellent! How do you stay updated with new technologies in your field?"
            else:
                reply = "Thank you for that response. Let me ask you a follow-up question about your technical skills."
            
            return reply
            
        except Exception as e:
            self.print_error(f"Reply generation error: {str(e)}")
            return None
    
    async def play_audio(self, audio_url: str):
        """Play audio from URL."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(audio_url)
                if response.status_code == 200:
                    # Save to temporary file and play
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                        temp_file.write(response.content)
                        temp_file_path = temp_file.name
                    
                    # Play audio
                    data, samplerate = sf.read(temp_file_path)
                    sd.play(data, samplerate)
                    sd.wait()
                    
                    # Clean up
                    os.unlink(temp_file_path)
                    self.print_success("Audio played successfully")
                else:
                    self.print_error(f"Failed to download audio: {response.status_code}")
                    
        except Exception as e:
            self.print_error(f"Audio playback error: {str(e)}")
    
    def simulate_user_response(self) -> str:
        """Simulate user response for testing without microphone."""
        responses = [
        "I have about 5 years of experience in software development, primarily working with Python and JavaScript. I've built several web applications using React and Node.js, and I'm comfortable with both frontend and backend development.",
        "When debugging, I usually start by reproducing the issue and then use logging and debugging tools to trace through the code. I find that systematic debugging helps me identify the root cause more efficiently.",
        "I believe in thorough code reviews that focus on both functionality and maintainability. I always check for potential bugs, code style consistency, and opportunities for improvement.",
        "One of the most challenging projects I worked on was a real-time collaboration tool that required handling concurrent edits and conflict resolution. It taught me a lot about distributed systems.",
        "I stay updated by following tech blogs, participating in online communities, and experimenting with new technologies in side projects. I also attend conferences when possible."
        ]
        
        import random
        return random.choice(responses)
    
    async def conduct_interview_round(self, question: str, persona) -> bool:
        """Conduct one round of the interview."""
        self.print_header(f"Interview Round {self.round_number}")
        
        # Display question
        print(f"🤖 {persona.name}: {question}")
        print()
        
        # Generate and play question audio
        self.print_info("Generating question audio...")
        audio_url = await self.generate_agent_question_audio(question, persona)
        if audio_url:
            self.print_info("Playing question audio...")
            await self.play_audio(audio_url)
        else:
            self.print_warning("Could not generate audio, continuing with text only")
        
        print()
        
        # Get user response
        print("🎤 Your turn to respond:")
        
        # Check if microphone is available
        try:
            response_choice = input("Choose response method:\n1. Record audio (microphone)\n2. Simulate response (for testing)\nEnter choice (1 or 2): ").strip()
            
            if response_choice == "1":
                audio_bytes = self.record_user_response()
                if audio_bytes:
                    user_response = await self.transcribe_user_response(audio_bytes)
                else:
                    self.print_warning("No audio recorded, using simulated response")
                    user_response = self.simulate_user_response()
            else:
                user_response = self.simulate_user_response()
                self.print_info(f"Simulated response: {user_response}")
        except KeyboardInterrupt:
            self.print_warning("Response input cancelled")
            return False
        
        if not user_response:
            self.print_error("No response received")
            return False
        
        print()
        
        # Generate agent reply
        self.print_info("Generating agent reply...")
        agent_reply = await self.generate_agent_reply(question, user_response, persona)
        
        if agent_reply:
            print(f"🤖 {persona.name}: {agent_reply}")
            
            # Generate and play reply audio
            reply_audio_url = await self.generate_agent_question_audio(agent_reply, persona)
            if reply_audio_url:
                self.print_info("Playing reply audio...")
                await self.play_audio(reply_audio_url)
        
        # Store round data
        round_data = {
            "round": self.round_number,
            "question": question,
            "user_response": user_response,
            "agent_reply": agent_reply,
            "timestamp": datetime.now().isoformat()
        }
        self.interview_history.append(round_data)
        
        self.round_number += 1
        return True
    
    async def start_interview(self):
        """Start the interactive mock interview."""
        self.print_header("Live Mock Interview System")
        self.print_info("Welcome to the TalentSync Transcription Service Mock Interview!")
        print()
        
        # Check service health
        if not await self.check_service_health():
            self.print_error("Cannot proceed without transcription service")
            return
        
        # Select persona
        self.selected_persona = self.select_persona()
        if not self.selected_persona:
            return
        
        print()
        self.print_info(f"Interviewer: {self.selected_persona.name}")
        self.print_info(f"Voice: {self.selected_persona.voice}")
        self.print_info(f"Domain: {self.selected_persona.domain}")
        self.print_info(f"Session ID: {self.session_id}")
        print()
        
        # Get questions for the persona
        questions = self.get_questions_for_persona(self.selected_persona)
        
        # Conduct interview rounds
        for i, question in enumerate(questions[:3]):  # Limit to 3 questions for demo
            try:
                success = await self.conduct_interview_round(question, self.selected_persona)
                if not success:
                    break
                
                if i < len(questions) - 1:  # Not the last question
                    continue_choice = input("\nContinue to next question? (y/n): ").strip().lower()
                    if continue_choice != 'y':
                        break
                        
            except KeyboardInterrupt:
                self.print_warning("Interview interrupted by user")
                break
        
        # Interview summary
        await self.show_interview_summary()
    
    async def show_interview_summary(self):
        """Show interview summary and save to file."""
        self.print_header("Interview Summary")
        
        print(f"📊 Total Rounds: {len(self.interview_history)}")
        print(f"🎭 Interviewer: {self.selected_persona.name}")
        print(f"🆔 Session ID: {self.session_id}")
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        for i, round_data in enumerate(self.interview_history, 1):
            print(f"Round {i}:")
            print(f"  Q: {round_data['question']}")
            print(f"  A: {round_data['user_response'][:100]}...")
            if round_data['agent_reply']:
                print(f"  R: {round_data['agent_reply']}")
            print()
        
        # Save interview to file
        summary_file = f"mock_interview_{self.session_id}.json"
        try:
            summary_data = {
                "session_id": self.session_id,
                "persona": {
                    "name": self.selected_persona.name,
                    "domain": self.selected_persona.domain,
                    "voice": self.selected_persona.voice
                },
                "interview_history": self.interview_history,
                "timestamp": datetime.now().isoformat()
            }
            
            with open(summary_file, 'w') as f:
                json.dump(summary_data, f, indent=2)
            
            self.print_success(f"Interview summary saved to: {summary_file}")
            
        except Exception as e:
            self.print_error(f"Failed to save summary: {str(e)}")

async def main():
    """Main function."""
    try:
        # Check dependencies
        try:
            import sounddevice
            import soundfile
            import numpy
        except ImportError as e:
            print("❌ Missing dependencies for audio recording:")
            print("Please install: pip install sounddevice soundfile numpy")
            return
        
        # Start mock interview
        interview = LiveMockInterview()
        await interview.start_interview()
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Mock interview failed: {str(e)}")
        logger.error(f"Mock interview failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 
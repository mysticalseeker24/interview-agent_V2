#!/usr/bin/env python3

"""
Enhanced Interactive AI Interview Conversation System with TTS

This script creates a complete voice-to-voice conversation experience:
- Real-time audio capture and transcription (STT)
- AI persona-driven responses with OpenAI o4-mini
- Text-to-Speech audio playback (TTS)
- Session management and audio file handling
"""

import asyncio
import os
import sys
import time
import threading
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

# Third-party imports
import pygame
from openai import OpenAI

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.services.transcription_service import TranscriptionService
from app.core.database import get_session, engine
from app.core.config import settings

class EnhancedInteractiveInterview:
    """Complete voice-to-voice interview system with TTS support."""
    
    def __init__(self):
        """Initialize the enhanced interview system."""
        self.transcription_service = TranscriptionService()
        self.openai_client = OpenAI(api_key=settings.openai_api_key)
        self.personas = self.load_personas()
        self.conversation_history = []
        self.current_persona = None
        self.session_id = f"voice_interview_{int(time.time())}"
        
        # TTS and audio playback setup
        pygame.mixer.init()
        self.playback_finished = threading.Event()
        self.temp_audio_files = []
        
        print("🎤 Enhanced Interview System Initialized")
        print("✅ Speech-to-Text: OpenAI Whisper")
        print("✅ Text-to-Speech: OpenAI TTS")
        print("✅ AI Conversation: OpenAI o4-mini")
        
    def load_personas(self) -> Dict[str, Dict[str, Any]]:
        """Load and parse persona guidelines from files."""
        personas_dir = Path(__file__).parent / "test-assets" / "personas"
        personas = {}
        
        if not personas_dir.exists():
            print(f"❌ Personas directory not found: {personas_dir}")
            return personas
            
        try:
            for persona_file in personas_dir.glob("*-guidelines.txt"):
                persona_name = persona_file.stem.replace("-guidelines", "")
                try:
                    with open(persona_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        # Parse TalentSync persona format
                        lines = content.split('\n')
                        name = persona_name.replace("_", " ").title().replace("-", " ")
                        role = "Technical Interviewer"
                        specialty = "General Interview"
                        background = ""
                        
                        for i, line in enumerate(lines):
                            line = line.strip()
                            
                            # Extract name and role from header
                            if "# TalentSync AI Interviewer Persona -" in line:
                                persona_info = line.replace("# TalentSync AI Interviewer Persona -", "").strip()
                                if "(" in persona_info and ")" in persona_info:
                                    name = persona_info.split("(")[0].strip()
                                    role = persona_info.split("(")[1].replace(")", "").strip()
                                else:
                                    name = persona_info.strip()
                            
                            # Extract background
                            elif line.startswith("## Background") and i + 1 < len(lines):
                                background_lines = []
                                for j in range(i + 1, len(lines)):
                                    next_line = lines[j].strip()
                                    if not next_line:
                                        continue
                                    elif next_line.startswith("#"):
                                        break
                                    else:
                                        background_lines.append(next_line)
                                        if len(background_lines) >= 3 or len(' '.join(background_lines)) > 150:
                                            break
                                
                                if background_lines:
                                    background = ' '.join(background_lines)
                                    if len(background) > 200:
                                        background = background[:200] + "..."
                            
                            # Extract specialty
                            elif "Focus areas:" in line:
                                specialty = line.split("Focus areas:", 1)[-1].strip()[:80]
                        
                        personas[persona_name] = {
                            "name": name,
                            "role": role,
                            "specialty": specialty,
                            "background": background,
                            "guidelines": content,
                            "file": persona_file
                        }
                except Exception as e:
                    print(f"Error loading persona {persona_file}: {e}")
        except Exception as e:
            print(f"Error accessing personas directory: {e}")
        
        return personas
    
    def display_personas(self):
        """Display available personas with detailed information."""
        print("\n🎭 Available TalentSync AI Interview Personas:")
        print("=" * 75)
        
        if not self.personas:
            print("❌ No personas loaded. Check the personas directory.")
            return
        
        persona_list = list(self.personas.keys())
        
        for i, persona_key in enumerate(persona_list, 1):
            persona = self.personas[persona_key]
            print(f"  {i}. 🤖 {persona['name']}")
            print(f"     📋 Role: {persona['role']}")
            if persona['background']:
                print(f"     📚 Background: {persona['background']}")
            if persona['specialty'] != "General Interview":
                print(f"     🎯 Focus: {persona['specialty']}")
            print()
    
    def select_persona(self) -> Optional[str]:
        """Allow user to select a persona for conversation."""
        if not self.personas:
            print("❌ No personas available.")
            return None
            
        personas = list(self.personas.keys())
        
        while True:
            try:
                self.display_personas()
                choice = input(f"\n🎯 Select a persona (1-{len(personas)}) or 'q' to quit: ").strip()
                
                if choice.lower() == 'q':
                    return None
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(personas):
                    selected_persona_key = personas[choice_num - 1]
                    selected_persona = self.personas[selected_persona_key]
                    print(f"\n✅ Selected: {selected_persona['name']}")
                    print(f"📋 Role: {selected_persona['role']}")
                    return selected_persona_key
                else:
                    print(f"❌ Please enter a number between 1 and {len(personas)}")
                    
            except ValueError:
                print("❌ Please enter a valid number or 'q' to quit")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                return None
    
    async def speech_to_text(self) -> str:
        """Record user's speech and convert to text."""
        try:
            print("\n🎤 Listening... (speak now)")
            audio_data = await self.transcription_service.record_audio()
            
            print("🔄 Transcribing speech...")
            result = await self.transcription_service.transcribe_audio_chunk(audio_data)
            
            transcript = result.get('text', '').strip()
            confidence = result.get('confidence_score', 0)
            
            if transcript:
                print(f"✅ You said: \"{transcript}\" (confidence: {confidence:.2f})")
                return transcript
            else:
                print("❌ No speech detected. Please try again.")
                return ""
                
        except Exception as e:
            print(f"❌ Error in speech recognition: {e}")
            return ""
    
    def text_to_speech(self, text: str, voice: str = "alloy") -> bool:
        """Convert text to speech and play it back."""
        if not text.strip():
            return False
            
        # Create unique temporary file
        temp_audio_file = f"interview_tts_{int(time.time())}_{threading.get_ident()}.mp3"
        
        try:
            print(f"🔊 Generating speech...")
            
            # Generate speech using OpenAI TTS
            response = self.openai_client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text
            )
            
            # Save to temporary file
            with open(temp_audio_file, "wb") as f:
                f.write(response.content)
            
            self.temp_audio_files.append(temp_audio_file)
            
            # Play audio in separate thread
            def play_audio():
                try:
                    pygame.mixer.music.load(temp_audio_file)
                    pygame.mixer.music.play()
                    
                    # Wait for playback to complete
                    while pygame.mixer.music.get_busy():
                        pygame.time.Clock().tick(10)
                        
                except Exception as e:
                    print(f"❌ Error playing audio: {e}")
                finally:
                    # Clean up
                    try:
                        pygame.mixer.music.stop()
                        pygame.mixer.music.unload()
                    except:
                        pass
                    self.playback_finished.set()
            
            self.playback_finished.clear()
            threading.Thread(target=play_audio, daemon=True).start()
            
            # Wait for playback to complete
            self.playback_finished.wait()
            
            return True
            
        except Exception as e:
            print(f"❌ Error in text-to-speech: {e}")
            return False
    
    def generate_ai_response(self, user_input: str) -> str:
        """Generate AI response using OpenAI o4-mini with persona context."""
        if not self.current_persona:
            return "I'm sorry, no persona is selected."
        
        try:
            persona_data = self.personas[self.current_persona]
            persona_guidelines = persona_data['guidelines']
            
            # Create system prompt with persona context
            system_prompt = f"""You are {persona_data['name']}, a {persona_data['role']} conducting an interview.

{persona_guidelines[:1000]}...

Instructions:
- Stay in character as {persona_data['name']}
- Keep responses concise and conversational (2-3 sentences max for voice)
- Ask follow-up questions to explore the candidate's experience
- Be professional but approachable
- Focus on your specialty: {persona_data['specialty']}
- This is a voice conversation, so avoid overly complex explanations
"""
            
            # Add user input to conversation history
            self.conversation_history.append({
                "role": "user", 
                "content": user_input
            })
            
            # Generate response using o4-mini
            messages = [
                {"role": "system", "content": system_prompt}
            ] + self.conversation_history[-10:]  # Keep last 10 exchanges for context
            
            print("🤖 AI is thinking...")
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Using o4-mini
                messages=messages,
                max_tokens=200,  # Keep responses concise for voice
                temperature=0.7,
                presence_penalty=0.6,
                frequency_penalty=0.3
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Add AI response to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": ai_response
            })
            
            return ai_response
            
        except Exception as e:
            print(f"❌ Error generating AI response: {e}")
            return "I'm sorry, I'm having trouble processing your response right now."
    
    def is_conversation_ending(self, text: str) -> bool:
        """Check if the conversation should end."""
        ending_phrases = [
            "i am done", "i'm done", "end interview", "finish interview",
            "thank you for your time", "goodbye", "that's all",
            "no more questions", "we can end here"
        ]
        
        text_lower = text.lower().strip()
        return any(phrase in text_lower for phrase in ending_phrases)
    
    def cleanup_temp_files(self):
        """Clean up temporary audio files."""
        for temp_file in self.temp_audio_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                print(f"Warning: Could not remove {temp_file}: {e}")
        
        self.temp_audio_files.clear()
    
    async def start_interview(self):
        """Start the complete voice-to-voice interview experience."""
        print("\n🚀 Starting Enhanced Voice Interview System")
        print("=" * 60)
        
        # Select persona
        selected_persona = self.select_persona()
        if not selected_persona:
            print("👋 Goodbye!")
            return
        
        self.current_persona = selected_persona
        persona_data = self.personas[selected_persona]
        
        print(f"\n🎭 Interview Starting with {persona_data['name']}")
        print(f"📋 Role: {persona_data['role']}")
        print(f"🎯 Session ID: {self.session_id}")
        print("\n" + "=" * 60)
        
        # Initial greeting
        greeting = f"Hello! I'm {persona_data['name']}, your {persona_data['role']} for today's interview. I'm excited to learn more about your background and experience. Please introduce yourself and tell me a bit about what role you're interested in."
        
        print(f"🤖 {persona_data['name']}: {greeting}")
        self.text_to_speech(greeting)
        
        # Main conversation loop
        turn_count = 0
        try:
            while True:
                turn_count += 1
                print(f"\n--- Turn {turn_count} ---")
                
                # Get user speech input
                user_input = await self.speech_to_text()
                
                if not user_input:
                    print("⚠️ No input detected. Please try speaking again.")
                    continue
                
                # Check for conversation ending
                if self.is_conversation_ending(user_input):
                    farewell = f"Thank you for your time today! It was great speaking with you. We'll be in touch soon about next steps. Have a wonderful day!"
                    print(f"🤖 {persona_data['name']}: {farewell}")
                    self.text_to_speech(farewell)
                    break
                
                # Generate and speak AI response
                ai_response = self.generate_ai_response(user_input)
                print(f"🤖 {persona_data['name']}: {ai_response}")
                self.text_to_speech(ai_response)
                
                # Check if AI ended the conversation
                if self.is_conversation_ending(ai_response):
                    break
                    
        except KeyboardInterrupt:
            print("\n\n⚠️ Interview interrupted by user")
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
        finally:
            self.cleanup_temp_files()
            pygame.mixer.quit()
            
            # Save conversation history
            try:
                import json
                history_file = f"interview_history_{self.session_id}.json"
                with open(history_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        "session_id": self.session_id,
                        "persona": persona_data['name'],
                        "role": persona_data['role'],
                        "turn_count": turn_count,
                        "conversation": self.conversation_history,
                        "timestamp": time.time()
                    }, f, indent=2, ensure_ascii=False)
                
                print(f"\n📄 Interview saved to: {history_file}")
            except Exception as e:
                print(f"⚠️ Could not save interview history: {e}")
            
            print(f"\n✅ Interview completed! Total turns: {turn_count}")
            print("👋 Thank you for using the Enhanced Voice Interview System!")

async def main():
    """Main function to run the enhanced interview system."""
    try:
        # Check dependencies
        if not settings.openai_api_key:
            print("❌ OpenAI API key not found!")
            print("Please set OPENAI_API_KEY in your .env file")
            return
        
        # Create and start interview system
        interview = EnhancedInteractiveInterview()
        await interview.start_interview()
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")

if __name__ == "__main__":
    print("🎤🔊 Enhanced Voice-to-Voice Interview System")
    print("=" * 50)
    print("Features:")
    print("✅ Real-time Speech Recognition (OpenAI Whisper)")
    print("✅ AI Conversation (OpenAI o4-mini)")
    print("✅ Text-to-Speech Playback (OpenAI TTS)")
    print("✅ Persona-driven Interviews")
    print("✅ Session Management")
    print("=" * 50)
    
    # Run the interview system
    asyncio.run(main())

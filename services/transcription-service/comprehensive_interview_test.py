#!/usr/bin/env python3

"""
Comprehensive Interactive AI Interview Testing System

This system provides:
1. Full persona parsing and display with unique details
2. Interactive voice-based interviews with real-time transcription
3. OpenAI GPT-4 Mini integration for dynamic, context-aware responses
4. Audio file storage and management
5. Session logging and conversation history
6. Advanced interview scenarios and follow-up questions

Audio files are stored temporarily during transcription in the system temp directory,
then cleaned up automatically. Conversation logs are saved locally.
"""

import asyncio
import os
import sys
import time
import json
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.services.transcription_service import TranscriptionService
from app.core.database import get_session, engine
from app.core.config import settings

# Import OpenAI for advanced responses
from openai import OpenAI

class ComprehensiveInterviewTester:
    """Advanced interactive interview testing system with OpenAI integration."""
    
    def __init__(self):
        self.transcription_service = TranscriptionService()
        self.openai_client = OpenAI(api_key=settings.openai_api_key)
        self.personas = self.load_personas()
        self.conversation_history = []
        self.current_persona = None
        self.session_id = f"test_interview_{int(time.time())}"
        self.audio_files_dir = Path(tempfile.gettempdir()) / "talentsync_audio" / self.session_id
        self.logs_dir = Path(__file__).parent / "interview_logs"
        
        # Create directories
        self.audio_files_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        # Interview configuration
        self.use_openai_responses = True
        self.max_turns = 10
        self.confidence_threshold = 0.7
        
        print(f"🎯 Interview session initialized: {self.session_id}")
        print(f"📁 Audio files will be stored in: {self.audio_files_dir}")
        print(f"📋 Conversation logs will be saved in: {self.logs_dir}")
    
    def load_personas(self) -> Dict[str, Dict[str, Any]]:
        """Load and parse persona guidelines with comprehensive extraction."""
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
                        
                        # Extract comprehensive persona info
                        lines = content.split('\n')
                        name = persona_name.replace("_", " ").title().replace("-", " ")
                        role = "Technical Interviewer"
                        specialty = "General Interview"
                        background = ""
                        domains = []
                        interview_style = ""
                        
                        for i, line in enumerate(lines):
                            line = line.strip()
                            
                            # Extract from header
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
                                        if len(background_lines) >= 2 or len(' '.join(background_lines)) > 200:
                                            break
                                
                                if background_lines:
                                    background = ' '.join(background_lines)
                                    if len(background) > 250:
                                        background = background[:250] + "..."
                            
                            # Extract interview style/approach
                            elif line.startswith("## Interview") and any(keyword in line.lower() for keyword in ["approach", "style", "philosophy"]):
                                style_lines = []
                                for j in range(i + 1, len(lines)):
                                    next_line = lines[j].strip()
                                    if not next_line:
                                        continue
                                    elif next_line.startswith("#"):
                                        break
                                    else:
                                        style_lines.append(next_line)
                                        if len(style_lines) >= 2:
                                            break
                                
                                if style_lines:
                                    interview_style = ' '.join(style_lines)[:150]
                            
                            # Extract domains and specialties
                            elif "Domain" in line and ("Expertise" in line or "Specialization" in line):
                                # Look for numbered or bulleted lists
                                for j in range(i + 1, min(i + 15, len(lines))):
                                    next_line = lines[j].strip()
                                    if not next_line or next_line.startswith("#"):
                                        break
                                    # Extract domain names from numbered lists or bullets
                                    if any(char in next_line for char in ['1.', '2.', '3.', '*', '-']) and ":" in next_line:
                                        domain = next_line.split(":")[0].strip()
                                        # Clean up numbering and bullets
                                        domain = domain.replace("**", "").strip()
                                        for prefix in ["1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "*", "-"]:
                                            domain = domain.replace(prefix, "").strip()
                                        if domain and len(domain) < 50:
                                            domains.append(domain)
                            
                            # Extract focus areas
                            elif "Focus areas:" in line:
                                specialty = line.split("Focus areas:", 1)[-1].strip()[:100]
                        
                        # If no domains found, try to extract from specialty or role
                        if not domains:
                            if "ai" in role.lower() or "ml" in role.lower():
                                domains = ["Machine Learning", "AI Engineering"]
                            elif "devops" in role.lower():
                                domains = ["DevOps", "Infrastructure"]
                            elif "algorithm" in role.lower():
                                domains = ["Data Structures & Algorithms"]
                            elif "resume" in role.lower():
                                domains = ["Resume-Driven Interview"]
                            else:
                                domains = ["Software Engineering"]
                        
                        personas[persona_name] = {
                            "name": name,
                            "role": role,
                            "specialty": specialty,
                            "background": background,
                            "interview_style": interview_style,
                            "domains": domains,
                            "guidelines": content,
                            "file": persona_file
                        }
                        
                        print(f"✅ Loaded persona: {name} ({role})")
                        
                except Exception as e:
                    print(f"❌ Error loading persona {persona_file}: {e}")
        except Exception as e:
            print(f"❌ Error accessing personas directory: {e}")
        
        return personas
    
    def display_personas(self):
        """Display available personas with comprehensive information."""
        print("\n" + "="*80)
        print("🎭 TalentSync AI Interview Personas - Comprehensive Test Suite")
        print("="*80)
        
        if not self.personas:
            print("❌ No personas loaded. Check the personas directory.")
            return
        
        persona_list = list(self.personas.keys())
        
        for i, persona_key in enumerate(persona_list, 1):
            persona = self.personas[persona_key]
            print(f"\n  {i}. 🤖 {persona['name']}")
            print(f"     📋 Role: {persona['role']}")
            print(f"     🎯 Domains: {', '.join(persona['domains'][:3])}")
            if persona['background']:
                print(f"     📚 Background: {persona['background'][:120]}...")
            if persona['interview_style']:
                print(f"     🎨 Style: {persona['interview_style'][:100]}...")
            print(f"     📄 Source: {persona['file'].name}")
    
    def select_persona(self) -> Optional[str]:
        """Allow user to select a persona for comprehensive testing."""
        if not self.personas:
            print("❌ No personas available.")
            return None
            
        personas = list(self.personas.keys())
        
        while True:
            try:
                self.display_personas()
                print(f"\n🔧 Test Configuration:")
                print(f"   🤖 OpenAI Integration: {'✅ Enabled' if self.use_openai_responses else '❌ Disabled'}")
                print(f"   🔄 Max Turns: {self.max_turns}")
                print(f"   📊 Confidence Threshold: {self.confidence_threshold}")
                
                choice = input(f"\n🎯 Select persona (1-{len(personas)}), 'c' for config, or 'q' to quit: ").strip()
                
                if choice.lower() == 'q':
                    return None
                elif choice.lower() == 'c':
                    self.configure_test()
                    continue
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(personas):
                    selected_persona_key = personas[choice_num - 1]
                    selected_persona = self.personas[selected_persona_key]
                    print(f"\n✅ Selected: {selected_persona['name']}")
                    print(f"📋 Role: {selected_persona['role']}")
                    print(f"🎯 Domains: {', '.join(selected_persona['domains'])}")
                    return selected_persona_key
                else:
                    print(f"❌ Please enter a number between 1 and {len(personas)}")
                    
            except ValueError:
                print("❌ Please enter a valid number, 'c' for config, or 'q' to quit")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                return None
    
    def configure_test(self):
        """Configure test parameters."""
        print("\n⚙️ Test Configuration")
        print("=" * 40)
        
        # OpenAI toggle
        toggle = input(f"🤖 Use OpenAI responses? (current: {self.use_openai_responses}) [y/n]: ").strip().lower()
        if toggle in ['y', 'yes', 'true']:
            self.use_openai_responses = True
        elif toggle in ['n', 'no', 'false']:
            self.use_openai_responses = False
        
        # Max turns
        try:
            turns = input(f"🔄 Max turns (current: {self.max_turns}): ").strip()
            if turns:
                self.max_turns = max(1, int(turns))
        except ValueError:
            pass
        
        # Confidence threshold
        try:
            threshold = input(f"📊 Confidence threshold (current: {self.confidence_threshold}): ").strip()
            if threshold:
                self.confidence_threshold = max(0.0, min(1.0, float(threshold)))
        except ValueError:
            pass
        
        print(f"\n✅ Configuration updated!")
    
    async def record_and_transcribe_with_storage(self, turn_number: int) -> Optional[Dict[str, Any]]:
        """Record audio and transcribe with file storage."""
        try:
            print(f"\n🎤 Turn {turn_number} - Recording... (speak clearly, pause when finished)")
            print("🤫 Recording will stop automatically after silence")
            
            # Record audio
            audio_data = await self.transcription_service.record_audio()
            
            if not audio_data:
                print("❌ No audio recorded.")
                return None
            
            # Save audio file
            audio_filename = f"turn_{turn_number:02d}_{int(time.time())}.wav"
            audio_path = self.audio_files_dir / audio_filename
            
            with open(audio_path, 'wb') as f:
                f.write(audio_data)
            
            print(f"💾 Audio saved: {audio_filename}")
            print("✅ Audio recorded! Transcribing...")
            
            # Transcribe
            transcript_result = await self.transcription_service.transcribe_audio_chunk(audio_data)
            
            transcript_text = transcript_result['text'].strip()
            confidence = transcript_result.get('confidence_score', 0.0)
            segments = transcript_result.get('segments', [])
            
            print(f"📝 You said: \"{transcript_text}\"")
            print(f"📊 Confidence: {confidence:.2f}")
            
            if confidence and confidence < self.confidence_threshold:
                print(f"⚠️ Low confidence detected. Consider speaking more clearly.")
            
            # Store transcription details
            transcription_data = {
                "text": transcript_text,
                "confidence": confidence,
                "segments": segments,
                "audio_file": str(audio_path),
                "timestamp": datetime.now().isoformat(),
                "turn_number": turn_number
            }
            
            return transcription_data
            
        except Exception as e:
            print(f"❌ Error during recording/transcription: {e}")
            return None
    
    async def generate_openai_response(self, persona_key: str, user_input: str, turn_number: int) -> str:
        """Generate contextual response using OpenAI GPT-4 Mini."""
        try:
            persona = self.personas[persona_key]
            
            # Build conversation context
            context_messages = [
                {
                    "role": "system",
                    "content": f"""You are {persona['name']}, a {persona['role']} conducting a technical interview through the TalentSync platform.
                    
Background: {persona['background']}

Interview Style: {persona['interview_style']}

Domains of Expertise: {', '.join(persona['domains'])}

Guidelines:
1. Maintain the persona's character and expertise level
2. Ask progressive questions that build on previous responses
3. Provide constructive feedback and follow-up questions
4. Keep responses conversational but professional
5. Adapt difficulty based on candidate responses
6. This is turn {turn_number} of the interview

Previous conversation context: {len(self.conversation_history)} previous exchanges"""
                }
            ]
            
            # Add conversation history
            for entry in self.conversation_history[-5:]:  # Last 5 exchanges for context
                context_messages.append({"role": "user", "content": entry.get("user_input", "")})
                context_messages.append({"role": "assistant", "content": entry.get("persona_response", "")})
            
            # Add current input
            context_messages.append({"role": "user", "content": user_input})
            
            # Generate response
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=context_messages,
                max_tokens=300,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"❌ Error generating OpenAI response: {e}")
            return self.generate_fallback_response(persona_key, user_input, turn_number)
    
    def generate_fallback_response(self, persona_key: str, user_input: str, turn_number: int) -> str:
        """Generate fallback response when OpenAI is unavailable."""
        persona = self.personas[persona_key]
        persona_name = persona['name']
        
        # Simple pattern-based responses
        if turn_number == 1:
            return f"Hello! I'm {persona_name}, and I'll be conducting your interview today. Thank you for sharing that with me. Could you tell me more about your technical background and what interests you about this role?"
        elif turn_number == 2:
            return f"That's interesting! Based on what you've mentioned, I'd like to dive deeper into your experience. Can you walk me through a specific technical challenge you've faced and how you approached solving it?"
        elif turn_number == 3:
            return f"Great example! I can see you have solid problem-solving skills. Now, let's explore your technical knowledge further. What technologies or frameworks are you most comfortable working with, and why do you prefer them?"
        else:
            responses = [
                "That's a thoughtful approach. Can you elaborate on the trade-offs you considered?",
                "Interesting perspective! How would you handle this scenario under tight deadlines?",
                "Good thinking! What would you do differently if you encountered this problem again?",
                "I appreciate the detail in your response. How would you explain this concept to a non-technical team member?",
                "Excellent! Let's consider a variation of this problem. How would your approach change if...?"
            ]
            return responses[(turn_number - 4) % len(responses)]
    
    async def conversation_loop(self, persona_key: str):
        """Comprehensive conversation loop with full logging and audio management."""
        persona = self.personas[persona_key]
        self.current_persona = persona_key
        
        print(f"\n🎬 Starting Comprehensive Interview Test")
        print("=" * 70)
        print(f"🤖 Interviewer: {persona['name']}")
        print(f"📋 Role: {persona['role']}")
        print(f"🎯 Domains: {', '.join(persona['domains'])}")
        print(f"🔧 OpenAI Integration: {'✅ Enabled' if self.use_openai_responses else '❌ Disabled'}")
        print("=" * 70)
        print("💡 Instructions:")
        print("   - Speak clearly into your microphone")
        print("   - Wait for transcription and response after each turn")
        print("   - Say 'quit', 'exit', or 'end' to finish the interview")
        print("   - Press Ctrl+C for emergency exit")
        print("=" * 70)
        
        # Initial greeting
        initial_greeting = f"Welcome to your TalentSync interview! I'm {persona['name']}, your {persona['role']}. I'm excited to learn about your background and experience today. To get started, could you please introduce yourself and tell me what brings you here?"
        
        print(f"\n🤖 {persona['name']}: {initial_greeting}")
        
        turn_number = 1
        
        try:
            while turn_number <= self.max_turns:
                print(f"\n" + "─" * 50)
                print(f"🔄 Turn {turn_number}/{self.max_turns}")
                
                # Record and transcribe
                transcription_data = await self.record_and_transcribe_with_storage(turn_number)
                
                if not transcription_data:
                    print("❌ Skipping turn due to transcription error")
                    continue
                
                user_input = transcription_data["text"]
                
                # Check for exit commands
                if any(exit_word in user_input.lower() for exit_word in ['quit', 'exit', 'end', 'stop']):
                    print("👋 Interview ended by user request")
                    break
                
                # Generate response
                print("🤔 Generating response...")
                
                if self.use_openai_responses:
                    persona_response = await self.generate_openai_response(persona_key, user_input, turn_number)
                else:
                    persona_response = self.generate_fallback_response(persona_key, user_input, turn_number)
                
                print(f"\n🤖 {persona['name']}: {persona_response}")
                
                # Log the exchange
                exchange = {
                    "turn_number": turn_number,
                    "timestamp": datetime.now().isoformat(),
                    "user_input": user_input,
                    "transcription_confidence": transcription_data.get("confidence", 0.0),
                    "audio_file": transcription_data.get("audio_file", ""),
                    "persona_response": persona_response,
                    "persona_name": persona["name"],
                    "segments": transcription_data.get("segments", [])
                }
                
                self.conversation_history.append(exchange)
                turn_number += 1
        
        except KeyboardInterrupt:
            print("\n\n⚠️ Interview interrupted by user")
        except Exception as e:
            print(f"\n❌ Unexpected error during interview: {e}")
        finally:
            await self.save_conversation_log()
            self.display_session_summary()
    
    async def save_conversation_log(self):
        """Save comprehensive conversation log."""
        try:
            log_filename = f"interview_log_{self.session_id}.json"
            log_path = self.logs_dir / log_filename
            
            log_data = {
                "session_id": self.session_id,
                "persona": self.personas.get(self.current_persona, {}) if self.current_persona else {},
                "configuration": {
                    "openai_enabled": self.use_openai_responses,
                    "max_turns": self.max_turns,
                    "confidence_threshold": self.confidence_threshold
                },
                "conversation_history": self.conversation_history,
                "audio_files_directory": str(self.audio_files_dir),
                "total_turns": len(self.conversation_history),
                "start_time": datetime.now().isoformat(),
                "audio_files": [f.name for f in self.audio_files_dir.glob("*.wav")] if self.audio_files_dir.exists() else []
            }
            
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
            
            print(f"📋 Conversation log saved: {log_path}")
            
        except Exception as e:
            print(f"❌ Error saving conversation log: {e}")
    
    def display_session_summary(self):
        """Display comprehensive session summary."""
        print("\n" + "="*70)
        print("📊 Interview Session Summary")
        print("="*70)
        
        if self.current_persona and self.current_persona in self.personas:
            persona = self.personas[self.current_persona]
            print(f"🤖 Interviewer: {persona['name']} ({persona['role']})")
        
        print(f"🆔 Session ID: {self.session_id}")
        print(f"🔄 Total Turns: {len(self.conversation_history)}")
        
        if self.conversation_history:
            confidences = [h.get("transcription_confidence", 0) for h in self.conversation_history if h.get("transcription_confidence")]
            if confidences:
                avg_confidence = sum(confidences) / len(confidences)
                print(f"📊 Average Transcription Confidence: {avg_confidence:.2f}")
            
            # Count low confidence turns
            low_confidence_turns = sum(1 for c in confidences if c < self.confidence_threshold)
            if low_confidence_turns > 0:
                print(f"⚠️ Low Confidence Turns: {low_confidence_turns}")
        
        print(f"📁 Audio Files Stored: {len(list(self.audio_files_dir.glob('*.wav'))) if self.audio_files_dir.exists() else 0}")
        print(f"📂 Audio Directory: {self.audio_files_dir}")
        print(f"📋 Log Directory: {self.logs_dir}")
        print(f"🤖 OpenAI Integration: {'✅ Used' if self.use_openai_responses else '❌ Not Used'}")
        
        print("\n💡 Next Steps:")
        print("   - Review conversation logs for analysis")
        print("   - Audio files can be replayed for quality assessment")
        print("   - Test different personas or configurations")
        print("   - Check transcription accuracy and confidence scores")
        
        # Cleanup prompt
        cleanup = input("\n🗑️ Clean up audio files? [y/N]: ").strip().lower()
        if cleanup in ['y', 'yes']:
            self.cleanup_audio_files()
    
    def cleanup_audio_files(self):
        """Clean up temporary audio files."""
        try:
            if self.audio_files_dir.exists():
                audio_files = list(self.audio_files_dir.glob("*.wav"))
                for audio_file in audio_files:
                    audio_file.unlink()
                
                # Remove directory if empty
                try:
                    self.audio_files_dir.rmdir()
                    parent_dir = self.audio_files_dir.parent
                    if not any(parent_dir.iterdir()):
                        parent_dir.rmdir()
                except OSError:
                    pass  # Directory not empty
                
                print(f"🗑️ Cleaned up {len(audio_files)} audio files")
        except Exception as e:
            print(f"❌ Error cleaning up audio files: {e}")
    
    async def run_comprehensive_test(self):
        """Run the comprehensive interview test."""
        print("🚀 TalentSync Comprehensive Interview Testing System")
        print("=" * 60)
        print("This system tests the full interview pipeline:")
        print("✅ Persona loading and parsing")
        print("✅ Real-time audio capture and transcription")
        print("✅ OpenAI-powered dynamic responses")
        print("✅ Audio file storage and management")
        print("✅ Conversation logging and analysis")
        print("=" * 60)
        
        # Load personas
        if not self.personas:
            print("❌ No personas available. Please check the personas directory.")
            return
        
        print(f"✅ Loaded {len(self.personas)} personas successfully")
        
        # Select persona
        selected_persona = self.select_persona()
        
        if selected_persona:
            await self.conversation_loop(selected_persona)
        else:
            print("👋 Test cancelled by user")

async def main():
    """Main entry point for comprehensive testing."""
    try:
        tester = ComprehensiveInterviewTester()
        await tester.run_comprehensive_test()
    except KeyboardInterrupt:
        print("\n\n👋 Test system shutdown by user")
    except Exception as e:
        print(f"\n❌ System error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Check dependencies
    try:
        import openai
        import sounddevice
        import numpy
        print("✅ All dependencies available")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Install with: pip install openai sounddevice numpy")
        sys.exit(1)
    
    # Run the comprehensive test
    asyncio.run(main())

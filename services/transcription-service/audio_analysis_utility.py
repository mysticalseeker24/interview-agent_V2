#!/usr/bin/env python3

"""
Audio File Analysis Utility

This utility helps you understand how audio files are handled in the TalentSync system:
1. Shows where audio files are stored during interviews
2. Analyzes audio file properties and storage patterns
3. Provides cleanup and management tools
4. Demonstrates the audio processing pipeline
"""

import os
import sys
import tempfile
import wave
from pathlib import Path
from datetime import datetime

def analyze_audio_storage():
    """Analyze how and where audio files are stored."""
    print("🔍 TalentSync Audio File Storage Analysis")
    print("=" * 60)
    
    # System temp directory
    system_temp = Path(tempfile.gettempdir())
    talentsync_audio_dir = system_temp / "talentsync_audio"
    
    print(f"📁 System Temp Directory: {system_temp}")
    print(f"📂 TalentSync Audio Directory: {talentsync_audio_dir}")
    print(f"📊 Exists: {'✅ Yes' if talentsync_audio_dir.exists() else '❌ No'}")
    
    if talentsync_audio_dir.exists():
        session_dirs = list(talentsync_audio_dir.glob("test_interview_*"))
        print(f"🎯 Interview Sessions Found: {len(session_dirs)}")
        
        total_audio_files = 0
        total_size = 0
        
        for session_dir in session_dirs:
            audio_files = list(session_dir.glob("*.wav"))
            session_size = sum(f.stat().st_size for f in audio_files)
            total_audio_files += len(audio_files)
            total_size += session_size
            
            print(f"  📋 Session: {session_dir.name}")
            print(f"     🎵 Audio Files: {len(audio_files)}")
            print(f"     💾 Size: {session_size / 1024:.1f} KB")
            
            # Analyze individual files
            for audio_file in audio_files[:3]:  # Show first 3 files
                try:
                    with wave.open(str(audio_file), 'rb') as wf:
                        frames = wf.getnframes()
                        sample_rate = wf.getframerate()
                        duration = frames / sample_rate
                        channels = wf.getnchannels()
                        
                    file_size = audio_file.stat().st_size
                    print(f"     🎤 {audio_file.name}:")
                    print(f"        ⏱️ Duration: {duration:.1f}s")
                    print(f"        📊 Sample Rate: {sample_rate}Hz")
                    print(f"        🔊 Channels: {channels}")
                    print(f"        💾 Size: {file_size} bytes")
                except Exception as e:
                    print(f"     ❌ Error analyzing {audio_file.name}: {e}")
        
        print(f"\n📊 Total Statistics:")
        print(f"   🎵 Total Audio Files: {total_audio_files}")
        print(f"   💾 Total Size: {total_size / 1024:.1f} KB")
        
        if total_audio_files > 0:
            cleanup = input(f"\n🗑️ Clean up all {total_audio_files} audio files? [y/N]: ").strip().lower()
            if cleanup in ['y', 'yes']:
                cleanup_audio_files(talentsync_audio_dir)
    
    # Check transcription service temp files
    print(f"\n🔧 Transcription Service Temp Files:")
    temp_files = list(system_temp.glob("tmp*.wav"))
    whisper_files = list(system_temp.glob("*whisper*"))
    
    print(f"   🎵 Temp WAV files: {len(temp_files)}")
    print(f"   🤖 Whisper-related files: {len(whisper_files)}")
    
    if temp_files or whisper_files:
        print("   💡 These are temporary files created during transcription")
        print("   💡 They should be automatically cleaned up")

def cleanup_audio_files(audio_dir: Path):
    """Clean up audio files with confirmation."""
    try:
        cleaned_files = 0
        cleaned_dirs = 0
        
        for session_dir in audio_dir.glob("test_interview_*"):
            audio_files = list(session_dir.glob("*.wav"))
            for audio_file in audio_files:
                audio_file.unlink()
                cleaned_files += 1
            
            # Remove empty directory
            try:
                session_dir.rmdir()
                cleaned_dirs += 1
            except OSError:
                pass  # Directory not empty
        
        # Remove main directory if empty
        try:
            if not any(audio_dir.iterdir()):
                audio_dir.rmdir()
                print(f"🗑️ Removed main audio directory")
        except (OSError, FileNotFoundError):
            pass
        
        print(f"✅ Cleaned up {cleaned_files} audio files and {cleaned_dirs} session directories")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")

def demonstrate_audio_pipeline():
    """Demonstrate the audio processing pipeline."""
    print("\n🎯 Audio Processing Pipeline in TalentSync")
    print("=" * 50)
    
    print("1. 🎤 Audio Capture:")
    print("   - Uses sounddevice library for real-time recording")
    print("   - 16kHz sample rate, mono channel")
    print("   - Stops automatically after 2 seconds of silence")
    print("   - Audio stored in memory as numpy array")
    
    print("\n2. 💾 Temporary Storage:")
    print("   - Audio converted to WAV format")
    print("   - Saved to system temp directory during transcription")
    print(f"   - Location: {tempfile.gettempdir()}")
    print("   - Automatically cleaned up after transcription")
    
    print("\n3. 🎵 Interview Session Storage:")
    print("   - Each interview gets unique session directory")
    print("   - Audio files numbered by turn: turn_01_timestamp.wav")
    print("   - Stored for analysis and quality checking")
    print("   - User can choose to clean up after interview")
    
    print("\n4. 🤖 Transcription Process:")
    print("   - Audio sent to OpenAI Whisper API")
    print("   - Returns text + confidence scores + segments")
    print("   - Temporary files deleted immediately")
    print("   - Results stored in conversation log")
    
    print("\n5. 📋 Logging and Analysis:")
    print("   - Conversation logs saved as JSON")
    print("   - Include transcription confidence scores")
    print("   - Reference to audio files for replay")
    print("   - Comprehensive session metadata")

def show_current_usage():
    """Show current audio file usage."""
    print("\n📊 Current Audio File Usage")
    print("=" * 40)
    
    system_temp = Path(tempfile.gettempdir())
    
    # TalentSync audio files
    talentsync_audio = system_temp / "talentsync_audio"
    if talentsync_audio.exists():
        sessions = list(talentsync_audio.glob("test_interview_*"))
        total_files = sum(len(list(s.glob("*.wav"))) for s in sessions)
        total_size = sum(sum(f.stat().st_size for f in s.glob("*.wav")) for s in sessions)
        
        print(f"🎯 Active Interview Sessions: {len(sessions)}")
        print(f"🎵 Total Audio Files: {total_files}")
        print(f"💾 Total Storage Used: {total_size / 1024:.1f} KB")
    else:
        print("📭 No active interview sessions")
    
    # Temp files
    temp_wav_files = list(system_temp.glob("tmp*.wav"))
    temp_other = list(system_temp.glob("*whisper*")) + list(system_temp.glob("*talentsync*"))
    
    print(f"🔧 Temp WAV Files: {len(temp_wav_files)}")
    print(f"🤖 Other Temp Files: {len(temp_other)}")

def main():
    """Main analysis function."""
    print("🎵 TalentSync Audio File Analysis & Management")
    print("=" * 55)
    
    while True:
        print("\n🔧 Options:")
        print("  1. 🔍 Analyze audio storage")
        print("  2. 🎯 Show audio pipeline")
        print("  3. 📊 Show current usage")
        print("  4. 🗑️ Cleanup all audio files")
        print("  5. ❌ Exit")
        
        choice = input("\n🎯 Select option [1-5]: ").strip()
        
        if choice == '1':
            analyze_audio_storage()
        elif choice == '2':
            demonstrate_audio_pipeline()
        elif choice == '3':
            show_current_usage()
        elif choice == '4':
            system_temp = Path(tempfile.gettempdir())
            talentsync_audio = system_temp / "talentsync_audio"
            if talentsync_audio.exists():
                cleanup_audio_files(talentsync_audio)
            else:
                print("📭 No audio files to clean up")
        elif choice == '5':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please select 1-5.")

if __name__ == "__main__":
    main()

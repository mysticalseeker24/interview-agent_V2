#!/usr/bin/env python3
"""
Test script for voice assignment to personas
"""

import logging
import sys
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent / "app"))

try:
    from app.services.persona_service import persona_service
    
    print("🎭 Testing Voice Assignment System")
    print("=" * 50)
    
    print(f"\n📊 Total personas loaded: {len(persona_service.personas)}")
    
    # Test voice assignments for each persona
    print("\n🎤 Voice Assignments by Persona:")
    print("-" * 40)
    
    for key, persona in persona_service.personas.items():
        voice_desc = persona_service.get_voice_description(persona.voice)
        print(f"👤 {persona.name} ({persona.domain})")
        print(f"   🎵 Voice: {persona.voice}")
        print(f"   📝 Description: {voice_desc}")
        print()
    
    # Test voice summary
    print("\n📈 Voice Summary:")
    print("-" * 40)
    voice_summary = persona_service.get_voice_summary()
    for voice, data in voice_summary.items():
        print(f"🎵 {voice}: {data['count']} personas")
        print(f"   📝 {data['description']}")
        print(f"   👥 {', '.join(data['personas'])}")
        print()
    
    # Test available voices
    print("\n🎵 Available Voices:")
    print("-" * 40)
    voices = persona_service.get_available_voices()
    for voice, description in voices.items():
        print(f"🎵 {voice}: {description}")
    
    print("\n✅ Voice assignment test completed successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc() 
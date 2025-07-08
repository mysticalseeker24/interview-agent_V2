#!/usr/bin/env python3

"""
Test script to verify persona parsing is working correctly.
"""

import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

# Import the module
import interview_conversation

def test_persona_parsing():
    """Test that personas are parsed correctly and show unique details."""
    print("🧪 Testing persona parsing...")
    
    # Create conversation instance
    conversation = interview_conversation.InteractiveInterviewConversation()
    
    # Check if personas were loaded
    print(f"\n📊 Loaded {len(conversation.personas)} personas:")
    
    for persona_key, persona_data in conversation.personas.items():
        print(f"\n🎭 Persona Key: {persona_key}")
        print(f"   📝 Name: {persona_data['name']}")
        print(f"   🎯 Role: {persona_data['role']}")
        print(f"   🏢 Specialty: {persona_data['specialty']}")
        print(f"   📚 Background: {persona_data['background'][:100]}...")
        print(f"   📄 File: {persona_data['file'].name}")
    
    # Test display function
    print("\n" + "="*80)
    print("🎭 Testing display_personas() function:")
    conversation.display_personas()
    
    return len(conversation.personas) > 0

if __name__ == "__main__":
    success = test_persona_parsing()
    if success:
        print("\n✅ Persona parsing test completed successfully!")
    else:
        print("\n❌ Persona parsing test failed!")

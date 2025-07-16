#!/usr/bin/env python3
"""
Debug script for persona loading
"""

import logging
import sys
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent / "app"))

try:
    from app.services.persona_service import PersonaService
    
    print("🔍 Debugging Persona Service")
    print("=" * 50)
    
    # Create a new instance with debug logging
    persona_service = PersonaService()
    
    print(f"\n📁 Personas directory: {persona_service.personas_dir}")
    print(f"📁 Directory exists: {persona_service.personas_dir.exists()}")
    
    if persona_service.personas_dir.exists():
        print(f"\n📂 Contents of personas directory:")
        for item in persona_service.personas_dir.iterdir():
            print(f"  - {item.name} ({'dir' if item.is_dir() else 'file'})")
    
    print(f"\n👥 Total personas loaded: {len(persona_service.personas)}")
    
    if persona_service.personas:
        print("\n📋 Loaded personas:")
        for key, persona in persona_service.personas.items():
            print(f"  - {key}: {persona.name} ({persona.domain})")
    else:
        print("\n❌ No personas loaded!")
        
        # Check if persona files exist
        individuals_dir = persona_service.personas_dir / "individuals"
        jobs_dir = persona_service.personas_dir / "jobs"
        
        print(f"\n🔍 Checking individual personas: {individuals_dir}")
        if individuals_dir.exists():
            for file in individuals_dir.glob("*.txt"):
                print(f"  - Found: {file}")
        else:
            print("  - Directory not found")
            
        print(f"\n🔍 Checking domain personas: {jobs_dir}")
        if jobs_dir.exists():
            for domain_dir in jobs_dir.iterdir():
                if domain_dir.is_dir():
                    print(f"  - Domain: {domain_dir.name}")
                    for file in domain_dir.glob("*.txt"):
                        print(f"    - Found: {file}")
        else:
            print("  - Directory not found")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc() 
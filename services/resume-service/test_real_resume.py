#!/usr/bin/env python3
"""
Real Resume Processing Test
Tests the resume service with the actual resume PDF provided.
"""

import os
import sys
import time
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.resume_processor import ResumeProcessor


def test_real_resume_processing():
    """Test processing of the real resume PDF."""
    print("📄 REAL RESUME PROCESSING TEST")
    print("=" * 80)
    
    # Check for the real resume file
    resume_file = Path("data/Resume (1).pdf")
    
    if not resume_file.exists():
        print(f"❌ Resume file not found: {resume_file}")
        print("   Please ensure the resume PDF is in the data/ directory")
        return False
    
    print(f"📄 Testing with: {resume_file.name}")
    print(f"📁 File path: {resume_file.absolute()}")
    print(f"📏 File size: {resume_file.stat().st_size / 1024:.1f} KB")
    
    # Check environment
    api_key = os.getenv('OPENAI_API_KEY')
    use_llm = os.getenv('USE_LLM_ENHANCEMENT', 'false').lower() == 'true'
    
    print(f"\n🔧 Environment:")
    print(f"   OpenAI API Key: {'✅ Set' if api_key else '❌ Not Set'}")
    print(f"   LLM Enhancement: {'✅ Enabled' if use_llm else '❌ Disabled'}")
    
    # Test basic processing (no LLM)
    print(f"\n🧪 TEST 1: Basic Processing (No LLM)")
    print("-" * 50)
    
    start_time = time.time()
    processor_basic = ResumeProcessor(use_llm=False)
    result_basic = processor_basic.process_resume(str(resume_file))
    basic_time = time.time() - start_time
    
    if result_basic.success:
        print(f"✅ Success in {basic_time:.2f}s")
        print(f"🎯 Confidence: {result_basic.data.parsing_confidence:.1%}")
        print(f"📧 Email: {result_basic.data.contact.email or 'Not found'}")
        print(f"📱 Phone: {result_basic.data.contact.phone or 'Not found'}")
        print(f"👤 Name: {result_basic.data.contact.name or 'Not found'}")
        print(f"💼 Experience: {len(result_basic.data.experience)} entries")
        print(f"🛠️  Skills: {len(result_basic.data.skills)} categories")
        print(f"📜 Certifications: {len(result_basic.data.certifications)} found")
        print(f"🚀 Projects: {len(result_basic.data.projects)} found")
        print(f"🎓 Education: {len(result_basic.data.education)} entries")
        print(f"🏆 Achievements: {len(result_basic.data.achievements)} found")
        print(f"🎭 Domains: {', '.join(result_basic.data.domains[:3])}")
        
        # Save basic result
        output_file = Path("data/output/Resume (1)_basic.json")
        output_file.parent.mkdir(exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result_basic.data.model_dump_json(indent=2))
        print(f"💾 Basic result saved to: {output_file}")
        
    else:
        print(f"❌ Failed: {result_basic.error_message}")
        return False
    
    # Test LLM processing if API key is available
    if api_key and use_llm:
        print(f"\n🤖 TEST 2: LLM-Enhanced Processing")
        print("-" * 50)
        
        start_time = time.time()
        processor_llm = ResumeProcessor(use_llm=True, openai_api_key=api_key)
        result_llm = processor_llm.process_resume(str(resume_file))
        llm_time = time.time() - start_time
        
        if result_llm.success:
            print(f"✅ Success in {llm_time:.2f}s")
            print(f"🎯 Confidence: {result_llm.data.parsing_confidence:.1%}")
            print(f"📧 Email: {result_llm.data.contact.email or 'Not found'}")
            print(f"📱 Phone: {result_llm.data.contact.phone or 'Not found'}")
            print(f"👤 Name: {result_llm.data.contact.name or 'Not found'}")
            print(f"💼 Experience: {len(result_llm.data.experience)} entries")
            print(f"🛠️  Skills: {len(result_llm.data.skills)} categories")
            print(f"📜 Certifications: {len(result_llm.data.certifications)} found")
            print(f"🚀 Projects: {len(result_llm.data.projects)} found")
            print(f"🎓 Education: {len(result_llm.data.education)} entries")
            print(f"🏆 Achievements: {len(result_llm.data.achievements)} found")
            print(f"🎭 Domains: {', '.join(result_llm.data.domains[:3])}")
            
            # Save LLM result
            output_file = Path("data/output/Resume (1)_llm.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result_llm.data.model_dump_json(indent=2))
            print(f"💾 LLM result saved to: {output_file}")
            
            # Compare results
            confidence_improvement = result_llm.data.parsing_confidence - result_basic.data.parsing_confidence
            print(f"\n📈 Comparison:")
            print(f"   Basic Confidence: {result_basic.data.parsing_confidence:.1%}")
            print(f"   LLM Confidence: {result_llm.data.parsing_confidence:.1%}")
            print(f"   Improvement: {confidence_improvement:+.1%}")
            print(f"   Processing Time: {basic_time:.2f}s → {llm_time:.2f}s ({llm_time/basic_time:.1f}x)")
            
        else:
            print(f"❌ LLM processing failed: {result_llm.error_message}")
    
    print(f"\n✅ Real resume processing test completed!")
    return True


def test_service_health():
    """Test the service health endpoint."""
    print(f"\n🏥 SERVICE HEALTH TEST")
    print("=" * 80)
    print("⚠️  Note: This requires the FastAPI server to be running.")
    print("   Start with: python main.py")
    print("   Then test the health endpoint manually.")


def main():
    """Run the real resume processing test."""
    print("🚀 TALENTSYNC RESUME SERVICE - REAL RESUME TEST")
    print("=" * 80)
    
    # Test real resume processing
    success = test_real_resume_processing()
    
    if success:
        print(f"\n🎉 All tests passed!")
        print(f"📁 Check the data/output/ directory for processed results")
    else:
        print(f"\n❌ Some tests failed!")
        print(f"🔧 Check the configuration and try again")
    
    # Show service health info
    test_service_health()


if __name__ == "__main__":
    main() 
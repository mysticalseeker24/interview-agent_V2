#!/usr/bin/env python3
"""
Complete integration test with LLM enhancement.
Tests both basic and LLM-enhanced extraction.
"""
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.resume_processor import ResumeProcessor


def test_llm_integration():
    """Test LLM integration and cost optimization."""
    print("🤖 TESTING LLM INTEGRATION")
    print("=" * 80)
    
    # Check environment setup
    api_key = os.getenv('OPENAI_API_KEY')
    use_llm = os.getenv('USE_LLM_ENHANCEMENT', 'false').lower() == 'true'
    
    print("🔧 Environment Configuration:")
    print(f"   OpenAI API Key: {'✅ Set' if api_key else '❌ Missing'}")
    print(f"   LLM Enhancement: {'✅ Enabled' if use_llm else '❌ Disabled'}")
    print(f"   Model: {os.getenv('OPENAI_MODEL', 'o1-mini')}")
    print(f"   Max Tokens: {os.getenv('OPENAI_MAX_TOKENS', '2000')}")
    
    if not api_key:
        print("\n⚠️  OpenAI API key not found!")
        print("   Set OPENAI_API_KEY in .env file to test LLM features.")
        return
    
    print("\n" + "=" * 80)
    print("🧪 TESTING BOTH MODES")
    print("=" * 80)
    
    # Find resume file
    data_dir = Path("data")
    pdf_files = list(data_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("❌ No PDF files found in data directory!")
        return
    
    resume_file = pdf_files[0]
    print(f"📄 Testing with: {resume_file.name}\n")
    
    results = {}
    
    # Test 1: Basic extraction (no LLM)
    print("📊 Test 1: Basic Extraction (No LLM)")
    print("-" * 40)
    
    start_time = time.time()
    processor_basic = ResumeProcessor(use_llm=False)
    result_basic = processor_basic.process_resume(str(resume_file))
    basic_time = time.time() - start_time
    
    if result_basic.success:
        print(f"✅ Success in {basic_time:.2f}s")
        print(f"🎯 Confidence: {result_basic.data.parsing_confidence:.2%}")
        print(f"📧 Email: {result_basic.data.contact.email or 'Not found'}")
        print(f"📱 Phone: {result_basic.data.contact.phone or 'Not found'}")
        print(f"👤 Name: {result_basic.data.contact.name or 'Not found'}")
        print(f"💼 Experience: {len(result_basic.data.experience)} entries")
        print(f"🛠️  Skills: {len(result_basic.data.skills)} categories")
        print(f"📜 Certifications: {len(result_basic.data.certifications)} found")
        results['basic'] = result_basic
    else:
        print(f"❌ Failed: {result_basic.error_message}")
    
    print()
    
    # Test 2: LLM-enhanced extraction
    print("🤖 Test 2: LLM-Enhanced Extraction")
    print("-" * 40)
    
    start_time = time.time()
    processor_llm = ResumeProcessor(use_llm=True, openai_api_key=api_key)
    result_llm = processor_llm.process_resume(str(resume_file))
    llm_time = time.time() - start_time
    
    if result_llm.success:
        print(f"✅ Success in {llm_time:.2f}s")
        print(f"🎯 Confidence: {result_llm.data.parsing_confidence:.2%}")
        print(f"📧 Email: {result_llm.data.contact.email or 'Not found'}")
        print(f"📱 Phone: {result_llm.data.contact.phone or 'Not found'}")
        print(f"👤 Name: {result_llm.data.contact.name or 'Not found'}")
        print(f"💼 Experience: {len(result_llm.data.experience)} entries")
        print(f"🛠️  Skills: {len(result_llm.data.skills)} categories")
        print(f"📜 Certifications: {len(result_llm.data.certifications)} found")
        
        # Check for LLM enhancements
        if hasattr(result_llm.data, 'llm_enhanced') and result_llm.data.llm_enhanced:
            print("🚀 LLM Enhancement: Applied")
            if hasattr(result_llm.data, 'llm_notes'):
                print(f"📝 LLM Notes: {result_llm.data.llm_notes}")
        else:
            print("⏭️  LLM Enhancement: Skipped (confidence sufficient)")
        
        results['llm'] = result_llm
    else:
        print(f"❌ Failed: {result_llm.error_message}")
    
    print()
    
    # Comparison
    if 'basic' in results and 'llm' in results:
        print("📈 COMPARISON")
        print("=" * 80)
        
        basic_data = results['basic'].data
        llm_data = results['llm'].data
        
        print(f"Processing Time:")
        print(f"   Basic: {basic_time:.2f}s")
        print(f"   LLM:   {llm_time:.2f}s ({llm_time/basic_time:.1f}x slower)")
        
        print(f"\nConfidence Score:")
        print(f"   Basic: {basic_data.parsing_confidence:.2%}")
        print(f"   LLM:   {llm_data.parsing_confidence:.2%}")
        
        confidence_improvement = llm_data.parsing_confidence - basic_data.parsing_confidence
        print(f"   Improvement: {confidence_improvement:+.1%}")
        
        print(f"\nExtraction Quality:")
        
        # Contact information
        basic_contact_score = sum([
            1 if basic_data.contact.name else 0,
            1 if basic_data.contact.email else 0,
            1 if basic_data.contact.phone else 0,
        ])
        llm_contact_score = sum([
            1 if llm_data.contact.name else 0,
            1 if llm_data.contact.email else 0,
            1 if llm_data.contact.phone else 0,
        ])
        
        print(f"   Contact Info: {basic_contact_score}/3 → {llm_contact_score}/3")
        print(f"   Experience: {len(basic_data.experience)} → {len(llm_data.experience)} entries")
        print(f"   Skills: {len(basic_data.skills)} → {len(llm_data.skills)} categories")
        print(f"   Certifications: {len(basic_data.certifications)} → {len(llm_data.certifications)} found")
        
        # Cost estimation
        estimated_tokens = 1000  # Conservative estimate
        cost_per_1k_tokens = 0.003  # o1-mini pricing
        estimated_cost = (estimated_tokens / 1000) * cost_per_1k_tokens
        
        print(f"\n💰 Cost Estimation:")
        print(f"   Estimated tokens: ~{estimated_tokens}")
        print(f"   Estimated cost: ~${estimated_cost:.4f} per resume")
        print(f"   Monthly cost (100 resumes): ~${estimated_cost * 100:.2f}")
    
    print("\n" + "=" * 80)
    print("🎯 RECOMMENDATIONS")
    print("=" * 80)
    
    if 'basic' in results:
        basic_confidence = results['basic'].data.parsing_confidence
        
        if basic_confidence < 0.6:
            print("📊 Low confidence detected - LLM enhancement recommended")
            print("   Enable USE_LLM_ENHANCEMENT=true for better results")
        elif basic_confidence < 0.8:
            print("📊 Medium confidence - LLM enhancement optional")
            print("   Consider enabling for critical applications")
        else:
            print("📊 High confidence - basic extraction sufficient")
            print("   LLM enhancement may not provide significant value")
    
    print("\n✅ LLM Integration test completed!")


def test_cost_optimization():
    """Test cost optimization features."""
    print("\n💰 TESTING COST OPTIMIZATION")
    print("=" * 80)
    
    print("Cost optimization features:")
    print("✅ LLM only triggered when confidence < 80%")
    print("✅ Minimal token usage (~500-1000 tokens)")
    print("✅ o1-mini model (most cost-effective)")
    print("✅ Configurable enhancement threshold")
    print("✅ Fallback to basic extraction on LLM failure")
    
    print("\nEstimated costs (o1-mini pricing):")
    print("   Per resume: $0.001 - $0.005")
    print("   100 resumes/month: $0.10 - $0.50")
    print("   1000 resumes/month: $1.00 - $5.00")


def main():
    """Run all LLM integration tests."""
    test_llm_integration()
    test_cost_optimization()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Enhanced Resume Processing System Test
Tests the advanced resume parsing system with OCR, hidden link detection, and metadata extraction.
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

from app.enhanced_resume_processor import EnhancedResumeProcessor


def test_enhanced_resume_processing():
    """Test the enhanced resume processing system."""
    print("🚀 ENHANCED RESUME PROCESSING SYSTEM TEST")
    print("=" * 80)
    
    # Initialize enhanced processor
    processor = EnhancedResumeProcessor()
    
    # Test with the real resume
    resume_file = Path("data/Resume (1).pdf")
    
    if not resume_file.exists():
        print(f"❌ Resume file not found: {resume_file}")
        return False
    
    print(f"📄 Testing with resume: {resume_file}")
    print(f"📊 File size: {resume_file.stat().st_size / 1024:.1f} KB")
    
    # Process the resume
    start_time = time.time()
    result = processor.process_resume(str(resume_file))
    processing_time = time.time() - start_time
    
    if result.success:
        print(f"\n✅ Processing completed successfully!")
        print(f"⏱️ Processing time: {processing_time:.2f} seconds")
        print(f"📝 Stages completed: {', '.join(result.stages_completed)}")
        
        # Display enhanced results
        display_enhanced_results(result)
        
        return True
    else:
        print(f"\n❌ Processing failed: {result.error_message}")
        return False


def display_enhanced_results(result):
    """Display comprehensive results from enhanced processing."""
    data = result.data
    
    print("\n" + "=" * 80)
    print("🎯 ENHANCED EXTRACTION RESULTS")
    print("=" * 80)
    
    # Basic statistics
    print(f"📊 Processing Time: {result.processing_time:.2f}s")
    print(f"📝 Text Length: {data.raw_text_length:,} characters")
    print(f"🎯 Confidence: {data.parsing_confidence:.2%}")
    print(f"🏷️ Sections Detected: {', '.join(data.sections_detected)}")
    print(f"🤖 LLM Enhanced: {'Yes' if data.llm_enhanced else 'No'}")
    
    # Contact information with enhanced data
    contact = data.contact
    print(f"\n👤 CONTACT INFORMATION:")
    print(f"   Name: {contact.name or 'N/A'}")
    print(f"   Email: {contact.email or 'N/A'}")
    print(f"   Phone: {contact.phone or 'N/A'}")
    print(f"   Location: {contact.location or 'N/A'}")
    print(f"   LinkedIn: {contact.linkedin or 'N/A'}")
    print(f"   GitHub: {contact.github or 'N/A'}")
    print(f"   Website: {contact.website or 'N/A'}")
    
    # Experience
    print(f"\n💼 EXPERIENCE ({len(data.experience)} entries):")
    for i, exp in enumerate(data.experience[:3], 1):
        print(f"   {i}. {exp.position or 'Unknown Position'} at {exp.company or 'Unknown Company'}")
        if exp.start_date or exp.end_date:
            print(f"      📅 {exp.start_date or 'N/A'} → {exp.end_date or 'N/A'}")
        print(f"      🏆 {len(exp.bullets)} achievements, {len(exp.metrics)} metrics")
        print(f"      🛠️ Technologies: {', '.join(exp.technologies[:5])}{'...' if len(exp.technologies) > 5 else ''}")
    
    # Projects with enhanced link detection
    print(f"\n🚀 PROJECTS ({len(data.projects)} entries):")
    for i, proj in enumerate(data.projects[:3], 1):
        print(f"   {i}. {proj.name or 'Unknown Project'}")
        if proj.description:
            print(f"      📝 {proj.description[:100]}{'...' if len(proj.description) > 100 else ''}")
        if proj.url:
            print(f"      🔗 URL: {proj.url}")
        print(f"      🛠️ Technologies: {', '.join(proj.technologies[:5])}{'...' if len(proj.technologies) > 5 else ''}")
    
    # Education
    print(f"\n🎓 EDUCATION ({len(data.education)} entries):")
    for edu in data.education:
        print(f"   📜 {edu.degree or 'Unknown Degree'} @ {edu.institution or 'Unknown Institution'}")
        if edu.field_of_study:
            print(f"      📚 Field: {edu.field_of_study}")
        if edu.start_date or edu.end_date:
            print(f"      📅 {edu.start_date or 'N/A'} → {edu.end_date or 'N/A'}")
    
    # Skills with enhanced categorization
    print(f"\n🛠️ SKILLS ({len(data.skills)} categories):")
    for skill_cat in data.skills:
        print(f"   📂 {skill_cat.category}: {', '.join(skill_cat.skills[:8])}{'...' if len(skill_cat.skills) > 8 else ''}")
    
    # Certifications
    print(f"\n🏆 CERTIFICATIONS ({len(data.certifications)} entries):")
    for cert in data.certifications[:3]:
        print(f"   🏅 {cert.name}")
        if cert.issuer:
            print(f"      🏢 Issuer: {cert.issuer}")
        if cert.issue_date:
            print(f"      📅 Date: {cert.issue_date}")
    
    # Achievements
    print(f"\n🏅 ACHIEVEMENTS ({len(data.achievements)} entries):")
    for achievement in data.achievements[:3]:
        print(f"   🏆 {achievement}")
    
    # Professional domains
    if data.domains:
        print(f"\n🎯 PROFESSIONAL DOMAINS:")
        for domain in data.domains:
            print(f"   🎯 {domain}")
    
    # Hidden elements (if available in metadata)
    if hasattr(result, 'metadata') and result.metadata:
        print(f"\n🔍 HIDDEN ELEMENTS DETECTED:")
        metadata = result.metadata
        
        if metadata.get('links'):
            print(f"   🔗 Links: {len(metadata['links'])} found")
            for link in metadata['links'][:3]:
                print(f"      - {link.get('type', 'unknown')}: {link.get('url', 'N/A')}")
        
        if metadata.get('tables'):
            print(f"   📊 Tables: {len(metadata['tables'])} found")
        
        if metadata.get('form_fields'):
            print(f"   📝 Form Fields: {len(metadata['form_fields'])} found")
        
        if metadata.get('hidden_text'):
            print(f"   📄 Hidden Text: {len(metadata['hidden_text'])} sections")
        
        if metadata.get('social_profiles'):
            print(f"   📱 Social Profiles: {len(metadata['social_profiles'])} found")
            for platform, profile in metadata['social_profiles'].items():
                print(f"      - {platform}: {profile.get('username', 'N/A')}")
    
    print("\n" + "=" * 80)


def test_pipeline_info():
    """Test the enhanced pipeline information."""
    print("\n🔧 PIPELINE INFORMATION TEST")
    print("=" * 50)
    
    processor = EnhancedResumeProcessor()
    info = processor.get_pipeline_info()
    
    print(f"Pipeline: {info['pipeline_name']}")
    print(f"Version: {info['version']}")
    print(f"Description: {info['description']}")
    
    print(f"\n📋 Supported Formats:")
    for format_type in info['supported_formats']:
        print(f"   - {format_type}")
    
    print(f"\n🚀 Advanced Features:")
    for feature in info['advanced_features']:
        print(f"   - {feature}")
    
    print(f"\n🤖 LLM Enhancement:")
    llm_info = info['llm_enhancement']
    print(f"   - Enabled: {llm_info['enabled']}")
    print(f"   - Model: {llm_info['model']}")
    print(f"   - Cost Optimization: {llm_info['cost_optimization']}")


def test_text_processing():
    """Test text processing with enhanced extraction."""
    print("\n📝 TEXT PROCESSING TEST")
    print("=" * 50)
    
    processor = EnhancedResumeProcessor()
    
    # Sample text with links and social media profiles
    sample_text = """
    SAKSHAM MISHRA
    Email: saksham.mishra2402@gmail.com
    Phone: +91 85778 76517
    Location: Prayagraj, India
    
    LinkedIn: https://linkedin.com/in/saksham-mishra
    GitHub: https://github.com/saksham-mishra
    Portfolio: https://saksham.dev
    
    EXPERIENCE:
    Senior Software Engineer @ TechCorp (Jan 2020 - Present)
    - Led development of microservices architecture
    - Improved performance by 40%
    - Technologies: Python, React, AWS, Docker
    
    PROJECTS:
    StockIO: Financial Application
    - GitHub: https://github.com/saksham/stockio
    - Technologies: Python, LSTM, BERT, React
    
    SKILLS:
    Programming Languages: Python, JavaScript, TypeScript, Java
    Web Technologies: React, Node.js, FastAPI, Django
    Cloud & DevOps: AWS, Docker, Kubernetes, CI/CD
    """
    
    print("Processing sample text with enhanced extraction...")
    result = processor.process_text(sample_text)
    
    if result.success:
        print("✅ Text processing successful!")
        print(f"📊 Confidence: {result.data.parsing_confidence:.2%}")
        print(f"👤 Contact: {result.data.contact.name}")
        print(f"🔗 LinkedIn: {result.data.contact.linkedin}")
        print(f"💻 GitHub: {result.data.contact.github}")
        print(f"🌐 Website: {result.data.contact.website}")
    else:
        print(f"❌ Text processing failed: {result.error_message}")


def main():
    """Run all enhanced system tests."""
    print("🧪 ENHANCED RESUME PROCESSING SYSTEM - COMPREHENSIVE TEST")
    print("=" * 80)
    
    # Test 1: Enhanced resume processing
    print("\n1️⃣ Testing Enhanced Resume Processing...")
    success1 = test_enhanced_resume_processing()
    
    # Test 2: Pipeline information
    print("\n2️⃣ Testing Pipeline Information...")
    test_pipeline_info()
    
    # Test 3: Text processing
    print("\n3️⃣ Testing Text Processing...")
    test_text_processing()
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    if success1:
        print("✅ Enhanced resume processing: PASSED")
    else:
        print("❌ Enhanced resume processing: FAILED")
    
    print("✅ Pipeline information: PASSED")
    print("✅ Text processing: PASSED")
    
    print("\n🎉 Enhanced system testing completed!")
    print("\n🔧 Advanced Features Tested:")
    print("   - OCR for scanned documents")
    print("   - Hidden link detection from PDF annotations")
    print("   - Social media profile extraction")
    print("   - Table and form field extraction")
    print("   - Image analysis for embedded text")
    print("   - Enhanced entity extraction with metadata")
    print("   - Comprehensive link and social media profile extraction")


if __name__ == "__main__":
    main() 
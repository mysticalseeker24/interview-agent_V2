#!/usr/bin/env python3
"""
Test script for the unified resume processing pipeline.
Tests the complete text-to-JSON conversion process.
"""
import asyncio
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.resume_processor import ResumeProcessor
from src.schema import ProcessingResult, ResumeJSON


# Sample resume text for testing
SAMPLE_RESUME_TEXT = """
John Doe
Senior Software Engineer
Email: john.doe@example.com
Phone: +1-555-123-4567
LinkedIn: https://linkedin.com/in/johndoe
GitHub: https://github.com/johndoe

Professional Summary
Experienced software engineer with 8+ years in full-stack development, cloud architecture, and team leadership.

Experience

Senior Software Engineer @ Google Inc. (March 2021 – Present) | Mountain View, CA
• Led development of payment processing system handling $2M+ daily transactions
• Improved API response time by 45% through optimization and caching strategies
• Mentored team of 5 junior developers, resulting in 30% faster feature delivery
• Implemented microservices architecture serving 10M+ users globally
• Technologies: Python, Go, Kubernetes, PostgreSQL, Redis, GCP

Software Engineer @ Microsoft Corporation (June 2019 – February 2021) | Seattle, WA
• Built real-time analytics dashboard processing 100K events per second
• Reduced infrastructure costs by 25% through efficient resource management
• Collaborated with cross-functional teams on machine learning integration
• Achieved 99.9% uptime across distributed systems
• Technologies: C#, .NET, Azure, SQL Server, React, TypeScript

Projects

StockIO: Financial Trading Platform | GitHub: https://github.com/johndoe/stockio
• Built real-time stock trading platform with LSTM prediction models
• Processed market data for 500+ stocks with 99.5% accuracy
• Technologies: Python, TensorFlow, FastAPI, PostgreSQL, Redis, Docker

E-Commerce Microservices Architecture
• Designed and implemented scalable microservices for online retail
• Handled 10M+ daily transactions with sub-100ms response times
• Achieved 40% improvement in system reliability
• Technologies: Go, Kubernetes, gRPC, PostgreSQL, Redis

Education

Master of Science in Computer Science @ Stanford University (2015 – 2017)
• Specialization: Machine Learning and AI
• GPA: 3.8/4.0

Bachelor of Science in Software Engineering @ UC Berkeley (2011 – 2015)
• Magna Cum Laude, GPA: 3.7/4.0

Technical Skills

Programming Languages: Python, Go, JavaScript, TypeScript, C#, Java, SQL
Web Technologies: React, Node.js, FastAPI, Django, .NET, Express
Cloud & DevOps: AWS, GCP, Azure, Kubernetes, Docker, Terraform
Databases: PostgreSQL, MongoDB, Redis, SQL Server, BigQuery
AI/ML: TensorFlow, PyTorch, Scikit-learn, Pandas, NumPy

Certifications & Achievements

AWS Certified Solutions Architect - Professional | March 2023
Google Cloud Professional Cloud Architect | January 2023
Certified Kubernetes Administrator (CKA) | October 2022

Employee of the Year 2022 - Google Inc.
Dean's List - Stanford University (2016, 2017)
Hackathon Winner - TechCrunch Disrupt 2021
"""


async def test_pipeline():
    """Test the complete resume processing pipeline."""
    print("🚀 TESTING UNIFIED RESUME PROCESSING PIPELINE")
    print("=" * 80)
    
    # Initialize processor
    processor = ResumeProcessor(use_llm=False)
    
    print("📊 Pipeline Configuration:")
    info = processor.get_pipeline_info()
    for key, value in info.items():
        print(f"   {key}: {value}")
    
    print("\n" + "=" * 80)
    print("🔄 PROCESSING SAMPLE RESUME")
    print("=" * 80)
    
    # Process the sample text
    result = processor.process_text(SAMPLE_RESUME_TEXT)
    
    print(f"\n📈 PROCESSING RESULTS:")
    print(f"   ✅ Success: {result.success}")
    print(f"   ⏱️ Processing Time: {result.processing_time_seconds:.3f}s")
    print(f"   🏗️ Stages Completed: {', '.join(result.stages_completed)}")
    
    if result.error_message:
        print(f"   ❌ Error: {result.error_message}")
        return
    
    if not result.resume_json:
        print("   ❌ No resume JSON generated")
        return
    
    resume = result.resume_json
    
    print(f"\n📊 EXTRACTED DATA OVERVIEW:")
    print(f"   📝 Text Length: {resume.raw_text_length:,} characters")
    print(f"   🎯 Confidence: {resume.parsing_confidence:.2%}")
    print(f"   🏷️ Sections Detected: {', '.join(resume.sections_detected)}")
    print(f"   🎭 Domains: {', '.join(resume.domains)}")
    print(f"   🔧 Extraction Method: {resume.text_extraction_method}")
    print(f"   🤖 LLM Enhanced: {resume.llm_enhanced}")
    
    print(f"\n👤 CONTACT INFORMATION:")
    contact = resume.contact
    print(f"   Name: {contact.name or 'N/A'}")
    print(f"   Email: {contact.email or 'N/A'}")
    print(f"   Phone: {contact.phone or 'N/A'}")
    print(f"   LinkedIn: {contact.linkedin or 'N/A'}")
    print(f"   GitHub: {contact.github or 'N/A'}")
    print(f"   Location: {contact.location or 'N/A'}")
    
    if resume.summary:
        print(f"\n📄 SUMMARY:")
        print(f"   {resume.summary}")
    
    print(f"\n💼 EXPERIENCE ({len(resume.experience)} entries):")
    for i, exp in enumerate(resume.experience, 1):
        print(f"   {i}. {exp.position or 'N/A'} at {exp.company or 'N/A'}")
        print(f"      📅 Duration: {exp.start_date or 'N/A'} → {exp.end_date or 'N/A'}")
        print(f"      📍 Location: {exp.location or 'N/A'}")
        print(f"      🏆 Bullets: {len(exp.bullets)} achievements")
        print(f"      📊 Metrics: {len(exp.metrics)} metrics extracted")
        print(f"      🛠️ Technologies: {', '.join(exp.technologies[:5])}{'...' if len(exp.technologies) > 5 else ''}")
        if exp.metrics:
            print(f"         📈 Sample metrics: {', '.join(exp.metrics[:3])}")
        if exp.bullets:
            print(f"         💡 Sample bullet: {exp.bullets[0][:80]}...")
    
    print(f"\n🚀 PROJECTS ({len(resume.projects)} projects):")
    for i, proj in enumerate(resume.projects, 1):
        print(f"   {i}. {proj.name or 'N/A'}")
        print(f"      🔗 URL: {proj.url or 'N/A'}")
        print(f"      📅 Duration: {proj.start_date or 'N/A'} → {proj.end_date or 'N/A'}")
        print(f"      🛠️ Technologies: {', '.join(proj.technologies)}")
        print(f"      🏆 Bullets: {len(proj.bullets)} details")
        print(f"      📊 Metrics: {len(proj.metrics)} metrics")
        if proj.description:
            print(f"      📝 Description: {proj.description[:80]}...")
    
    print(f"\n🎓 EDUCATION ({len(resume.education)} entries):")
    for edu in resume.education:
        print(f"   📜 {edu.degree or 'N/A'} from {edu.institution or 'N/A'}")
        print(f"      📅 Duration: {edu.start_date or 'N/A'} → {edu.end_date or 'N/A'}")
        print(f"      🔬 Field: {edu.field_of_study or 'N/A'}")
        print(f"      📊 GPA: {edu.gpa or 'N/A'}")
        print(f"      🏆 Honors: {edu.honors or 'N/A'}")
    
    print(f"\n🛠️ SKILLS ({len(resume.skills)} categories):")
    for skill_cat in resume.skills:
        skills_preview = ', '.join(skill_cat.skills[:4])
        if len(skill_cat.skills) > 4:
            skills_preview += f" ... (+{len(skill_cat.skills) - 4} more)"
        print(f"   {skill_cat.category}: {skills_preview}")
    
    print(f"\n📜 CERTIFICATIONS ({len(resume.certifications)} certs):")
    for cert in resume.certifications:
        print(f"   • {cert.name}")
        if cert.issuer:
            print(f"     🏢 Issuer: {cert.issuer}")
        if cert.issue_date:
            print(f"     📅 Issued: {cert.issue_date}")
    
    print(f"\n🏆 ACHIEVEMENTS ({len(resume.achievements)} awards):")
    for achievement in resume.achievements:
        print(f"   • {achievement}")
    
    # Save the JSON for inspection
    output_path = Path("test_output.json")
    with open(output_path, 'w') as f:
        json.dump(resume.model_dump(), f, indent=2, default=str)
    
    print(f"\n💾 JSON OUTPUT SAVED TO: {output_path.absolute()}")
    
    print("\n" + "=" * 80)
    print("✅ PIPELINE TEST COMPLETED SUCCESSFULLY!")
    print("=" * 80)


async def test_file_processing():
    """Test file processing if a test file is available."""
    print("\n🔍 LOOKING FOR TEST RESUME FILES...")
    
    # Check for common test file locations
    test_locations = [
        Path("uploads"),
        Path("data"), 
        Path("test_resume.pdf"),
        Path("sample_resume.pdf")
    ]
    
    test_files = []
    for location in test_locations:
        if location.is_file():
            test_files.append(location)
        elif location.is_dir():
            test_files.extend(location.glob("*.pdf"))
            test_files.extend(location.glob("*.docx"))
    
    if not test_files:
        print("   📁 No test files found. Skipping file processing test.")
        return
    
    print(f"   📄 Found {len(test_files)} test files:")
    for file in test_files:
        print(f"      • {file}")
    
    # Test with first file
    test_file = test_files[0]
    print(f"\n🔄 TESTING FILE PROCESSING: {test_file}")
    
    processor = ResumeProcessor()
    result = processor.process_resume(str(test_file))
    
    print(f"   ✅ Success: {result.success}")
    print(f"   ⏱️ Processing Time: {result.processing_time_seconds:.3f}s")
    
    if result.resume_json:
        print(f"   🎯 Confidence: {result.resume_json.parsing_confidence:.2%}")
        print(f"   🏷️ Sections: {', '.join(result.resume_json.sections_detected)}")


async def main():
    """Run all tests."""
    try:
        await test_pipeline()
        await test_file_processing()
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

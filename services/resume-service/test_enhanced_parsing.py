"""
Test script for the enhanced resume parsing service.
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent / "app"))

from app.services.advanced_resume_parser import AdvancedResumeParser
from app.services.resume_parsing_service import ResumeParsingService

# Sample resume text for testing
SAMPLE_RESUME_TEXT = """
John Doe
Software Engineer
Email: john.doe@example.com
Phone: +1 (555) 123-4567
LinkedIn: https://linkedin.com/in/johndoe
GitHub: https://github.com/johndoe

PROFESSIONAL SUMMARY
Experienced software engineer with 5+ years of experience in full-stack development, 
specializing in Python, JavaScript, and cloud technologies.

EXPERIENCE

Senior Software Engineer at Google
January 2022 - Present
• Developed scalable web applications using React, Node.js, and Python
• Implemented microservices architecture using Docker and Kubernetes
• Worked with PostgreSQL, Redis, and MongoDB databases
• Used AWS services including Lambda, S3, and RDS

Software Developer at Microsoft
June 2019 - December 2021
• Built REST APIs using Django and Flask frameworks
• Implemented CI/CD pipelines using Jenkins and GitHub Actions
• Collaborated with cross-functional teams using Agile methodologies

EDUCATION

Master of Science in Computer Science
Stanford University
September 2017 - May 2019
GPA: 3.8/4.0

Bachelor of Science in Software Engineering
UC Berkeley
September 2013 - May 2017
GPA: 3.6/4.0

SKILLS
Programming Languages: Python, JavaScript, Java, TypeScript, Go
Web Technologies: React, Angular, Node.js, Django, Flask, HTML, CSS
Databases: PostgreSQL, MySQL, MongoDB, Redis
Cloud & DevOps: AWS, Docker, Kubernetes, Jenkins, Terraform
AI/ML: TensorFlow, PyTorch, Scikit-learn, Pandas, NumPy

PROJECTS

E-commerce Platform
• Built a full-stack e-commerce platform using React and Django
• Implemented payment processing with Stripe API
• Technologies: React, Django, PostgreSQL, Redis, AWS

Machine Learning Recommendation System
• Developed a recommendation system for Netflix-like platform
• Used collaborative filtering and content-based filtering
• Technologies: Python, TensorFlow, Pandas, AWS Lambda

CERTIFICATIONS
AWS Certified Solutions Architect
Google Cloud Professional Developer
Certified Kubernetes Administrator (CKA)

LANGUAGES
English (Native)
Spanish (Fluent)
French (Conversational)
"""


async def test_basic_parsing():
    """Test basic resume parsing functionality."""
    print("=" * 60)
    print("TESTING BASIC RESUME PARSING")
    print("=" * 60)
    
    # Test the parsing service
    parser = ResumeParsingService()
    result = parser.parse_resume(SAMPLE_RESUME_TEXT)
    
    print(f"📊 Parsing Results:")
    print(f"   Raw text length: {result.raw_text_length}")
    print(f"   Sections found: {result.sections_found}")
    print(f"   Total experience: {result.total_experience_years} years")
    
    print(f"\n👤 Contact Information:")
    print(f"   Name: {result.contact_info.name}")
    print(f"   Email: {result.contact_info.email}")
    print(f"   Phone: {result.contact_info.phone}")
    print(f"   LinkedIn: {result.contact_info.linkedin}")
    print(f"   GitHub: {result.contact_info.github}")
    
    print(f"\n🛠️ Skills by Category:")
    for skill_category in result.skills:
        print(f"   {skill_category.category}: {', '.join(skill_category.skills[:5])}{'...' if len(skill_category.skills) > 5 else ''}")
    
    print(f"\n💼 Work Experience:")
    for i, exp in enumerate(result.experience[:3]):  # Show first 3
        print(f"   {i+1}. {exp.position or 'N/A'} at {exp.company or 'N/A'}")
        if exp.start_date or exp.end_date:
            print(f"      Duration: {exp.start_date or 'N/A'} - {exp.end_date or 'Present'}")
    
    print(f"\n🎓 Education:")
    for edu in result.education:
        print(f"   {edu.degree or 'N/A'} from {edu.institution or 'N/A'}")
    
    print(f"\n🚀 Projects:")
    for proj in result.projects[:3]:  # Show first 3
        print(f"   {proj.name or 'N/A'}")
        if proj.technologies:
            print(f"      Technologies: {', '.join(proj.technologies[:3])}{'...' if len(proj.technologies) > 3 else ''}")
    
    print(f"\n📜 Certifications:")
    for cert in result.certifications:
        print(f"   {cert.name}")
    
    print(f"\n🌐 Languages:")
    for lang in result.languages:
        print(f"   {lang.language}: {lang.proficiency or 'N/A'}")
    
    return result


async def test_advanced_parsing():
    """Test advanced parsing features."""
    print("\n\n" + "=" * 60)
    print("TESTING ADVANCED PARSING FEATURES")
    print("=" * 60)
    
    # Test the advanced parser directly
    advanced_parser = AdvancedResumeParser()
    result = advanced_parser.parse_resume_advanced(SAMPLE_RESUME_TEXT)
    
    print(f"📊 Advanced Parsing Results:")
    print(f"   Sections detected: {len(result.sections_found)}")
    print(f"   Section types: {', '.join(result.sections_found)}")
    
    # Test section detection
    sections = advanced_parser.detect_sections(SAMPLE_RESUME_TEXT)
    print(f"\n📋 Section Detection:")
    for section, content in sections.items():
        print(f"   {section}: {len(content)} characters")
    
    # Test contact extraction
    contact = advanced_parser.extract_contact_info(SAMPLE_RESUME_TEXT)
    print(f"\n👤 Contact Extraction Test:")
    print(f"   Name: {contact.name}")
    print(f"   Email: {contact.email}")
    print(f"   Phone: {contact.phone}")
    print(f"   LinkedIn: {contact.linkedin}")
    print(f"   GitHub: {contact.github}")
    
    # Test skills extraction
    skills = advanced_parser.extract_skills(SAMPLE_RESUME_TEXT, sections)
    print(f"\n🛠️ Skills Extraction Test:")
    for skill_cat in skills:
        print(f"   {skill_cat.category} ({len(skill_cat.skills)}): {', '.join(skill_cat.skills[:3])}{'...' if len(skill_cat.skills) > 3 else ''}")
    
    return result


async def test_pdf_extraction():
    """Test PDF text extraction if available."""
    print("\n\n" + "=" * 60)
    print("TESTING PDF TEXT EXTRACTION")
    print("=" * 60)
    
    # Look for PDF files in uploads directory
    uploads_dir = Path("uploads")
    pdf_files = list(uploads_dir.glob("*.pdf")) if uploads_dir.exists() else []
    
    if not pdf_files:
        print("❌ No PDF files found in uploads directory for testing")
        return
    
    parser = AdvancedResumeParser()
    
    for pdf_file in pdf_files[:2]:  # Test first 2 PDFs
        print(f"\n📄 Testing PDF: {pdf_file.name}")
        try:
            text = parser.extract_text_from_pdf_advanced(str(pdf_file))
            print(f"   ✅ Extracted {len(text)} characters")
            print(f"   Preview: {text[:200]}...")
            
            # Test parsing the extracted text
            result = parser.parse_resume_advanced(text)
            print(f"   📊 Parsing results: {len(result.skills)} skill categories, {len(result.experience)} experience entries")
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")


async def test_error_handling():
    """Test error handling and edge cases."""
    print("\n\n" + "=" * 60)
    print("TESTING ERROR HANDLING")
    print("=" * 60)
    
    parser = ResumeParsingService()
    
    # Test empty text
    print("📝 Testing empty text...")
    result = parser.parse_resume("")
    print(f"   ✅ Empty text handled: {len(result.skills)} skills found")
    
    # Test malformed text
    print("📝 Testing malformed text...")
    malformed_text = "This is not a resume just random text with no structure!"
    result = parser.parse_resume(malformed_text)
    print(f"   ✅ Malformed text handled: {len(result.skills)} skills found")
    
    # Test very long text
    print("📝 Testing very long text...")
    long_text = SAMPLE_RESUME_TEXT * 100  # Repeat 100 times
    result = parser.parse_resume(long_text)
    print(f"   ✅ Long text handled: {len(result.skills)} skills found")


def performance_comparison():
    """Compare performance between basic and advanced parsing."""
    print("\n\n" + "=" * 60)
    print("PERFORMANCE COMPARISON")
    print("=" * 60)
    
    import time
    
    parser = ResumeParsingService()
    
    # Test basic parsing time
    start_time = time.time()
    result_basic = parser._parse_resume_legacy(SAMPLE_RESUME_TEXT)
    basic_time = time.time() - start_time
    
    # Test advanced parsing time
    start_time = time.time()
    result_advanced = parser.parse_resume(SAMPLE_RESUME_TEXT)
    advanced_time = time.time() - start_time
    
    print(f"⏱️  Basic parsing time: {basic_time:.3f} seconds")
    print(f"⏱️  Advanced parsing time: {advanced_time:.3f} seconds")
    print(f"📊 Speed ratio: {advanced_time/basic_time:.2f}x")
    
    print(f"\n📈 Results comparison:")
    print(f"   Basic skills found: {len(result_basic.skills)} categories")
    print(f"   Advanced skills found: {len(result_advanced.skills)} categories")
    print(f"   Basic experience: {result_basic.total_experience_years} years")
    print(f"   Advanced experience: {result_advanced.total_experience_years} years")


async def main():
    """Run all tests."""
    print("🚀 ENHANCED RESUME PARSING TEST SUITE")
    print("=" * 60)
    
    try:
        # Run all tests
        await test_basic_parsing()
        await test_advanced_parsing()
        await test_pdf_extraction()
        await test_error_handling()
        performance_comparison()
        
        print("\n\n" + "=" * 60)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

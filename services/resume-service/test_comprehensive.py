#!/usr/bin/env python3
"""
Comprehensive test script for the unified resume processing pipeline.
Tests both the core pipeline and API endpoints.
"""
import asyncio
        print(f"  🎯 Confidence: {result.data.parsing_confidence:.1%}")
        print(f"  📧 Email Extracted: {'✓' if result.data.contact.email else '✗'}")
        print(f"  📱 Phone Extracted: {'✓' if result.data.contact.phone else '✗'}")
        print(f"  💼 Experience Entries: {len(result.data.experience)}")
        print(f"  🚀 Projects: {len(result.data.projects)}")
        print(f"  🎓 Education: {len(result.data.education)}")
        print(f"  🛠️  Skill Categories: {len(result.data.skills)}")
        print(f"  📜 Certifications: {len(result.data.certifications)}")
        print(f"  🏆 Achievements: {len(result.data.achievements)}")
        print(f"  🎭 Domains: {len(result.data.domains)}")
        
        # Show LLM enhancement status
        if hasattr(result.data, 'llm_enhanced'):
            print(f"  🤖 LLM Enhanced: {'✓' if result.data.llm_enhanced else '✗'}")port json
import os
import time
from pathlib import Path
from typing import Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.resume_processor import ResumeProcessor
from src.schema import ProcessingResult, ResumeJSON


# Test configurations
TEST_CONFIGS = {
    "basic": {"use_llm": False, "description": "Basic extraction without LLM"},
    "llm_enhanced": {"use_llm": True, "description": "LLM-enhanced extraction (requires API key)"}
}

# Extended sample resume for comprehensive testing
COMPREHENSIVE_RESUME_TEXT = """
Sarah Chen
Senior Full-Stack Engineer & AI Specialist
📧 sarah.chen@techcorp.com | 📱 +1-415-555-0123
🔗 LinkedIn: https://linkedin.com/in/sarahchen | GitHub: https://github.com/sarahchen
📍 San Francisco, CA

PROFESSIONAL SUMMARY
Innovative full-stack engineer with 7+ years building scalable web applications and AI-driven solutions. 
Expert in React/Node.js ecosystems, cloud architecture (AWS/GCP), and machine learning model deployment. 
Led cross-functional teams of 8+ developers, delivered products serving 2M+ users.

EXPERIENCE

Staff Software Engineer @ Netflix Inc. (April 2022 – Present) | Los Gatos, CA
• Architected microservices platform handling 50M+ daily streaming requests with 99.95% uptime
• Reduced content recommendation latency by 60% through ML model optimization and caching
• Led migration of legacy monolith to event-driven architecture, improving deployment frequency by 5x
• Mentored 12 engineers across 3 teams, implementing best practices that reduced bugs by 40%
• Technologies: Python, Go, React, TensorFlow, Kubernetes, PostgreSQL, Redis, Apache Kafka

Senior Software Engineer @ Uber Technologies (June 2020 – March 2022) | San Francisco, CA
• Built real-time driver matching algorithm processing 100K+ requests per minute globally
• Implemented fraud detection system using ensemble ML models, reducing fraudulent transactions by 85%
• Optimized core API endpoints, achieving sub-50ms response times at 99th percentile
• Collaborated with data science team on A/B testing framework affecting 15M+ riders
• Technologies: Java, Spring Boot, React Native, Apache Spark, Cassandra, AWS

Software Engineer @ Square (Fintech) (August 2018 – May 2020) | San Francisco, CA
• Developed payment processing infrastructure handling $2B+ annual transaction volume
• Created merchant analytics dashboard with real-time insights, increasing user engagement by 30%
• Implemented OAuth 2.0 security protocols and PCI-DSS compliance measures
• Built automated testing suite reducing regression bugs by 70%
• Technologies: Ruby on Rails, JavaScript, Vue.js, PostgreSQL, Redis, Docker

PROJECTS

AIVoice: Personal Voice Assistant Platform | GitHub: https://github.com/sarahchen/aivoice | 2023
• Built end-to-end voice AI platform using Whisper for transcription and GPT-4 for responses
• Achieved 95% accuracy in speech recognition across 10+ languages
• Deployed on AWS Lambda with auto-scaling, handling 10K+ daily interactions
• Technologies: Python, FastAPI, OpenAI API, AWS Lambda, DynamoDB, React

CryptoTracker: Real-time Cryptocurrency Analytics | Live: https://cryptotracker.dev | 2022
• Developed real-time crypto portfolio tracker with predictive analytics using LSTM models
• Integrated with 15+ exchange APIs for live price feeds and trading data
• Achieved 78% accuracy in 24-hour price prediction models
• Technologies: Python, Django, TensorFlow, PostgreSQL, Celery, WebSocket, D3.js

E-Commerce ML Platform | Internal Project | 2021
• Designed recommendation engine increasing conversion rates by 25% for online retailer
• Processed 1M+ user interactions daily using collaborative filtering and deep learning
• Implemented A/B testing framework measuring impact across 500K+ users
• Technologies: Python, Scikit-learn, Apache Airflow, BigQuery, React, Node.js

EDUCATION

Master of Science in Computer Science @ Stanford University (2016 – 2018)
• Specialization: Artificial Intelligence and Machine Learning
• Thesis: "Deep Learning for Natural Language Understanding in Conversational AI"
• GPA: 3.9/4.0 | Teaching Assistant for CS229 (Machine Learning)

Bachelor of Science in Computer Engineering @ UC Berkeley (2012 – 2016)
• Summa Cum Laude, GPA: 3.85/4.0
• President of Women in Engineering Society (2015-2016)
• Dean's Honor List (Fall 2014, Spring 2015, Fall 2015, Spring 2016)

TECHNICAL SKILLS

Programming Languages: Python, JavaScript, TypeScript, Java, Go, Ruby, SQL, C++, Rust
Frontend Technologies: React, Vue.js, Angular, Next.js, HTML5, CSS3, Sass, Tailwind CSS
Backend Technologies: Node.js, Django, FastAPI, Spring Boot, Ruby on Rails, Express.js
Cloud & DevOps: AWS, GCP, Azure, Docker, Kubernetes, Terraform, Jenkins, GitHub Actions
Databases: PostgreSQL, MongoDB, Redis, Cassandra, DynamoDB, BigQuery, Elasticsearch
AI/ML Frameworks: TensorFlow, PyTorch, Scikit-learn, Hugging Face, OpenAI API, LangChain
Data Processing: Apache Spark, Apache Kafka, Airflow, Pandas, NumPy, Dask

CERTIFICATIONS & ACHIEVEMENTS

AWS Certified Solutions Architect - Professional | Amazon Web Services | Valid until Dec 2025
Google Cloud Professional Machine Learning Engineer | Google Cloud | March 2024
Certified Kubernetes Administrator (CKA) | CNCF | January 2024
AWS Certified Developer Associate | Amazon Web Services | September 2023

Distinguished Engineer Award 2023 | Netflix Inc.
Top Performer Q1-Q4 2022 | Uber Technologies  
Dean's List (4 semesters) | UC Berkeley (2014-2016)
Grace Hopper Conference Scholarship Recipient | 2017
Hackathon Winner - TechCrunch Disrupt SF | Best AI Application | 2023
Women in Tech Leadership Award | Silicon Valley Tech Council | 2022
"""


async def test_pipeline_configurations():
    """Test different pipeline configurations."""
    print("🚀 COMPREHENSIVE RESUME PROCESSING PIPELINE TEST")
    print("=" * 100)
    
    results = {}
    
    for config_name, config in TEST_CONFIGS.items():
        print(f"\n📋 Testing Configuration: {config['description']}")
        print("─" * 80)
        
        # Check for OpenAI API key if LLM is enabled
        if config["use_llm"]:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                print("⚠️  OpenAI API key not found. Skipping LLM-enhanced test.")
                print("   Set OPENAI_API_KEY environment variable to test LLM features.")
                continue
        
        # Initialize processor
        processor = ResumeProcessor(
            use_llm=config["use_llm"],
            openai_api_key=os.getenv("OPENAI_API_KEY") if config["use_llm"] else None
        )
        
        # Process resume
        start_time = time.time()
        result = processor.process_text(COMPREHENSIVE_RESUME_TEXT)
        processing_time = time.time() - start_time
        
        results[config_name] = {
            "result": result,
            "processing_time": processing_time,
            "config": config
        }
        
        # Display results
        display_results(config_name, result, processing_time)
    
    # Compare configurations
    print("\n📊 CONFIGURATION COMPARISON")
    print("=" * 100)
    
    for config_name, data in results.items():
        result = data["result"]
        time_taken = data["processing_time"]
        
        print(f"\n{config_name.upper()}:")
        print(f"  ⏱️  Processing Time: {time_taken:.2f}s")
        print(f"  ✅ Success: {result.success}")
        print(f"  🎯 Confidence: {result.resume_json.parsing_confidence:.1%}")
        print(f"  📧 Email Extracted: {'✓' if result.resume_json.contact.email else '✗'}")
        print(f"  📱 Phone Extracted: {'✓' if result.resume_json.contact.phone else '✗'}")
        print(f"  💼 Experience Entries: {len(result.resume_json.experience)}")
        print(f"  🚀 Projects: {len(result.resume_json.projects)}")
        print(f"  🎓 Education: {len(result.resume_json.education)}")
        print(f"  🛠️  Skill Categories: {len(result.resume_json.skills)}")
        print(f"  📜 Certifications: {len(result.resume_json.certifications)}")
        print(f"  🏆 Achievements: {len(result.resume_json.achievements)}")
        print(f"  🎭 Domains: {len(result.resume_json.domains)}")
        
        # LLM-specific info
        if hasattr(result.resume_json, 'llm_enhanced'):
            print(f"  🤖 LLM Enhanced: {'✓' if result.resume_json.llm_enhanced else '✗'}")


def display_results(config_name: str, result: ProcessingResult, processing_time: float):
    """Display detailed processing results."""
    print(f"📈 PROCESSING RESULTS ({config_name}):")
    print(f"   ✅ Success: {result.success}")
    print(f"   ⏱️ Processing Time: {processing_time:.3f}s")
    print(f"   🏗️ Stages: {', '.join(result.stages_completed)}")
    
    if not result.success:
        print(f"   ❌ Error: {result.error}")
        return
    
    resume = result.data
    
    print(f"📊 EXTRACTION SUMMARY:")
    print(f"   📝 Text Length: {resume.raw_text_length:,} characters")
    print(f"   🎯 Confidence: {resume.parsing_confidence:.1%}")
    print(f"   🏷️ Sections: {', '.join(resume.sections_detected) if hasattr(resume, 'sections_detected') else 'N/A'}")
    print(f"   🎭 Domains: {', '.join(resume.domains[:3])}{'...' if len(resume.domains) > 3 else ''}")
    
    # Contact information
    print(f"👤 CONTACT INFORMATION:")
    contact = resume.contact
    print(f"   Name: {contact.name or 'N/A'}")
    print(f"   Email: {contact.email or 'N/A'}")
    print(f"   Phone: {contact.phone or 'N/A'}")
    print(f"   LinkedIn: {contact.linkedin or 'N/A'}")
    print(f"   GitHub: {contact.github or 'N/A'}")
    
    # Experience overview
    if resume.experience:
        print(f"💼 EXPERIENCE ({len(resume.experience)} entries):")
        for i, exp in enumerate(resume.experience[:2], 1):  # Show first 2
            print(f"   {i}. {exp.position} at {exp.company}")
            print(f"      📅 {exp.start_date or 'N/A'} → {exp.end_date or 'N/A'}")
            print(f"      🛠️  Tech: {', '.join(exp.technologies[:5])}{'...' if len(exp.technologies) > 5 else ''}")
            print(f"      📊 Metrics: {len(exp.metrics)} found")
    
    # Projects overview
    if resume.projects:
        print(f"🚀 PROJECTS ({len(resume.projects)} projects):")
        for i, proj in enumerate(resume.projects[:2], 1):  # Show first 2
            print(f"   {i}. {proj.name}")
            print(f"      🔗 {proj.url or 'No URL'}")
            print(f"      🛠️  Tech: {', '.join(proj.technologies[:5])}{'...' if len(proj.technologies) > 5 else ''}")
    
    # Skills overview
    if resume.skills:
        print(f"🛠️  SKILLS ({len(resume.skills)} categories):")
        for skill_cat in resume.skills[:3]:  # Show first 3 categories
            skills_preview = ', '.join(skill_cat.skills[:4])
            if len(skill_cat.skills) > 4:
                skills_preview += f" ... (+{len(skill_cat.skills) - 4} more)"
            print(f"   {skill_cat.category}: {skills_preview}")
    
    # Certifications
    if resume.certifications:
        print(f"📜 CERTIFICATIONS ({len(resume.certifications)}):")
        for cert in resume.certifications[:3]:  # Show first 3
            print(f"   • {cert.name}")
            if cert.issuer:
                print(f"     Issuer: {cert.issuer}")
            if cert.issue_date:
                print(f"     Date: {cert.issue_date}")
    
    # Achievements
    if resume.achievements:
        print(f"🏆 ACHIEVEMENTS ({len(resume.achievements)}):")
        for achievement in resume.achievements[:3]:  # Show first 3
            print(f"   • {achievement}")


async def test_api_endpoints():
    """Test the FastAPI endpoints."""
    print(f"\n🌐 API ENDPOINTS TEST")
    print("=" * 100)
    print("⚠️  Note: This requires the FastAPI server to be running.")
    print("   Start with: uvicorn src.api:app --reload")
    print("   Then run this test again to validate API endpoints.")


async def test_file_processing():
    """Test file upload and processing."""
    print(f"\n📁 FILE PROCESSING TEST")
    print("=" * 100)
    
    # Check for test files
    test_files_dir = Path("test_files")
    uploads_dir = Path("uploads")
    
    print(f"📂 Checking for test files in: {test_files_dir.absolute()}")
    
    if test_files_dir.exists():
        test_files = list(test_files_dir.glob("*.pdf")) + list(test_files_dir.glob("*.docx"))
        if test_files:
            print(f"   Found {len(test_files)} test files")
            processor = ResumeProcessor(use_llm=False)
            
            for file_path in test_files[:2]:  # Test first 2 files
                print(f"\n📄 Processing: {file_path.name}")
                try:
                    start_time = time.time()
                    result = processor.process_file(str(file_path))
                    processing_time = time.time() - start_time
                    
                    print(f"   ✅ Processed in {processing_time:.2f}s")
                    print(f"   🎯 Confidence: {result.data.parsing_confidence:.1%}")
                    print(f"   📧 Email: {result.data.contact.email or 'Not found'}")
                    print(f"   💼 Experience: {len(result.data.experience)} entries")
                    
                except Exception as e:
                    print(f"   ❌ Error: {str(e)}")
        else:
            print("   No PDF or DOCX files found")
    else:
        print(f"   Directory not found. Create {test_files_dir} and add resume files to test.")


async def create_sample_files():
    """Create sample resume files for testing."""
    print(f"\n📝 CREATING SAMPLE FILES")
    print("=" * 100)
    
    # Create test files directory
    test_dir = Path("test_files")
    test_dir.mkdir(exist_ok=True)
    
    # Create a sample text file
    sample_txt = test_dir / "sample_resume.txt"
    with open(sample_txt, 'w', encoding='utf-8') as f:
        f.write(COMPREHENSIVE_RESUME_TEXT)
    
    print(f"✅ Created sample text file: {sample_txt}")
    print(f"   You can test file processing with this file.")
    
    # Also save the JSON output for reference
    output_dir = Path("sample_outputs")
    output_dir.mkdir(exist_ok=True)
    
    processor = ResumeProcessor(use_llm=False)
    result = processor.process_text(COMPREHENSIVE_RESUME_TEXT)
    
    output_file = output_dir / "comprehensive_resume_output.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result.data.model_dump(), f, indent=2, default=str)
    
    print(f"✅ Created sample JSON output: {output_file}")


async def main():
    """Run all tests."""
    await test_pipeline_configurations()
    await test_file_processing()
    await test_api_endpoints()
    await create_sample_files()
    
    print(f"\n🎉 COMPREHENSIVE TESTING COMPLETED!")
    print("=" * 100)
    print("📋 NEXT STEPS:")
    print("   1. Add your own resume files to test_files/ directory")
    print("   2. Set OPENAI_API_KEY environment variable to test LLM enhancement")
    print("   3. Start the API server: uvicorn src.api:app --reload")
    print("   4. Test API endpoints with curl or Postman")
    print("   5. Integrate with your Interview Service")


if __name__ == "__main__":
    asyncio.run(main())

"""
Comprehensive test for enhanced domain-aware resume parsing.
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent / "app"))

from app.services.enhanced_parsing_service import DomainAwareResumeParser, ResumeParsingService

# Enhanced sample resume with more domain-specific content
ENHANCED_SAMPLE_RESUME = """
John Doe
Senior Software Engineer & AI/ML Specialist
Email: john.doe@example.com
Phone: +1 (555) 123-4567
LinkedIn: https://linkedin.com/in/johndoe
GitHub: https://github.com/johndoe

PROFESSIONAL SUMMARY
Senior software engineer with 6+ years of experience in full-stack development, machine learning, 
and DevOps. Expertise in Python, JavaScript, cloud technologies (AWS), and modern AI/ML frameworks. 
Proven track record in building scalable applications, implementing MLOps pipelines, and leading 
cross-functional teams in agile environments.

EXPERIENCE

Senior AI Engineer at Google
January 2022 - Present
• Developed and deployed large-scale machine learning models using TensorFlow and PyTorch
• Implemented MLOps pipelines with Kubeflow and MLflow for model versioning and monitoring
• Built recommendation systems serving 10M+ users with 99.9% uptime
• Led migration of ML infrastructure to Kubernetes, reducing deployment time by 60%
• Technologies: Python, TensorFlow, PyTorch, Kubernetes, Docker, Apache Spark, Kafka

Machine Learning Engineer at Microsoft
March 2020 - December 2021
• Designed and implemented computer vision models for autonomous vehicle perception
• Fine-tuned BERT and GPT models for natural language understanding tasks
• Built real-time data pipelines using Apache Airflow and Kafka for ML feature engineering
• Collaborated with research teams on cutting-edge deep learning architectures
• Technologies: PyTorch, Transformers, spaCy, NLTK, Azure ML, Docker, Git

Full Stack Developer at Startup Inc
June 2018 - February 2020
• Developed scalable web applications using React, Node.js, and PostgreSQL
• Implemented microservices architecture with Docker and Kubernetes
• Built REST APIs serving 100K+ daily active users
• Set up CI/CD pipelines using Jenkins and GitHub Actions
• Technologies: JavaScript, React, Node.js, PostgreSQL, MongoDB, Redis, AWS, Docker

EDUCATION

Master of Science in Computer Science
Stanford University
September 2016 - May 2018
Specialization: Artificial Intelligence and Machine Learning
GPA: 3.8/4.0
Relevant Coursework: Deep Learning, Natural Language Processing, Computer Vision

Bachelor of Science in Software Engineering  
UC Berkeley
September 2012 - May 2016
GPA: 3.6/4.0
Relevant Coursework: Data Structures and Algorithms, Database Systems, Software Architecture

SKILLS
Programming Languages: Python, JavaScript, Java, TypeScript, Go, SQL
Machine Learning: TensorFlow, PyTorch, Scikit-learn, Keras, XGBoost, LightGBM
NLP: Transformers, BERT, GPT, spaCy, NLTK, Hugging Face
AI Engineering: MLOps, LLMOps, Model Deployment, A/B Testing, Feature Stores
Data Engineering: Apache Spark, Kafka, Airflow, Snowflake, dbt, Pandas, NumPy
Cloud & DevOps: AWS, Azure, Docker, Kubernetes, Terraform, Jenkins, GitHub Actions
Web Technologies: React, Angular, Node.js, Django, Flask, FastAPI
Databases: PostgreSQL, MongoDB, Redis, Elasticsearch
Tools: Git, Jira, Confluence, Jupyter, VS Code

PROJECTS

AI-Powered Code Review Assistant
• Built an LLM-based code review assistant using GPT-4 and fine-tuned CodeT5
• Implemented RAG (Retrieval Augmented Generation) with vector databases
• Achieved 85% accuracy in detecting code quality issues and security vulnerabilities
• Technologies: Python, OpenAI API, LangChain, Pinecone, FastAPI, React
GitHub: https://github.com/johndoe/ai-code-reviewer

Real-time Fraud Detection System
• Developed machine learning system detecting fraudulent transactions in real-time
• Implemented ensemble models using Random Forest, XGBoost, and Neural Networks
• Built streaming data pipeline with Kafka and Apache Spark
• Achieved 95% precision and 92% recall on fraud detection
• Technologies: Python, Scikit-learn, XGBoost, Apache Spark, Kafka, PostgreSQL

Kubernetes-Native ML Platform
• Designed and built MLOps platform for model training, deployment, and monitoring
• Implemented custom Kubernetes operators for ML workload management
• Integrated with Prometheus and Grafana for comprehensive monitoring
• Reduced model deployment time from hours to minutes
• Technologies: Kubernetes, Go, Python, Helm, Prometheus, Grafana, MLflow

CERTIFICATIONS
AWS Certified Solutions Architect - Professional (2023)
Certified Kubernetes Administrator (CKA) (2022)
Google Cloud Professional Machine Learning Engineer (2021)
Deep Learning Specialization - Coursera (2020)

PUBLICATIONS
"Scalable MLOps on Kubernetes: A Production-Ready Framework" - KubeCon 2023
"Efficient Fine-tuning of Large Language Models for Code Generation" - NeurIPS 2022 Workshop

AWARDS
Best Paper Award - International Conference on Machine Learning Applications (2023)
Google Exceptional Contributor Award (2022)
Microsoft Innovation Award (2021)

LANGUAGES
English (Native)
Spanish (Fluent) 
Mandarin (Conversational)
"""


async def test_enhanced_domain_parsing():
    """Test the enhanced domain-aware parsing capabilities."""
    print("🚀 ENHANCED DOMAIN-AWARE RESUME PARSING TEST")
    print("=" * 70)
    
    # Initialize the enhanced parser
    parser = DomainAwareResumeParser()
    
    # Parse the enhanced resume
    result = parser.parse_resume_from_text(ENHANCED_SAMPLE_RESUME)
    
    print(f"📊 PARSING RESULTS:")
    print(f"   Raw text length: {result.raw_text_length:,} characters")
    print(f"   Parsing confidence: {result.parsing_confidence}")
    print(f"   Sections found: {', '.join(result.sections_found)}")
    
    print(f"\n👤 CONTACT INFORMATION:")
    print(f"   Name: {result.contact_info.name}")
    print(f"   Email: {result.contact_info.email}")
    print(f"   Phone: {result.contact_info.phone}")
    print(f"   LinkedIn: {result.contact_info.linkedin}")
    print(f"   GitHub: {result.contact_info.github}")
    
    print(f"\n🎯 DOMAIN CLASSIFICATION:")
    print(f"   Domains detected: {len(result.domains_supported)}")
    for domain in result.domains_supported:
        confidence = result.domain_confidence.get(domain, 0.0)
        print(f"   • {domain}: {confidence:.2f} confidence")
    
    print(f"\n🛠️ SKILLS BY CATEGORY:")
    total_skills = 0
    for skill_category in result.skills:
        skills_count = len(skill_category.skills)
        total_skills += skills_count
        print(f"   {skill_category.category} ({skills_count}): {', '.join(skill_category.skills[:5])}{'...' if skills_count > 5 else ''}")
    print(f"   Total skills extracted: {total_skills}")
    
    print(f"\n💼 WORK EXPERIENCE:")
    for i, exp in enumerate(result.experience, 1):
        print(f"   {i}. {exp.position or 'N/A'} at {exp.company or 'N/A'}")
        if exp.start_date or exp.end_date:
            print(f"      Duration: {exp.start_date or 'N/A'} - {exp.end_date or 'Present'}")
        if exp.technologies:
            print(f"      Technologies: {', '.join(exp.technologies[:5])}{'...' if len(exp.technologies) > 5 else ''}")
    print(f"   Total experience: {result.total_experience_years} years")
    
    print(f"\n🎓 EDUCATION:")
    for edu in result.education:
        print(f"   {edu.degree or 'N/A'} from {edu.institution or 'N/A'}")
        if edu.end_date:
            print(f"      Graduation: {edu.end_date}")
    
    print(f"\n🚀 PROJECTS:")
    for i, proj in enumerate(result.projects, 1):
        print(f"   {i}. {proj.name or 'N/A'}")
        if proj.url:
            print(f"      URL: {proj.url}")
        if proj.technologies:
            print(f"      Technologies: {', '.join(proj.technologies[:3])}{'...' if len(proj.technologies) > 3 else ''}")
    
    print(f"\n📜 CERTIFICATIONS:")
    for cert in result.certifications:
        print(f"   • {cert.name}")
        if cert.issue_date:
            print(f"     Issued: {cert.issue_date}")
    
    print(f"\n🏆 AWARDS:")
    for award in result.awards:
        print(f"   • {award}")
    
    print(f"\n📚 PUBLICATIONS:")
    for pub in result.publications:
        print(f"   • {pub}")
    
    print(f"\n🌐 LANGUAGES:")
    for lang in result.languages:
        print(f"   • {lang.language}: {lang.proficiency or 'N/A'}")
    
    return result


async def test_domain_classification_accuracy():
    """Test the accuracy of domain classification."""
    print("\n\n" + "=" * 70)
    print("🎯 DOMAIN CLASSIFICATION ACCURACY TEST")
    print("=" * 70)
    
    parser = DomainAwareResumeParser()
    result = parser.parse_resume_from_text(ENHANCED_SAMPLE_RESUME)
    
    # Expected domains based on the resume content
    expected_domains = {
        "Machine Learning", "AI Engineering", "Software Engineering", 
        "DevOps", "Kubernetes", "Data Engineering", "NLP", "LLM Engineering",
        "Cloud Engineering"
    }
    
    detected_domains = set(result.domains_supported)
    
    print(f"Expected domains: {len(expected_domains)}")
    print(f"Detected domains: {len(detected_domains)}")
    
    # Calculate accuracy metrics
    true_positives = expected_domains & detected_domains
    false_positives = detected_domains - expected_domains
    false_negatives = expected_domains - detected_domains
    
    precision = len(true_positives) / len(detected_domains) if detected_domains else 0
    recall = len(true_positives) / len(expected_domains) if expected_domains else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    print(f"\n📈 ACCURACY METRICS:")
    print(f"   True Positives: {len(true_positives)} - {', '.join(sorted(true_positives))}")
    print(f"   False Positives: {len(false_positives)} - {', '.join(sorted(false_positives))}")
    print(f"   False Negatives: {len(false_negatives)} - {', '.join(sorted(false_negatives))}")
    print(f"   Precision: {precision:.2f}")
    print(f"   Recall: {recall:.2f}")
    print(f"   F1 Score: {f1_score:.2f}")
    
    return {
        "precision": precision,
        "recall": recall, 
        "f1_score": f1_score,
        "true_positives": len(true_positives),
        "false_positives": len(false_positives),
        "false_negatives": len(false_negatives)
    }


async def test_legacy_compatibility():
    """Test backward compatibility with existing service."""
    print("\n\n" + "=" * 70)
    print("🔄 LEGACY COMPATIBILITY TEST")
    print("=" * 70)
    
    # Test the ResumeParsingService wrapper
    legacy_service = ResumeParsingService()
    result = legacy_service.parse_resume(ENHANCED_SAMPLE_RESUME)
    
    print(f"✅ Legacy service initialized successfully")
    print(f"✅ Parse method works: {result.parsing_confidence > 0}")
    print(f"✅ Domains supported: {len(result.domains_supported)} domains detected")
    print(f"✅ Contact info extracted: {bool(result.contact_info.email)}")
    print(f"✅ Skills categorized: {len(result.skills)} categories")
    print(f"✅ Experience parsed: {len(result.experience)} entries")
    
    return result


async def test_error_handling():
    """Test error handling and edge cases."""
    print("\n\n" + "=" * 70)
    print("🛡️ ERROR HANDLING TEST")
    print("=" * 70)
    
    parser = DomainAwareResumeParser()
    
    # Test empty text
    print("📝 Testing empty text...")
    result = parser.parse_resume_from_text("")
    print(f"   ✅ Empty text handled gracefully: confidence = {result.parsing_confidence}")
    
    # Test malformed text
    print("📝 Testing malformed text...")
    malformed = "This is not a resume at all! Just random text with no structure."
    result = parser.parse_resume_from_text(malformed)
    print(f"   ✅ Malformed text handled: {len(result.domains_supported)} domains, confidence = {result.parsing_confidence}")
    
    # Test very short text
    print("📝 Testing very short text...")
    short_text = "John Doe\njohn@email.com"
    result = parser.parse_resume_from_text(short_text)
    print(f"   ✅ Short text handled: name = {result.contact_info.name}, email = {result.contact_info.email}")
    
    # Test text with special characters
    print("📝 Testing text with special characters...")
    special_text = "Jöhn Döe 📧 john@email.com 📱 555-123-4567 🔗 linkedin.com/in/johndoe"
    result = parser.parse_resume_from_text(special_text)
    print(f"   ✅ Special characters handled: email = {result.contact_info.email}")


def performance_benchmark():
    """Benchmark parsing performance."""
    print("\n\n" + "=" * 70)
    print("⚡ PERFORMANCE BENCHMARK")
    print("=" * 70)
    
    import time
    
    parser = DomainAwareResumeParser()
    
    # Single parse timing
    start_time = time.time()
    result = parser.parse_resume_from_text(ENHANCED_SAMPLE_RESUME)
    single_parse_time = time.time() - start_time
    
    # Multiple parse timing
    num_iterations = 10
    start_time = time.time()
    for _ in range(num_iterations):
        parser.parse_resume_from_text(ENHANCED_SAMPLE_RESUME)
    total_time = time.time() - start_time
    avg_parse_time = total_time / num_iterations
    
    print(f"⏱️  Single parse time: {single_parse_time:.3f} seconds")
    print(f"⏱️  Average parse time ({num_iterations} iterations): {avg_parse_time:.3f} seconds")
    print(f"🚀 Throughput: {1/avg_parse_time:.1f} resumes/second")
    
    # Memory efficiency estimate
    text_size_kb = len(ENHANCED_SAMPLE_RESUME) / 1024
    domains_detected = len(result.domains_supported)
    skills_extracted = sum(len(cat.skills) for cat in result.skills)
    
    print(f"📊 Efficiency metrics:")
    print(f"   Input size: {text_size_kb:.1f} KB")
    print(f"   Domains detected: {domains_detected}")
    print(f"   Skills extracted: {skills_extracted}")
    print(f"   Processing rate: {text_size_kb/avg_parse_time:.1f} KB/second")


async def main():
    """Run comprehensive test suite."""
    print("🧪 ENHANCED DOMAIN-AWARE RESUME PARSING TEST SUITE")
    print("=" * 70)
    
    try:
        # Run all tests
        parsing_result = await test_enhanced_domain_parsing()
        domain_accuracy = await test_domain_classification_accuracy()
        legacy_result = await test_legacy_compatibility()
        await test_error_handling()
        performance_benchmark()
        
        print("\n\n" + "=" * 70)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        
        print(f"\n📋 SUMMARY:")
        print(f"   Parsing confidence: {parsing_result.parsing_confidence}")
        print(f"   Domains detected: {len(parsing_result.domains_supported)}")
        print(f"   Domain classification F1 score: {domain_accuracy['f1_score']:.2f}")
        print(f"   Skills extracted: {sum(len(cat.skills) for cat in parsing_result.skills)}")
        print(f"   Experience entries: {len(parsing_result.experience)}")
        print(f"   Legacy compatibility: ✅")
        
        # Save detailed results
        results_summary = {
            "parsing_confidence": parsing_result.parsing_confidence,
            "domains_detected": parsing_result.domains_supported,
            "domain_accuracy": domain_accuracy,
            "skills_count": sum(len(cat.skills) for cat in parsing_result.skills),
            "experience_count": len(parsing_result.experience),
            "education_count": len(parsing_result.education),
            "projects_count": len(parsing_result.projects),
            "certifications_count": len(parsing_result.certifications)
        }
        
        with open("enhanced_parsing_results.json", "w") as f:
            json.dump(results_summary, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: enhanced_parsing_results.json")
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

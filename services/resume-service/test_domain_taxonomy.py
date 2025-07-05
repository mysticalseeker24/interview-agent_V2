#!/usr/bin/env python3
"""
Test script to verify the domain taxonomy implementation works as described in the user request.
"""

import json
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent / "app"))

from app.services.enhanced_parsing_service import DomainAwareResumeParser


def test_domain_taxonomy():
    """Test the domain taxonomy implementation."""
    
    print("=== Testing Domain Taxonomy Implementation ===\n")
    
    # Initialize the parser
    parser = DomainAwareResumeParser()
    
    # Check if domain taxonomy is loaded
    print(f"1. Domain taxonomy loaded: {len(parser.domain_taxonomy)} domains")
    print(f"   Domains: {list(parser.domain_taxonomy.keys())}")
    print(f"   Master skills: {len(parser.master_skills)} skills")
    print(f"   Skill-to-domain mapping: {len(parser.skill_to_domains)} skills mapped\n")
    
    # Test skills parsing with domain classification
    print("2. Testing skills parsing with domain classification:")
    sample_skills = """
    Technical Skills:
    • Python, JavaScript, Java, Go
    • React, Node.js, Express
    • Docker, Kubernetes, Jenkins
    • TensorFlow, PyTorch, Scikit-learn
    • AWS, Terraform, Ansible
    • PostgreSQL, MongoDB, Redis
    • Git, GitHub Actions, CI/CD
    """
    
    skills, detected_domains = parser.parse_skills_with_domains(sample_skills)
    
    print(f"   Found {len(skills)} skill categories:")
    for skill_cat in skills:
        print(f"     - {skill_cat.category}: {skill_cat.skills}")
    
    print(f"   Detected domains from skills: {sorted(detected_domains)}\n")
    
    # Test experience-based domain detection
    print("3. Testing experience-based domain detection:")
    
    from app.schemas.resume import ExperienceEntry
    
    sample_experience = [
        ExperienceEntry(
            company="Tech Corp",
            position="Senior DevOps Engineer",
            description="""
            Designed and implemented CI/CD pipelines using Jenkins and GitHub Actions.
            Managed Kubernetes clusters on AWS with Terraform for infrastructure as code.
            Implemented monitoring solutions using Prometheus and Grafana.
            Automated deployment processes and reduced deployment time by 70%.
            """
        ),
        ExperienceEntry(
            company="AI Startup",
            position="Machine Learning Engineer",
            description="""
            Developed machine learning models using TensorFlow and PyTorch.
            Implemented feature engineering pipelines and model evaluation frameworks.
            Fine-tuned large language models for natural language processing tasks.
            Built MLOps infrastructure for model deployment and monitoring.
            """
        )
    ]
    
    sample_text = """
    John Doe - Senior Software Engineer
    
    Professional Summary:
    Experienced software engineer with expertise in cloud infrastructure, 
    machine learning, and DevOps practices. Skilled in containerization, 
    orchestration, and automated deployment pipelines.
    
    Technical Skills:
    Programming: Python, JavaScript, Go, Java
    Cloud: AWS, Azure, Google Cloud
    DevOps: Docker, Kubernetes, Jenkins, Terraform
    ML/AI: TensorFlow, PyTorch, Scikit-learn, BERT
    Databases: PostgreSQL, MongoDB, Redis
    
    Experience:
    Senior DevOps Engineer - Tech Corp
    • Designed CI/CD pipelines using Jenkins and GitHub Actions
    • Managed Kubernetes clusters with Terraform
    • Implemented monitoring with Prometheus and Grafana
    
    Machine Learning Engineer - AI Startup  
    • Developed ML models using TensorFlow and PyTorch
    • Fine-tuned large language models for NLP tasks
    • Built MLOps infrastructure for model deployment
    """
    
    # Test the new detect_domains method
    domains = parser.detect_domains(sample_text, sample_experience)
    print(f"   Domains detected from content: {domains}")
    
    # Test domain confidence scoring
    domain_confidence = parser.detect_domains_from_content(sample_text, sample_experience)
    print(f"   Domain confidence scores:")
    for domain, confidence in sorted(domain_confidence.items(), key=lambda x: x[1], reverse=True):
        print(f"     - {domain}: {confidence}")
    
    print("\n4. Testing full resume parsing:")
    
    # Test full resume parsing
    result = parser.parse_resume_from_text(sample_text)
    
    print(f"   Parsing confidence: {result.parsing_confidence}")
    print(f"   Domains supported: {result.domains_supported}")
    print(f"   Domain confidence: {result.domain_confidence}")
    print(f"   Skills categories found: {len(result.skills)}")
    for skill_cat in result.skills:
        print(f"     - {skill_cat.category}: {len(skill_cat.skills)} skills")
    
    print("\n=== Test Complete ===")
    return True


if __name__ == "__main__":
    test_domain_taxonomy()

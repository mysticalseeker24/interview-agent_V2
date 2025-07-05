#!/usr/bin/env python3
"""
Show the extracted resume text and test the service properly.
"""

import sys
from pathlib import Path

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent / "app"))

from app.services.enhanced_parsing_service import DomainAwareResumeParser


def show_resume_analysis():
    """Show detailed analysis of the actual resume."""
    
    print("=" * 80)
    print(" DETAILED RESUME ANALYSIS ")
    print("=" * 80)
    
    # Initialize parser
    parser = DomainAwareResumeParser()
    resume_file = Path("resume-data/Resume (1).pdf")
    
    if not resume_file.exists():
        print(f"❌ Resume file not found: {resume_file}")
        return
    
    # Extract and show raw text
    print("\n--- RAW EXTRACTED TEXT ---")
    text = parser.extract_text_with_fallback(str(resume_file))
    print(f"Text length: {len(text)} characters")
    print("First 500 characters:")
    print("-" * 40)
    print(text[:500])
    print("-" * 40)
    
    # Show sections detected
    print("\n--- SECTION DETECTION ---")
    sections = parser.split_sections(text)
    print(f"Sections found: {list(sections.keys())}")
    
    for section_name, content in sections.items():
        print(f"\n📁 {section_name.upper()}:")
        print(f"   Length: {len(content)} characters")
        preview = content[:200].replace('\n', ' ').strip()
        print(f"   Preview: {preview}{'...' if len(content) > 200 else ''}")
    
    # Parse with full results
    print("\n--- FULL PARSING RESULTS ---")
    result = parser.parse_resume(str(resume_file), "pdf")
    
    print(f"✅ Successfully parsed resume")
    print(f"📊 Overall confidence: {result.parsing_confidence}")
    print(f"📝 Text length: {result.raw_text_length}")
    
    # Contact info
    print(f"\n👤 CONTACT INFORMATION:")
    print(f"   Name: {result.contact_info.name}")
    print(f"   Email: {result.contact_info.email}")
    print(f"   Phone: {result.contact_info.phone}")
    print(f"   LinkedIn: {result.contact_info.linkedin}")
    print(f"   GitHub: {result.contact_info.github}")
    
    # Domain analysis - the key feature
    print(f"\n🎯 DOMAIN ANALYSIS (KEY FEATURE):")
    print(f"   Total domains detected: {len(result.domains_supported)}")
    print(f"   Domains: {result.domains_supported}")
    
    print(f"\n📊 DOMAIN CONFIDENCE SCORES:")
    sorted_domains = sorted(result.domain_confidence.items(), key=lambda x: x[1], reverse=True)
    for domain, confidence in sorted_domains:
        print(f"   {domain:<20}: {confidence:.3f}")
    
    # Skills by domain
    print(f"\n🛠️ SKILLS BY DOMAIN:")
    print(f"   Total skill categories: {len(result.skills)}")
    for skill_cat in result.skills:
        print(f"   📂 {skill_cat.category}: {skill_cat.skills}")
    
    # Show what domains were detected and why
    print(f"\n🔍 DOMAIN DETECTION BREAKDOWN:")
    
    # Test individual detection methods
    experience = parser.parse_experience(sections.get("experience", ""))
    
    # Method 1: Keyword-based detection
    domains_from_keywords = parser.detect_domains(text, experience)
    print(f"   Keyword-based detection: {domains_from_keywords}")
    
    # Method 2: Confidence scoring
    domain_confidence = parser.detect_domains_from_content(text, experience)
    print(f"   Confidence-based detection:")
    for domain, conf in sorted(domain_confidence.items(), key=lambda x: x[1], reverse=True):
        print(f"     • {domain}: {conf:.3f}")
    
    # Method 3: Skills-based
    if "skills" in sections:
        skills, skill_domains = parser.parse_skills_with_domains(sections["skills"])
        print(f"   Skills-based detection: {sorted(skill_domains)}")
    
    # Show specific matches for top domains
    print(f"\n🎯 WHY THESE DOMAINS WERE DETECTED:")
    
    text_lower = text.lower()
    for domain in ['AI Engineering', 'LLM Engineering', 'Machine Learning', 'DevOps', 'Software Engineering']:
        if domain in result.domain_confidence:
            print(f"\n   {domain}:")
            domain_info = parser.domain_taxonomy[domain]
            
            # Check for skill matches
            skill_matches = []
            for skill in domain_info["skills"]:
                if skill.lower() in text_lower:
                    skill_matches.append(skill)
            
            # Check for keyword matches  
            keyword_matches = []
            for keyword in domain_info["keywords"]:
                if keyword.lower() in text_lower:
                    keyword_matches.append(keyword)
            
            if skill_matches:
                print(f"     Skills found: {skill_matches[:5]}{'...' if len(skill_matches) > 5 else ''}")
            if keyword_matches:
                print(f"     Keywords found: {keyword_matches[:5]}{'...' if len(keyword_matches) > 5 else ''}")
    
    print(f"\n🎉 ANALYSIS COMPLETE!")
    print(f"📄 Your resume shows expertise in {len(result.domains_supported)} specialized domains!")


if __name__ == "__main__":
    show_resume_analysis()

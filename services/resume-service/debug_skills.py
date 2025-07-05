"""
Debug script for skills extraction
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "app"))

from app.services.advanced_resume_parser import AdvancedResumeParser

# Test text with clear skills
test_text = """
SKILLS
Programming Languages: Python, JavaScript, Java, TypeScript, Go
Web Technologies: React, Angular, Node.js, Django, Flask, HTML, CSS
Databases: PostgreSQL, MySQL, MongoDB, Redis
Cloud & DevOps: AWS, Docker, Kubernetes, Jenkins, Terraform
AI/ML: TensorFlow, PyTorch, Scikit-learn, Pandas, NumPy
"""

parser = AdvancedResumeParser()

# Test section detection
sections = parser.detect_sections(test_text)
print("Sections detected:", list(sections.keys()))
print("Skills section content:", sections.get('skills', 'NOT FOUND'))

# Test skills extraction
skills = parser.extract_skills(test_text, sections)
print(f"\nSkills extraction results: {len(skills)} categories found")
for skill_cat in skills:
    print(f"  {skill_cat.category}: {skill_cat.skills}")

# Test individual skill matching
print("\nTesting individual skill matching:")
for category, skill_list in parser.skills_db.items():
    found_skills = []
    for skill in skill_list[:5]:  # Test first 5 skills in each category
        if skill.lower() in test_text.lower():
            found_skills.append(skill)
    if found_skills:
        print(f"  {category}: {found_skills}")

# Test NER
import spacy
if parser.nlp:
    doc = parser.nlp(test_text)
    print(f"\nNER entities found: {len(doc.ents)}")
    for ent in doc.ents:
        print(f"  {ent.text} -> {ent.label_}")

"""
Advanced Resume Parsing Service with Enhanced NER and Section Detection.

This module provides comprehensive resume parsing capabilities using:
- spaCy for NER and linguistic analysis
- NLTK for text processing
- Custom regex patterns for structured data extraction
- Section-based parsing for better context understanding
- Phone number and email validation
- Date parsing for experience and education timelines

Inspired by pyresparser, DataTurks NER approaches, and modern NLP practices.
"""

import logging
import re
import os
import json
import spacy
import nltk
from typing import Dict, List, Optional, Any, Tuple, Set
from pathlib import Path
import dateparser
import phonenumbers
from email_validator import validate_email, EmailNotValidError
from fuzzywuzzy import fuzz, process
import PyPDF2
import pdfplumber
from docx import Document

from app.schemas.resume import (
    ResumeParseResult, ContactInfo, EducationEntry, ExperienceEntry, 
    ProjectEntry, SkillCategory, CertificationEntry, LanguageEntry
)

logger = logging.getLogger(__name__)


class AdvancedResumeParser:
    """Advanced resume parser with comprehensive entity extraction."""
    
    def __init__(self):
        """Initialize the advanced resume parser."""
        self.nlp = None
        self.skills_db = {}
        self.universities_db = set()
        self.companies_db = set()
        self._setup_nlp()
        self._download_nltk_data()
        self._load_knowledge_bases()
    
    def _setup_nlp(self):
        """Setup spaCy NLP pipeline with custom components."""
        try:
            logger.info("Loading spaCy model...")
            self.nlp = spacy.load("en_core_web_sm")
            
            # Add custom entity ruler for resume-specific entities
            if "entity_ruler" not in self.nlp.pipe_names:
                ruler = self.nlp.add_pipe("entity_ruler", before="ner")
            else:
                ruler = self.nlp.get_pipe("entity_ruler")
            
            # Load custom patterns
            skill_patterns = self._load_skill_patterns()
            company_patterns = self._load_company_patterns()
            education_patterns = self._load_education_patterns()
            
            ruler.add_patterns(skill_patterns + company_patterns + education_patterns)
            
            logger.info("spaCy model loaded successfully with custom patterns")
            
        except Exception as e:
            logger.error(f"Error loading spaCy model: {str(e)}")
            self.nlp = None
    
    def _download_nltk_data(self):
        """Download required NLTK data."""
        try:
            nltk_data = ['punkt', 'stopwords', 'words', 'averaged_perceptron_tagger']
            for data in nltk_data:
                try:
                    nltk.data.find(f'tokenizers/{data}')
                except LookupError:
                    logger.info(f"Downloading NLTK data: {data}")
                    nltk.download(data, quiet=True)
        except Exception as e:
            logger.warning(f"Error downloading NLTK data: {str(e)}")
    
    def _load_knowledge_bases(self):
        """Load knowledge bases for skills, universities, and companies."""
        # Enhanced skill categories with more comprehensive lists
        self.skills_db = {
            "Programming Languages": [
                "Python", "JavaScript", "Java", "C++", "C#", "Go", "Rust", "TypeScript",
                "PHP", "Ruby", "Swift", "Kotlin", "Scala", "R", "MATLAB", "SQL", "NoSQL",
                "Perl", "Shell", "Bash", "PowerShell", "Objective-C", "Dart", "F#",
                "Haskell", "Clojure", "Elixir", "Lua", "VBA", "Assembly"
            ],
            "Web Technologies": [
                "React", "Angular", "Vue.js", "Node.js", "Express", "Django", "Flask",
                "Spring", "Laravel", "Ruby on Rails", "ASP.NET", "jQuery", "HTML", "CSS",
                "SCSS", "SASS", "Bootstrap", "Tailwind CSS", "Next.js", "Nuxt.js",
                "Svelte", "FastAPI", "Ember.js", "Backbone.js", "Webpack", "Vite",
                "GraphQL", "REST API", "SOAP", "WebSocket", "Progressive Web Apps", "PWA"
            ],
            "Databases": [
                "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", "Oracle",
                "SQL Server", "Cassandra", "DynamoDB", "Neo4j", "Elasticsearch",
                "InfluxDB", "CouchDB", "MariaDB", "Amazon RDS", "Azure SQL",
                "Google Cloud SQL", "Firebase", "Supabase", "PlanetScale"
            ],
            "Cloud & DevOps": [
                "AWS", "Azure", "Google Cloud", "Docker", "Kubernetes", "Jenkins",
                "GitLab CI", "GitHub Actions", "Terraform", "Ansible", "Prometheus",
                "Grafana", "Nagios", "Chef", "Puppet", "Vagrant", "CircleCI",
                "Travis CI", "Heroku", "Vercel", "Netlify", "DigitalOcean"
            ],
            "AI/ML & Data Science": [
                "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy", "OpenCV",
                "Transformers", "LangChain", "Pinecone", "Hugging Face", "MLflow",
                "Jupyter", "Apache Spark", "Hadoop", "Kafka", "Airflow", "Databricks",
                "Snowflake", "Power BI", "Tableau", "D3.js", "Matplotlib", "Seaborn",
                "NLTK", "spaCy", "OpenAI", "LLM", "GPT", "BERT", "Computer Vision"
            ],
            "Mobile Development": [
                "React Native", "Flutter", "Swift", "Kotlin", "Xamarin", "Ionic",
                "Cordova", "Unity", "Android Studio", "Xcode", "Firebase", "Push Notifications"
            ],
            "Design & UX": [
                "Figma", "Adobe XD", "Sketch", "Photoshop", "Illustrator", "InDesign",
                "UI/UX", "Wireframing", "Prototyping", "User Research", "Design Systems"
            ],
            "Project Management": [
                "Agile", "Scrum", "Kanban", "Jira", "Confluence", "Trello", "Asana",
                "Monday.com", "Slack", "Microsoft Teams", "Notion", "PMP", "PRINCE2"
            ],
            "Testing": [
                "Jest", "Pytest", "JUnit", "Selenium", "Cypress", "TestNG", "Mocha",
                "Chai", "Postman", "Newman", "K6", "Unit Testing", "Integration Testing",
                "E2E Testing", "TDD", "BDD", "Automation Testing"
            ]
        }
        
        # Common universities (expandable)
        self.universities_db = {
            "MIT", "Stanford", "Harvard", "UC Berkeley", "Carnegie Mellon", "Caltech",
            "University of Washington", "Georgia Tech", "UT Austin", "UIUC", "Princeton",
            "Yale", "Columbia", "Cornell", "University of Michigan", "UCLA", "USC",
            "NYU", "Boston University", "Northeastern", "IIT", "NIT", "BITS"
        }
        
        # Common tech companies (expandable)
        self.companies_db = {
            "Google", "Microsoft", "Amazon", "Apple", "Meta", "Netflix", "Tesla",
            "Adobe", "Salesforce", "Oracle", "IBM", "Intel", "NVIDIA", "Uber",
            "Airbnb", "Spotify", "Twitter", "LinkedIn", "Dropbox", "Slack",
            "Atlassian", "GitHub", "GitLab", "Zoom", "Shopify", "Stripe"
        }
    
    def _load_skill_patterns(self) -> List[Dict[str, Any]]:
        """Load skill patterns for entity recognition."""
        patterns = []
        
        for category, skills in self.skills_db.items():
            for skill in skills:
                patterns.append({"label": "SKILL", "pattern": skill})
                # Add variations
                patterns.append({"label": "SKILL", "pattern": skill.lower()})
                patterns.append({"label": "SKILL", "pattern": skill.upper()})
        
        return patterns
    
    def _load_company_patterns(self) -> List[Dict[str, Any]]:
        """Load company patterns for entity recognition."""
        patterns = []
        
        for company in self.companies_db:
            patterns.append({"label": "ORG", "pattern": company})
        
        return patterns
    
    def _load_education_patterns(self) -> List[Dict[str, Any]]:
        """Load education patterns for entity recognition."""
        patterns = []
        
        # Degree patterns
        degrees = [
            "Bachelor", "Master", "PhD", "Doctorate", "MBA", "MS", "BS", "BA", "MA",
            "Bachelor's", "Master's", "Ph.D.", "B.S.", "M.S.", "B.A.", "M.A.",
            "Bachelor of Science", "Master of Science", "Bachelor of Arts", "Master of Arts"
        ]
        
        for degree in degrees:
            patterns.append({"label": "DEGREE", "pattern": degree})
        
        # University patterns
        for university in self.universities_db:
            patterns.append({"label": "UNIVERSITY", "pattern": university})
        
        return patterns
    
    def extract_text_from_pdf_advanced(self, file_path: str) -> str:
        """
        Extract text from PDF using multiple methods for better accuracy.
        """
        text = ""
        
        try:
            # Method 1: pdfplumber (better for complex layouts)
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            # If pdfplumber fails, fallback to PyPDF2
            if not text.strip():
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {str(e)}")
            # Final fallback to pypdf
            try:
                import pypdf
                with open(file_path, 'rb') as file:
                    pdf_reader = pypdf.PdfReader(file)
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
            except Exception as e2:
                logger.error(f"All PDF extraction methods failed: {str(e2)}")
        
        return text.strip()
    
    def detect_sections(self, text: str) -> Dict[str, str]:
        """
        Detect and extract different sections of the resume.
        """
        sections = {}
        
        # Common section headers with variations
        section_patterns = {
            'contact': r'(contact|personal\s+information|contact\s+information)',
            'summary': r'(summary|profile|objective|career\s+objective|professional\s+summary)',
            'experience': r'(experience|work\s+experience|employment|professional\s+experience|career\s+history)',
            'education': r'(education|academic\s+background|educational\s+background)',
            'skills': r'(skills|technical\s+skills|core\s+competencies|technologies)',
            'projects': r'(projects|personal\s+projects|notable\s+projects)',
            'certifications': r'(certifications|certificates|credentials)',
            'awards': r'(awards|honors|achievements|recognition)',
            'languages': r'(languages|language\s+proficiency)',
            'publications': r'(publications|papers|research)',
            'volunteer': r'(volunteer|volunteering|community\s+service)'
        }
        
        lines = text.split('\n')
        current_section = None
        section_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this line is a section header
            found_section = None
            for section_name, pattern in section_patterns.items():
                if re.search(pattern, line.lower()):
                    found_section = section_name
                    break
            
            if found_section:
                # Save previous section
                if current_section and section_content:
                    sections[current_section] = '\n'.join(section_content)
                
                # Start new section
                current_section = found_section
                section_content = []
            else:
                # Add to current section
                if current_section:
                    section_content.append(line)
        
        # Save last section
        if current_section and section_content:
            sections[current_section] = '\n'.join(section_content)
        
        return sections
    
    def extract_contact_info(self, text: str) -> ContactInfo:
        """Extract contact information from resume text."""
        contact = ContactInfo()
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            try:
                # Validate email
                valid_email = validate_email(emails[0])
                contact.email = valid_email.email
            except EmailNotValidError:
                contact.email = emails[0]  # Use even if validation fails
        
        # Extract phone number
        try:
            phone_matches = phonenumbers.PhoneNumberMatcher(text, None)
            for match in phone_matches:
                phone_number = phonenumbers.format_number(match.number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
                contact.phone = phone_number
                break
        except Exception:
            # Fallback to regex
            phone_pattern = r'(\+?1?[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
            phone_match = re.search(phone_pattern, text)
            if phone_match:
                contact.phone = phone_match.group(0)
        
        # Extract LinkedIn
        linkedin_pattern = r'(?:linkedin\.com/in/|linkedin\.com/pub/)([a-zA-Z0-9-]+)'
        linkedin_match = re.search(linkedin_pattern, text.lower())
        if linkedin_match:
            contact.linkedin = f"https://linkedin.com/in/{linkedin_match.group(1)}"
        
        # Extract GitHub
        github_pattern = r'(?:github\.com/)([a-zA-Z0-9-]+)'
        github_match = re.search(github_pattern, text.lower())
        if github_match:
            contact.github = f"https://github.com/{github_match.group(1)}"
        
        # Extract name (attempt from beginning of resume or near contact info)
        name = self._extract_name_from_text(text)
        if name:
            contact.name = name
        
        return contact
    
    def _extract_name_from_text(self, text: str) -> Optional[str]:
        """Extract person's name from resume text."""
        if not self.nlp:
            return None
        
        # Process first few lines where name is usually located
        lines = text.split('\n')[:5]
        text_sample = ' '.join(lines)
        
        doc = self.nlp(text_sample)
        
        # Look for PERSON entities
        for ent in doc.ents:
            if ent.label_ == "PERSON" and len(ent.text.split()) >= 2:
                # Basic validation: should contain at least first and last name
                name_parts = ent.text.strip().split()
                if len(name_parts) >= 2 and all(part.isalpha() for part in name_parts):
                    return ent.text.strip()
        
        return None
    
    def extract_skills(self, text: str, sections: Dict[str, str]) -> List[SkillCategory]:
        """Extract skills organized by categories."""
        skill_categories = []
        
        # Focus on skills section if available, otherwise use full text
        skills_text = sections.get('skills', text)
        
        if not self.nlp:
            return skill_categories
        
        doc = self.nlp(skills_text)
        found_skills = {}
        
        # Extract from NER
        for ent in doc.ents:
            if ent.label_ == "SKILL":
                skill = ent.text.strip()
                category = self._categorize_skill(skill)
                if category not in found_skills:
                    found_skills[category] = set()
                found_skills[category].add(skill)
        
        # Additional pattern-based extraction
        for category, skills_list in self.skills_db.items():
            for skill in skills_list:
                if re.search(r'\b' + re.escape(skill) + r'\b', skills_text, re.IGNORECASE):
                    if category not in found_skills:
                        found_skills[category] = set()
                    found_skills[category].add(skill)
        
        # Convert to schema format
        for category, skills in found_skills.items():
            if skills:
                skill_categories.append(SkillCategory(
                    category=category,
                    skills=list(skills)
                ))
        
        return skill_categories
    
    def _categorize_skill(self, skill: str) -> str:
        """Categorize a skill into predefined categories."""
        skill_lower = skill.lower()
        
        for category, skills_list in self.skills_db.items():
            for known_skill in skills_list:
                if fuzz.ratio(skill_lower, known_skill.lower()) > 85:
                    return category
        
        return "Other"
    
    def extract_experience(self, text: str, sections: Dict[str, str]) -> Tuple[List[ExperienceEntry], Optional[float]]:
        """Extract work experience entries and calculate total years."""
        experience_entries = []
        experience_text = sections.get('experience', text)
        
        if not self.nlp:
            return experience_entries, None
        
        # Pattern for experience entries
        experience_pattern = r'([A-Z][^|\n]*?)(?:\n|$)(.*?)(?=\n[A-Z][^|\n]*?(?:\n|$)|\Z)'
        matches = re.findall(experience_pattern, experience_text, re.DOTALL)
        
        for title_line, details in matches:
            entry = ExperienceEntry()
            
            # Extract company and position
            company_position = self._parse_title_line(title_line)
            entry.position = company_position.get('position')
            entry.company = company_position.get('company')
            
            # Extract dates
            dates = self._extract_dates_from_text(details)
            if dates:
                entry.start_date = dates.get('start')
                entry.end_date = dates.get('end')
            
            # Extract description and technologies
            entry.description = details.strip()
            entry.technologies = self._extract_technologies_from_text(details)
            
            experience_entries.append(entry)
        
        # Calculate total experience
        total_years = self._calculate_total_experience(experience_entries)
        
        return experience_entries, total_years
    
    def _parse_title_line(self, title_line: str) -> Dict[str, str]:
        """Parse job title and company from title line."""
        result = {}
        
        # Common patterns: "Position at Company" or "Position | Company" or "Position - Company"
        patterns = [
            r'(.+?)\s+at\s+(.+)',
            r'(.+?)\s*\|\s*(.+)',
            r'(.+?)\s*-\s*(.+)',
            r'(.+?)\s*,\s*(.+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title_line)
            if match:
                result['position'] = match.group(1).strip()
                result['company'] = match.group(2).strip()
                break
        
        return result
    
    def _extract_dates_from_text(self, text: str) -> Dict[str, str]:
        """Extract start and end dates from text."""
        dates = {}
        
        # Common date patterns
        date_patterns = [
            r'(\w+\s+\d{4})\s*[-–]\s*(\w+\s+\d{4})',
            r'(\d{1,2}/\d{4})\s*[-–]\s*(\d{1,2}/\d{4})',
            r'(\d{4})\s*[-–]\s*(\d{4})',
            r'(\w+\s+\d{4})\s*[-–]\s*(present|current)',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                dates['start'] = match.group(1)
                dates['end'] = match.group(2) if match.group(2).lower() not in ['present', 'current'] else None
                break
        
        return dates
    
    def _extract_technologies_from_text(self, text: str) -> List[str]:
        """Extract technologies/tools mentioned in experience description."""
        technologies = []
        
        for category, skills_list in self.skills_db.items():
            for skill in skills_list:
                if re.search(r'\b' + re.escape(skill) + r'\b', text, re.IGNORECASE):
                    technologies.append(skill)
        
        return list(set(technologies))
    
    def _calculate_total_experience(self, experience_entries: List[ExperienceEntry]) -> Optional[float]:
        """Calculate total years of experience."""
        total_months = 0
        
        for entry in experience_entries:
            if entry.start_date:
                start_date = dateparser.parse(entry.start_date)
                end_date = dateparser.parse(entry.end_date) if entry.end_date else dateparser.parse("today")
                
                if start_date and end_date:
                    months = (end_date.year - start_date.year) * 12 + end_date.month - start_date.month
                    total_months += max(0, months)
        
        return round(total_months / 12.0, 1) if total_months > 0 else None
    
    def extract_education(self, text: str, sections: Dict[str, str]) -> List[EducationEntry]:
        """Extract education information."""
        education_entries = []
        education_text = sections.get('education', text)
        
        if not self.nlp:
            return education_entries
        
        doc = self.nlp(education_text)
        
        # Extract degrees and institutions
        degrees = [ent.text for ent in doc.ents if ent.label_ == "DEGREE"]
        institutions = [ent.text for ent in doc.ents if ent.label_ in ["UNIVERSITY", "ORG"]]
        
        # Simple mapping (can be improved with more sophisticated parsing)
        for i, degree in enumerate(degrees):
            entry = EducationEntry()
            entry.degree = degree
            if i < len(institutions):
                entry.institution = institutions[i]
            education_entries.append(entry)
        
        return education_entries
    
    def extract_projects(self, text: str, sections: Dict[str, str]) -> List[ProjectEntry]:
        """Extract project information."""
        projects = []
        projects_text = sections.get('projects', text)
        
        # Simple project extraction (can be enhanced)
        project_lines = [line.strip() for line in projects_text.split('\n') if line.strip()]
        
        for line in project_lines:
            if len(line) > 10:  # Filter out very short lines
                project = ProjectEntry()
                project.name = line
                project.technologies = self._extract_technologies_from_text(line)
                projects.append(project)
        
        return projects
    
    def parse_resume_advanced(self, text: str) -> ResumeParseResult:
        """
        Parse resume with advanced techniques.
        """
        logger.info(f"Starting advanced resume parsing for text of length {len(text)}")
        
        try:
            # Detect sections
            sections = self.detect_sections(text)
            logger.info(f"Detected sections: {list(sections.keys())}")
            
            # Extract contact information
            contact_info = self.extract_contact_info(text)
            
            # Extract skills
            skills = self.extract_skills(text, sections)
            
            # Extract experience
            experience, total_years = self.extract_experience(text, sections)
            
            # Extract education
            education = self.extract_education(text, sections)
            
            # Extract projects
            projects = self.extract_projects(text, sections)
            
            # Create result
            result = ResumeParseResult(
                contact_info=contact_info,
                skills=skills,
                experience=experience,
                total_experience_years=total_years,
                education=education,
                projects=projects,
                sections_found=list(sections.keys()),
                raw_text_length=len(text)
            )
            
            logger.info(f"Advanced parsing completed: {len(skills)} skill categories, "
                       f"{len(experience)} experience entries, {len(education)} education entries")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in advanced resume parsing: {str(e)}")
            return ResumeParseResult()

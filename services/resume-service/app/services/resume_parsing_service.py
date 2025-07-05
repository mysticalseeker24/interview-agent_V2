"""Advanced Resume parsing service with comprehensive NLP capabilities and multi-template support."""
import re
import logging
import os
import json
import spacy
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import pypdf
from docx import Document
from datetime import datetime
import dateparser
from fuzzywuzzy import process

from app.core.config import get_settings
from app.schemas.resume import (
    ResumeParseResult, ContactInfo, ExperienceEntry,
    ProjectEntry, EducationEntry, SkillCategory,
    CertificationEntry, LanguageEntry
)
from app.services.advanced_resume_parser import AdvancedResumeParser

logger = logging.getLogger(__name__)
settings = get_settings()

# Comprehensive section headers supporting Deedy, RenderCV, and standard templates
SECTION_HEADERS = {
    "summary": r'(professional summary|summary|objective|profile|career objective)',
    "contact": r'(contact|contact information|personal information)',
    "experience": r'(experience|work history|professional experience|employment|career history)',
    "projects": r'(projects|personal projects|notable projects|side projects)',
    "education": r'(education|academic background|educational background)',
    "skills": r'(skills|technical skills|core competencies|technologies|technical expertise)',
    "certifications": r'(certifications|licenses|credentials|professional certifications)',
    "achievements": r'(achievements|awards|honors|recognition|accomplishments)',
    "publications": r'(publications|papers|research|articles)',
    "societies": r'(societies|organizations|professional organizations|memberships)',
    "service": r'(community service|volunteer experience|volunteering|volunteer work)',
    "languages": r'(languages|language proficiency|foreign languages)'
}

# Master skills list - can be loaded from external JSON/YAML
MASTER_SKILLS = [
    # Programming Languages
    "Python", "JavaScript", "Java", "C++", "C#", "Go", "Rust", "TypeScript",
    "PHP", "Ruby", "Swift", "Kotlin", "Scala", "R", "MATLAB", "SQL", "NoSQL",
    "Perl", "Shell", "Bash", "PowerShell", "Objective-C", "Dart", "F#",
    
    # Web Technologies
    "React", "Angular", "Vue.js", "Node.js", "Express", "Django", "Flask",
    "Spring", "Laravel", "Ruby on Rails", "ASP.NET", "jQuery", "HTML", "CSS",
    "SCSS", "SASS", "Bootstrap", "Tailwind CSS", "Next.js", "Nuxt.js",
    "Svelte", "FastAPI", "GraphQL", "REST API", "WebSocket",
    
    # Databases
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", "Oracle",
    "SQL Server", "Cassandra", "DynamoDB", "Neo4j", "Elasticsearch",
    "InfluxDB", "CouchDB", "MariaDB", "Firebase", "Supabase",
    
    # Cloud & DevOps
    "AWS", "Azure", "Google Cloud", "Docker", "Kubernetes", "Jenkins",
    "GitLab CI", "GitHub Actions", "Terraform", "Ansible", "Prometheus",
    "Grafana", "Nagios", "Chef", "Puppet", "Vagrant", "CircleCI",
    "Travis CI", "Heroku", "Vercel", "Netlify",
    
    # AI/ML & Data Science
    "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy", "OpenCV",
    "Transformers", "LangChain", "Pinecone", "Hugging Face", "MLflow",
    "Jupyter", "Apache Spark", "Hadoop", "Kafka", "Airflow", "Databricks",
    "Snowflake", "Power BI", "Tableau", "D3.js", "Matplotlib", "Seaborn",
    "NLTK", "spaCy", "OpenAI", "LLM", "GPT", "BERT", "Computer Vision",
    
    # Mobile Development
    "React Native", "Flutter", "iOS", "Android", "Xamarin", "Ionic",
    "Cordova", "Unity", "Android Studio", "Xcode",
    
    # Testing & Quality
    "Jest", "Pytest", "JUnit", "Selenium", "Cypress", "TestNG", "Mocha",
    "Chai", "Postman", "Newman", "K6", "Unit Testing", "Integration Testing",
    "E2E Testing", "TDD", "BDD", "Automation Testing"
]


class ResumeParsingService:
    """Advanced service for parsing resumes with multi-template support and comprehensive NLP."""
    
    def __init__(self):
        """Initialize the advanced resume parsing service."""
        self.nlp = None
        self.advanced_parser = AdvancedResumeParser()
        self._load_spacy_model()
        self._load_master_skills()
        
    def _load_spacy_model(self):
        """Load spaCy model with custom entity ruler."""
        try:
            logger.info(f"Loading spaCy model: {settings.SPACY_MODEL}")
            self.nlp = spacy.load(settings.SPACY_MODEL)
            logger.info("spaCy model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load spaCy model: {str(e)}; Using fallback NER")
            self.nlp = None
    
    def _load_master_skills(self):
        """Load master skills list from configuration or use default."""
        try:
            # Try to load from external file if it exists
            skills_file = Path("data/master_skills.json")
            if skills_file.exists():
                with open(skills_file, 'r') as f:
                    loaded_skills = json.load(f)
                    self.master_skills = loaded_skills.get('skills', MASTER_SKILLS)
                    logger.info(f"Loaded {len(self.master_skills)} skills from {skills_file}")
            else:
                self.master_skills = MASTER_SKILLS
                logger.info(f"Using default master skills list ({len(self.master_skills)} skills)")
        except Exception as e:
            logger.warning(f"Failed to load master skills: {str(e)}, using defaults")
            self.master_skills = MASTER_SKILLS
            
    def _load_skill_patterns(self) -> List[Dict[str, Any]]:
        """Load skill patterns from configuration."""
        patterns = []
        
        # Common programming languages
        languages = [
            "Python", "JavaScript", "Java", "C++", "C#", "Go", "Rust", "TypeScript",
            "PHP", "Ruby", "Swift", "Kotlin", "Scala", "R", "MATLAB", "SQL"
        ]
        
        # Web technologies
        web_tech = [
            "React", "Angular", "Vue.js", "Node.js", "Express", "Django", "Flask",
            "Spring", "Laravel", "Ruby on Rails", "ASP.NET", "jQuery", "HTML", "CSS"
        ]
        
        # Databases
        databases = [
            "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", "Oracle",
            "SQL Server", "Cassandra", "DynamoDB", "Neo4j", "Elasticsearch"
        ]
        
        # Cloud & DevOps
        cloud_devops = [
            "AWS", "Azure", "Google Cloud", "Docker", "Kubernetes", "Jenkins",
            "GitLab CI", "GitHub Actions", "Terraform", "Ansible", "Prometheus"
        ]
        
        # AI/ML
        ai_ml = [
            "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy", "OpenCV",
            "Transformers", "LangChain", "Pinecone", "Hugging Face", "MLflow"
        ]
        
        # Combine all skills
        all_skills = languages + web_tech + databases + cloud_devops + ai_ml
        
        for skill in all_skills:
            patterns.append({"label": "SKILL", "pattern": skill})
            
        return patterns
        
    def _load_project_patterns(self) -> List[Dict[str, Any]]:
        """Load project patterns from configuration."""
        patterns = []
        
        # Common project keywords
        project_keywords = [
            "E-commerce Platform", "Web Application", "Mobile App", "API", "Dashboard",
            "Machine Learning Model", "Data Pipeline", "Chatbot", "CRM System",
            "Inventory Management", "Blog Platform", "Social Media App", "Game",
            "Analytics Tool", "Recommendation System", "Authentication System"
        ]
        
        for keyword in project_keywords:
            patterns.append({"label": "PROJECT", "pattern": keyword})
            
        return patterns
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """
        Extract text from PDF using multiple methods with fallback strategy.
        Tries pypdf first, then advanced parser methods.
        """
        try:
            # Method 1: Try pypdf for speed
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            
            # Validate extraction quality
            if len(text.strip()) < 200:
                logger.warning("pypdf extracted too little text, trying advanced methods")
                return self.advanced_parser.extract_text_from_pdf_advanced(file_path)
            
            return text.strip()
            
        except Exception as e:
            logger.warning(f"pypdf failed ({str(e)}), falling back to advanced extraction")
            return self.advanced_parser.extract_text_from_pdf_advanced(file_path)
    
    def split_sections(self, text: str) -> Dict[str, str]:
        """
        Advanced section detection supporting multiple resume templates.
        """
        sections = {}
        
        # Create combined regex pattern for all section headers
        header_patterns = []
        for section_key, pattern in SECTION_HEADERS.items():
            header_patterns.append(f"(?P<{section_key}>{pattern})")
        
        combined_pattern = r'(?im)^(' + '|'.join(header_patterns) + r')\s*$'
        
        # Split text by section headers
        parts = re.split(combined_pattern, text)
        
        current_section = None
        for i, part in enumerate(parts):
            part = part.strip()
            if not part:
                continue
                
            # Check if this part is a section header
            for section_key, pattern in SECTION_HEADERS.items():
                if re.fullmatch(pattern, part, flags=re.IGNORECASE):
                    current_section = section_key
                    break
            else:
                # This is content for the current section
                if current_section and len(part) > 10:  # Ignore very short content
                    sections[current_section] = part
                    current_section = None
        
        # Fallback to basic section detection if regex approach fails
        if not sections:
            sections = self.advanced_parser.detect_sections(text)
        
        logger.info(f"Detected sections: {list(sections.keys())}")
        return sections
    
    def extract_contact_and_summary(self, text: str) -> Tuple[ContactInfo, Optional[str]]:
        """Extract contact information and professional summary."""
        # Use advanced parser for contact extraction
        contact_info = self.advanced_parser.extract_contact_info(text)
        
        # Extract summary/objective
        summary = None
        summary_patterns = [
            r'(?i)(?:professional\s+)?summary[:\s]*\n(.*?)(?=\n[A-Z]|$)',
            r'(?i)objective[:\s]*\n(.*?)(?=\n[A-Z]|$)',
            r'(?i)profile[:\s]*\n(.*?)(?=\n[A-Z]|$)'
        ]
        
        for pattern in summary_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                summary = match.group(1).strip()
                break
        
        return contact_info, summary
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """
        Extract text from DOCX file.
        
        Args:
            file_path: Path to DOCX file
            
        Returns:
            Extracted text
        """
        try:
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from DOCX {file_path}: {str(e)}")
            return ""
    
    def extract_text_from_txt(self, file_path: str) -> str:
        """
        Extract text from TXT file.
        
        Args:
            file_path: Path to TXT file
            
        Returns:
            Extracted text
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read().strip()
        except Exception as e:
            logger.error(f"Error extracting text from TXT {file_path}: {str(e)}")
            return ""
    
    def extract_text_from_file(self, file_path: str, file_type: str) -> str:
        """
        Extract text from file based on file type.
        
        Args:
            file_path: Path to file
            file_type: Type of file (pdf, docx, doc, txt)
            
        Returns:
            Extracted text
        """
        file_type = file_type.lower()
        
        if file_type == "pdf":
            return self.extract_text_from_pdf(file_path)
        elif file_type in ["docx", "doc"]:
            return self.extract_text_from_docx(file_path)
        elif file_type == "txt":
            return self.extract_text_from_txt(file_path)
        else:
            logger.warning(f"Unsupported file type: {file_type}")
            return ""
    
    def _extract_technologies(self, text: str) -> List[str]:
        """Extract technologies from text using fuzzy matching."""
        technologies = []
        
        # Extract potential technology names
        potential_techs = re.findall(r'\b[A-Za-z][A-Za-z0-9\+#\.\-]{1,20}\b', text)
        
        for tech in potential_techs:
            tech = tech.strip()
            if len(tech) < 2:
                continue
            
            # Fuzzy match against master skills
            match, score = process.extractOne(tech, self.master_skills)
            if score > 85:
                technologies.append(match)
        
        return list(set(technologies))  # Remove duplicates
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string using dateparser."""
        if not date_str:
            return None
        
        try:
            parsed_date = dateparser.parse(date_str.strip())
            return parsed_date.date().isoformat() if parsed_date else None
        except Exception:
            return None
    
    def compute_total_experience(self, experiences: List[ExperienceEntry]) -> Optional[float]:
        """Calculate total work experience in years."""
        total_days = 0
        
        for exp in experiences:
            if not exp.start_date:
                continue
            
            start_date = dateparser.parse(exp.start_date)
            end_date = dateparser.parse(exp.end_date) if exp.end_date else dateparser.parse("today")
            
            if start_date and end_date:
                days = (end_date - start_date).days
                total_days += max(0, days)
        
        return round(total_days / 365.25, 1) if total_days > 0 else None
    
    def compute_confidence_score(self, result: ResumeParseResult) -> float:
        """Compute overall parsing confidence score."""
        score = 0.0
        
        # Contact information (0.2 max)
        if result.contact_info.name:
            score += 0.05
        if result.contact_info.email:
            score += 0.05
        if result.contact_info.phone:
            score += 0.05
        if result.contact_info.linkedin or result.contact_info.github:
            score += 0.05
        
        # Core sections (0.6 max)
        score += min(1.0, len(result.skills)) * 0.15
        score += min(1.0, len(result.experience)) * 0.25
        score += min(1.0, len(result.education)) * 0.1
        score += min(1.0, len(result.projects)) * 0.1
        
        # Additional sections (0.2 max)
        score += min(1.0, len(result.certifications)) * 0.05
        score += min(1.0, len(result.publications)) * 0.05
        score += min(1.0, len(result.awards)) * 0.05
        score += min(1.0, len(result.volunteer_experience)) * 0.05
        
        return round(min(score, 1.0), 2)
    
    def parse_resume(self, text: str) -> ResumeParseResult:
        """
        Main parsing method with comprehensive multi-template support.
        """
        logger.info(f"Starting advanced resume parsing for text of length {len(text)}")
        
        try:
            # Split text into sections
            sections = self.split_sections(text)
            
            # Extract contact information and summary
            contact_info, summary = self.extract_contact_and_summary(text)
            
            # Parse each section
            experience = self.parse_experience(sections.get("experience", ""))
            projects = self.parse_projects(sections.get("projects", ""))
            education = self.parse_education(sections.get("education", ""))
            skills = self.parse_skills(sections.get("skills", ""))
            certifications = self.parse_certifications(sections.get("certifications", ""))
            publications = self.parse_publications(sections.get("publications", ""))
            awards = self.parse_simple_list(sections.get("achievements", ""))
            volunteer_experience = self.parse_simple_list(sections.get("service", ""))

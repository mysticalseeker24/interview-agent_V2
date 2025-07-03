"""Resume parsing service with NLP capabilities."""
import logging
import os
import json
import spacy
from typing import Dict, List, Optional, Any
from pathlib import Path
import pypdf
from docx import Document
from datetime import datetime

from app.core.config import get_settings
from app.schemas.resume import ResumeParseResult

logger = logging.getLogger(__name__)

settings = get_settings()


class ResumeParsingService:
    """Service for parsing resumes using NLP and extracting structured data."""
    
    def __init__(self):
        """Initialize the resume parsing service."""
        self.nlp = None
        self._load_spacy_model()
        
    def _load_spacy_model(self):
        """Load spaCy model with custom entity ruler."""
        try:
            logger.info(f"Loading spaCy model: {settings.SPACY_MODEL}")
            self.nlp = spacy.load(settings.SPACY_MODEL)
            
            # Add custom entity ruler for skills and projects
            if "entity_ruler" not in self.nlp.pipe_names:
                ruler = self.nlp.add_pipe("entity_ruler", before="ner")
            else:
                ruler = self.nlp.get_pipe("entity_ruler")
            
            # Load skill patterns
            skill_patterns = self._load_skill_patterns()
            project_patterns = self._load_project_patterns()
            
            # Add patterns to ruler
            ruler.add_patterns(skill_patterns + project_patterns)
            
            logger.info("spaCy model loaded successfully with custom patterns")
            
        except Exception as e:
            logger.error(f"Error loading spaCy model: {str(e)}")
            self.nlp = None
            
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
        Extract text from PDF file.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text
        """
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {str(e)}")
            return ""
    
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
    
    def parse_resume(self, text: str) -> ResumeParseResult:
        """
        Parse resume text using spaCy NLP.
        
        Args:
            text: Resume text to parse
            
        Returns:
            Parsed resume data
        """
        if not self.nlp:
            logger.error("spaCy model not loaded")
            return ResumeParseResult(skills=[], projects=[])
        
        try:
            # Process text with spaCy
            doc = self.nlp(text)
            
            # Extract skills and projects
            skills = list({ent.text for ent in doc.ents if ent.label_ == 'SKILL'})
            projects = list({ent.text for ent in doc.ents if ent.label_ == 'PROJECT'})
            
            # Extract additional information
            experience_years = self._extract_experience_years(text)
            education = self._extract_education(text)
            certifications = self._extract_certifications(text)
            languages = self._extract_languages(text)
            
            logger.info(f"Parsed resume: {len(skills)} skills, {len(projects)} projects")
            
            return ResumeParseResult(
                skills=skills,
                projects=projects,
                experience_years=experience_years,
                education=education,
                certifications=certifications,
                languages=languages
            )
            
        except Exception as e:
            logger.error(f"Error parsing resume: {str(e)}")
            return ResumeParseResult(skills=[], projects=[])
    
    def _extract_experience_years(self, text: str) -> Optional[int]:
        """Extract years of experience from text."""
        import re
        
        # Look for patterns like "5 years experience", "3+ years", etc.
        patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
            r'(\d+)\+?\s*years?\s*(?:of\s*)?(?:professional\s*)?experience',
            r'experience\s*(?:of\s*)?(\d+)\+?\s*years?'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                return int(matches[0])
        
        return None
    
    def _extract_education(self, text: str) -> List[str]:
        """Extract education information from text."""
        import re
        
        education = []
        
        # Common degree patterns
        degree_patterns = [
            r'(bachelor\'?s?\s+(?:of\s+)?(?:science|arts|engineering|computer science))',
            r'(master\'?s?\s+(?:of\s+)?(?:science|arts|engineering|computer science))',
            r'(phd|doctorate|ph\.d\.?)',
            r'(mba|master of business administration)',
            r'(b\.?s\.?|b\.?a\.?|m\.?s\.?|m\.?a\.?)',
        ]
        
        for pattern in degree_patterns:
            matches = re.findall(pattern, text.lower())
            education.extend(matches)
        
        return list(set(education))
    
    def _extract_certifications(self, text: str) -> List[str]:
        """Extract certification information from text."""
        import re
        
        certifications = []
        
        # Common certification patterns
        cert_patterns = [
            r'(aws\s+certified\s+[\w\s]+)',
            r'(azure\s+certified\s+[\w\s]+)',
            r'(google\s+cloud\s+certified\s+[\w\s]+)',
            r'(certified\s+[\w\s]+engineer)',
            r'(pmp|project management professional)',
            r'(cissp|certified information systems security professional)',
        ]
        
        for pattern in cert_patterns:
            matches = re.findall(pattern, text.lower())
            certifications.extend(matches)
        
        return list(set(certifications))
    
    def _extract_languages(self, text: str) -> List[str]:
        """Extract programming languages from text."""
        # This is already handled by the skill extraction
        # Return empty list to avoid duplication
        return []

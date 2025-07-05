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
    
    def parse_resume(self, text: str) -> ResumeParseResult:
        """
        Parse resume text using advanced NLP with fallback to legacy parsing.
        
        Args:
            text: Resume text to parse
            
        Returns:
            Parsed resume data
        """
        logger.info("Starting resume parsing with advanced methods")
        
        try:
            # Use advanced parser
            result = self.advanced_parser.parse_resume_advanced(text)
            
            # Validate result - if we got meaningful data, return it
            if (result.contact_info.name or result.contact_info.email or 
                result.skills or result.experience or result.education):
                logger.info("Advanced parsing successful")
                return result
            else:
                logger.warning("Advanced parsing returned empty results, falling back to legacy")
                return self._parse_resume_legacy(text)
                
        except Exception as e:
            logger.error(f"Advanced parsing failed: {str(e)}, falling back to legacy")
            return self._parse_resume_legacy(text)
    
    def _parse_resume_legacy(self, text: str) -> ResumeParseResult:
        """
        Legacy resume parsing method for fallback.
        """
        if not self.nlp:
            logger.error("spaCy model not loaded")
            return ResumeParseResult()
        
        try:
            # Process text with spaCy
            doc = self.nlp(text)
            
            # Extract skills and projects using legacy method
            skills = list({ent.text for ent in doc.ents if ent.label_ == 'SKILL'})
            projects = list({ent.text for ent in doc.ents if ent.label_ == 'PROJECT'})
            
            # Extract additional information
            experience_years = self._extract_experience_years(text)
            education = self._extract_education(text)
            certifications = self._extract_certifications(text)
            languages = self._extract_languages(text)
            
            # Convert to new schema format
            from app.schemas.resume import SkillCategory, ContactInfo
            
            # Create skill categories
            skill_categories = []
            if skills:
                skill_categories.append(SkillCategory(category="General", skills=skills))
            
            # Create basic contact info
            contact_info = ContactInfo()
            
            logger.info(f"Legacy parsing completed: {len(skills)} skills, {len(projects)} projects")
            
            return ResumeParseResult(
                contact_info=contact_info,
                skills=skill_categories,
                total_experience_years=float(experience_years) if experience_years else None,
                raw_text_length=len(text)
            )
            
        except Exception as e:
            logger.error(f"Error in legacy resume parsing: {str(e)}")
            return ResumeParseResult()
    
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
    
    def parse_experience(self, block: str) -> List[ExperienceEntry]:
        """Parse work experience with multiple format support."""
        entries = []
        
        # Split by double newlines to separate entries
        for chunk in re.split(r'\n{2,}', block):
            chunk = chunk.strip()
            if len(chunk) < 20:  # Skip very short chunks
                continue
            
            entry = ExperienceEntry()
            
            # Try multiple patterns for job title and company
            patterns = [
                # Pattern 1: "Senior Developer @ Google (Jan 2020 – Present)"
                r'(.+?)\s+@\s+(.+?)\s+\(([^–]+)–([^)]+)\)',
                # Pattern 2: "Senior Developer | Google | Jan 2020 - Present"
                r'(.+?)\s*\|\s*(.+?)\s*\|\s*([^-]+)-([^|]+)',
                # Pattern 3: "Senior Developer, Google (Jan 2020 - Present)"
                r'(.+?),\s*(.+?)\s+\(([^-]+)-([^)]+)\)',
                # Pattern 4: "Google - Senior Developer (Jan 2020 - Present)"
                r'(.+?)\s*-\s*(.+?)\s+\(([^-]+)-([^)]+)\)',
            ]
            
            parsed = False
            for pattern in patterns:
                match = re.search(pattern, chunk)
                if match:
                    groups = [g.strip() for g in match.groups()]
                    if 'google' in groups[1].lower() or 'microsoft' in groups[1].lower():
                        # Company first pattern
                        entry.company = groups[0]
                        entry.position = groups[1]
                    else:
                        # Position first pattern
                        entry.position = groups[0]
                        entry.company = groups[1]
                    
                    entry.start_date = self._parse_date(groups[2])
                    entry.end_date = self._parse_date(groups[3]) if groups[3].lower() not in ['present', 'current'] else None
                    parsed = True
                    break
            
            if not parsed:
                # Fallback: try to extract company and position from first line
                first_line = chunk.split('\n')[0]
                if ' at ' in first_line:
                    parts = first_line.split(' at ')
                    entry.position = parts[0].strip()
                    entry.company = parts[1].strip()
                elif ' - ' in first_line:
                    parts = first_line.split(' - ')
                    entry.position = parts[0].strip()
                    entry.company = parts[1].strip()
                else:
                    entry.position = first_line.strip()
            
            # Extract description (everything after first line)
            lines = chunk.split('\n')
            if len(lines) > 1:
                entry.description = '\n'.join(lines[1:]).strip()
            
            # Extract technologies from description
            entry.technologies = self._extract_technologies(chunk)
            
            # Extract achievements (lines starting with bullet points)
            achievements = []
            for line in lines[1:]:
                line = line.strip()
                if line.startswith(('•', '▪', '-', '*')):
                    achievements.append(line[1:].strip())
            entry.achievements = achievements
            
            entries.append(entry)
        
        return entries
    
    def parse_projects(self, block: str) -> List[ProjectEntry]:
        """Parse projects with enhanced pattern recognition."""
        projects = []
        
        for chunk in re.split(r'\n{2,}', block):
            chunk = chunk.strip()
            if len(chunk) < 15:
                continue
            
            project = ProjectEntry()
            lines = chunk.split('\n')
            
            # First line is usually project name
            project.name = lines[0].strip()
            
            # Look for URL patterns (from Deedy template \href)
            url_match = re.search(r'https?://[^\s\)]+', chunk)
            if url_match:
                project.url = url_match.group(0)
            
            # Extract description
            desc_lines = []
            for line in lines[1:]:
                line = line.strip()
                if line and not line.startswith(('•', '▪', '-', '*')):
                    desc_lines.append(line)
            project.description = ' '.join(desc_lines)
            
            # Extract technologies
            project.technologies = self._extract_technologies(chunk)
            
            projects.append(project)
        
        return projects
    
    def parse_education(self, block: str) -> List[EducationEntry]:
        """Parse education with degree and institution extraction."""
        entries = []
        
        for chunk in re.split(r'\n{2,}', block):
            chunk = chunk.strip()
            if len(chunk) < 10:
                continue
            
            entry = EducationEntry()
            
            # Try to parse degree and institution
            patterns = [
                # "Master of Science in Computer Science | Stanford University"
                r'(.+?)\s*\|\s*(.+)',
                # "Master of Science, Stanford University"
                r'(.+?),\s*(.+)',
                # "Stanford University — Master of Science"
                r'(.+?)\s*—\s*(.+)',
                # "Bachelor's Degree in Computer Science\nUC Berkeley"
                r'(.+)\n(.+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, chunk)
                if match:
                    part1, part2 = match.groups()
                    
                    # Determine which is degree and which is institution
                    degree_keywords = ['bachelor', 'master', 'phd', 'doctorate', 'mba', 'degree']
                    if any(kw in part1.lower() for kw in degree_keywords):
                        entry.degree = part1.strip()
                        entry.institution = part2.strip()
                    else:
                        entry.institution = part1.strip()
                        entry.degree = part2.strip()
                    break
            
            # Extract GPA if present
            gpa_match = re.search(r'GPA:?\s*([\d.]+)', chunk, re.IGNORECASE)
            if gpa_match:
                entry.gpa = gpa_match.group(1)
            
            entries.append(entry)
        
        return entries
    
    def parse_skills(self, block: str) -> List[SkillCategory]:
        """Parse skills with fuzzy matching against master list."""
        # Split skills by common delimiters
        raw_skills = re.split(r'[\n,•▪\-\*]', block)
        
        found_skills = set()
        categorized_skills = {}
        
        for skill_text in raw_skills:
            skill_text = skill_text.strip()
            if len(skill_text) < 2:
                continue
            
            # Remove common prefixes/suffixes
            skill_text = re.sub(r'^(proficient in|experience with|skilled in|knowledge of)\s*', '', skill_text, flags=re.IGNORECASE)
            skill_text = skill_text.strip('.,;:')
            
            # Fuzzy match against master skills
            match, score = process.extractOne(skill_text, self.master_skills)
            if score > 80:  # Threshold for fuzzy matching
                found_skills.add(match)
                
                # Categorize skill
                category = self._categorize_skill(match)
                if category not in categorized_skills:
                    categorized_skills[category] = set()
                categorized_skills[category].add(match)
        
        # Convert to schema format
        skill_categories = []
        for category, skills in categorized_skills.items():
            if skills:
                skill_categories.append(SkillCategory(
                    category=category,
                    skills=sorted(list(skills))
                ))
        
        # If no categorized skills found, create a general category
        if not skill_categories and found_skills:
            skill_categories.append(SkillCategory(
                category="Technical",
                skills=sorted(list(found_skills))
            ))
        
        return skill_categories
    
    def _categorize_skill(self, skill: str) -> str:
        """Categorize a skill into predefined categories."""
        skill_lower = skill.lower()
        
        # Programming languages
        if skill in ["Python", "JavaScript", "Java", "C++", "C#", "Go", "Rust", "TypeScript", "PHP", "Ruby", "Swift", "Kotlin", "Scala", "R", "MATLAB"]:
            return "Programming Languages"
        
        # Web technologies
        elif skill in ["React", "Angular", "Vue.js", "Node.js", "Express", "Django", "Flask", "HTML", "CSS", "Bootstrap"]:
            return "Web Technologies"
        
        # Databases
        elif skill in ["PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", "Oracle", "SQL Server", "Elasticsearch"]:
            return "Databases"
        
        # Cloud & DevOps
        elif skill in ["AWS", "Azure", "Google Cloud", "Docker", "Kubernetes", "Jenkins", "Terraform", "Ansible"]:
            return "Cloud & DevOps"
        
        # AI/ML
        elif skill in ["TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy", "OpenCV", "MLflow"]:
            return "AI/ML & Data Science"
        
        else:
            return "Technical"
    
    def parse_certifications(self, block: str) -> List[CertificationEntry]:
        """Parse certifications with issuer detection."""
        certifications = []
        
        for line in block.split('\n'):
            line = line.strip()
            if not line or line.startswith(('•', '▪', '-', '*')):
                line = line[1:].strip()
            
            if len(line) < 5:
                continue
            
            cert = CertificationEntry(name=line)
            
            # Try to extract issuer
            if 'aws' in line.lower():
                cert.issuer = "Amazon Web Services"
            elif 'google' in line.lower():
                cert.issuer = "Google"
            elif 'microsoft' in line.lower() or 'azure' in line.lower():
                cert.issuer = "Microsoft"
            elif 'oracle' in line.lower():
                cert.issuer = "Oracle"
            
            certifications.append(cert)
        
        return certifications
    
    def parse_publications(self, block: str) -> List[str]:
        """Parse publications with DOI and citation detection."""
        publications = []
        
        for line in block.split('\n'):
            line = line.strip()
            if len(line) < 10:
                continue
            
            # Look for academic patterns
            if any(pattern in line.lower() for pattern in ['doi:', 'arxiv:', 'conference:', 'journal:']):
                publications.append(line)
            elif re.search(r'\(\d{4}\)', line):  # Year in parentheses
                publications.append(line)
        
        return publications
    
    def parse_simple_list(self, block: str) -> List[str]:
        """Parse simple lists like awards, societies, etc."""
        items = []
        
        for line in block.split('\n'):
            line = line.strip()
            if line.startswith(('•', '▪', '-', '*')):
                line = line[1:].strip()
            
            if len(line) > 3:
                items.append(line)
        
        return items

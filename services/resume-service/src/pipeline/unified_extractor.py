"""
Stage 2: Unified Extractor Module
Single module that segments text and extracts all entities.
"""
import logging
import re
from typing import Dict, List, Tuple, Optional, Set
from datetime import datetime

import spacy
import dateparser
import phonenumbers
from thefuzz import process
from email_validator import validate_email, EmailNotValidError

from ..schema import (
    ContactInfo, ExperienceEntry, ProjectEntry, EducationEntry,
    SkillCategory, CertificationEntry
)

logger = logging.getLogger(__name__)


class UnifiedExtractor:
    """
    Single extractor that handles all resume sections and entities.
    Uses regex, spaCy NER, fuzzy matching, and optional LLM enhancement.
    """
    
    def __init__(self, use_llm: bool = False, openai_api_key: Optional[str] = None):
        self.use_llm = use_llm
        self.openai_api_key = openai_api_key
        self.nlp = self._load_spacy_model()
        self.master_skills = self._load_master_skills()
        self.domain_keywords = self._load_domain_keywords()
        
        # Compiled regex patterns for performance
        self._compile_patterns()
    
    def _load_spacy_model(self):
        """Load spaCy model for NER."""
        try:
            return spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model 'en_core_web_sm' not found. Install with: python -m spacy download en_core_web_sm")
            return None
    
    def _load_master_skills(self) -> Dict[str, List[str]]:
        """Load comprehensive skills database organized by category."""
        return {
            "Programming Languages": [
                "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Rust",
                "PHP", "Ruby", "Swift", "Kotlin", "Scala", "R", "MATLAB", "SQL", "NoSQL",
                "HTML", "CSS", "Bash", "PowerShell", "Perl", "Lua", "Dart", "F#"
            ],
            "Web Technologies": [
                "React", "Angular", "Vue.js", "Node.js", "Express", "Django", "Flask",
                "FastAPI", "Spring", "Laravel", "Ruby on Rails", "ASP.NET", "Next.js",
                "Nuxt.js", "Svelte", "jQuery", "Bootstrap", "Tailwind CSS", "GraphQL",
                "REST API", "WebSocket", "Progressive Web Apps", "PWA"
            ],
            "Cloud & DevOps": [
                "AWS", "Azure", "Google Cloud", "GCP", "Docker", "Kubernetes", "Jenkins",
                "GitLab CI", "GitHub Actions", "CircleCI", "Travis CI", "Terraform",
                "Ansible", "Chef", "Puppet", "Vagrant", "Prometheus", "Grafana",
                "Nagios", "Helm", "Istio", "Service Mesh"
            ],
            "Databases": [
                "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", "Oracle",
                "SQL Server", "Cassandra", "DynamoDB", "Neo4j", "Elasticsearch",
                "InfluxDB", "CouchDB", "MariaDB", "Amazon RDS", "Azure SQL",
                "Google Cloud SQL", "Firebase", "Supabase"
            ],
            "AI/ML & Data Science": [
                "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy", "OpenCV",
                "Keras", "XGBoost", "LightGBM", "Hugging Face", "Transformers",
                "BERT", "GPT", "LLM", "Computer Vision", "NLP", "Deep Learning",
                "Machine Learning", "Data Science", "MLflow", "Kubeflow"
            ],
            "Mobile Development": [
                "React Native", "Flutter", "iOS", "Android", "Xamarin", "Ionic",
                "Cordova", "Unity", "Android Studio", "Xcode", "Swift UI", "Jetpack Compose"
            ],
            "Testing & Quality": [
                "Jest", "Pytest", "JUnit", "Selenium", "Cypress", "TestNG", "Mocha",
                "Chai", "Postman", "Newman", "K6", "Unit Testing", "Integration Testing",
                "E2E Testing", "TDD", "BDD", "Automation Testing"
            ]
        }
    
    def _load_domain_keywords(self) -> Dict[str, List[str]]:
        """Load domain classification keywords."""
        return {
            "Full-Stack Development": ["full-stack", "frontend", "backend", "web development", "MEAN", "MERN", "LAMP"],
            "DevOps Engineering": ["devops", "ci/cd", "infrastructure", "deployment", "kubernetes", "docker", "terraform"],
            "Data Science": ["data science", "machine learning", "analytics", "statistics", "big data", "data mining"],
            "AI Engineering": ["artificial intelligence", "deep learning", "neural networks", "computer vision", "nlp"],
            "Mobile Development": ["mobile app", "ios development", "android development", "react native", "flutter"],
            "Cloud Architecture": ["cloud computing", "aws", "azure", "microservices", "serverless", "distributed systems"],
            "Security Engineering": ["cybersecurity", "security", "penetration testing", "vulnerability", "encryption"],
            "Product Management": ["product management", "roadmap", "stakeholder", "requirements", "user stories"]
        }
    
    def _compile_patterns(self):
        """Compile frequently used regex patterns."""
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.phone_pattern = re.compile(r'(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})')
        self.linkedin_pattern = re.compile(r'(?:linkedin\.com/in/|linkedin\.com/pub/)([a-zA-Z0-9-]+)')
        self.github_pattern = re.compile(r'(?:github\.com/)([a-zA-Z0-9-]+)')
        self.url_pattern = re.compile(r'https?://[^\s]+')
        self.metrics_pattern = re.compile(r'(\d+\.?\d*\s*(?:%|ms|s|x|times|days?|years?|months?|weeks?|million|billion|k|K|M|B|\$))')
        
        # Additional patterns for better contact extraction
        self.phone_alt_pattern = re.compile(r'(?:phone|tel|mobile|cell)[\s:]*([+]?[0-9\s.\-()]+)', re.IGNORECASE)
        self.email_alt_pattern = re.compile(r'(?:email|e-mail)[\s:]*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})', re.IGNORECASE)
    
    def extract_all(self, text: str) -> Dict:
        """
        Main extraction method that processes all sections.
        
        Returns a dictionary with all extracted entities.
        """
        logger.info(f"Starting unified extraction on {len(text)} characters")
        
        # Stage 2.1: Section Splitting
        sections = self._split_sections(text)
        logger.info(f"Detected sections: {list(sections.keys())}")
        
        # Stage 2.2: Entity Extraction
        results = {
            'contact': self._extract_contact(text),
            'summary': self._extract_summary(sections.get('summary', '')),
            'experience': self._extract_experience(sections.get('experience', '')),
            'projects': self._extract_projects(sections.get('projects', '')),
            'education': self._extract_education(sections.get('education', '')),
            'skills': self._extract_skills(sections.get('skills', '')),
            'certifications': self._extract_certifications(sections.get('certifications', '') + '\n' + sections.get('achievements', '')),
            'achievements': self._extract_achievements(sections.get('achievements', '') + '\n' + sections.get('certifications', '')),
            'domains': self._detect_domains(text),
            'sections_detected': list(sections.keys())
        }
        
        # Stage 2.3: LLM Enhancement (optional)
        if self.use_llm and self.openai_api_key:
            results = self._enhance_with_llm(text, results)
        
        return results
    
    def _split_sections(self, text: str) -> Dict[str, str]:
        """
        Split resume text into logical sections using header detection.
        """
        sections = {}
        
        # Define section header patterns (case-insensitive)
        section_patterns = {
            'summary': r'(?i)^(professional\s+summary|summary|objective|profile|career\s+objective)\s*$',
            'experience': r'(?i)^(experience|work\s+history|professional\s+experience|employment|career\s+history|work\s+experience)\s*$',
            'projects': r'(?i)^(projects|personal\s+projects|notable\s+projects|key\s+projects|side\s+projects)\s*$',
            'education': r'(?i)^(education|academic\s+background|educational\s+background)\s*$',
            'skills': r'(?i)^(skills|technical\s+skills|core\s+competencies|technologies|expertise|technical\s+expertise)\s*$',
            'certifications': r'(?i)^(certifications?|licenses?|credentials?|professional\s+certifications?|certifications?\s*&\s*achievements?)\s*$',
            'achievements': r'(?i)^(achievements?|awards?|honors?|recognition|accomplishments?|certifications?\s*&\s*achievements?)\s*$'
        }
        
        lines = text.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line_stripped = line.strip()
            
            # Check if line matches any section header
            matched_section = None
            for section_key, pattern in section_patterns.items():
                if re.match(pattern, line_stripped):
                    matched_section = section_key
                    break
            
            if matched_section:
                # Save previous section
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # Start new section
                current_section = matched_section
                current_content = []
            else:
                # Add line to current section
                if current_section:
                    current_content.append(line)
        
        # Save final section
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def _extract_contact(self, text: str) -> ContactInfo:
        """Extract contact information from entire text."""
        contact = ContactInfo()
        
        # Extract email - look in first 500 characters primarily
        first_part = text[:500]
        email_matches = self.email_pattern.findall(first_part)
        if not email_matches:
            # Try alternative pattern
            alt_matches = self.email_alt_pattern.findall(first_part)
            if alt_matches:
                email_matches = alt_matches
            else:
                # Fallback to full text
                email_matches = self.email_pattern.findall(text)
        
        if email_matches:
            # Validate email
            try:
                valid_email = validate_email(email_matches[0])
                contact.email = valid_email.email
            except EmailNotValidError:
                contact.email = email_matches[0]  # Still keep invalid email for reference
        
        # Extract phone - look in first 500 characters primarily
        first_part = text[:500]
        phone_matches = self.phone_pattern.findall(first_part)
        if not phone_matches:
            # Try alternative pattern
            alt_matches = self.phone_alt_pattern.findall(first_part)
            if alt_matches:
                phone_matches = [alt_matches[0]]
            else:
                # Fallback to full text
                phone_matches = self.phone_pattern.findall(text)
        
        if phone_matches:
            try:
                # Handle tuple result from regex groups
                if isinstance(phone_matches[0], tuple):
                    phone_str = ''.join(phone_matches[0])
                else:
                    phone_str = phone_matches[0]
                
                # Parse and format phone number
                parsed = phonenumbers.parse(phone_str, "US")
                if phonenumbers.is_valid_number(parsed):
                    contact.phone = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL)
                else:
                    contact.phone = phone_str  # Keep raw phone if invalid
            except:
                phone_str = phone_matches[0] if isinstance(phone_matches[0], str) else ''.join(phone_matches[0])
                contact.phone = phone_str
        
        # Extract LinkedIn
        linkedin_match = self.linkedin_pattern.search(text.lower())
        if linkedin_match:
            contact.linkedin = f"https://linkedin.com/in/{linkedin_match.group(1)}"
        
        # Extract GitHub
        github_match = self.github_pattern.search(text.lower())
        if github_match:
            contact.github = f"https://github.com/{github_match.group(1)}"
        
        # Extract name using spaCy NER
        if self.nlp:
            # Look for name in first few lines
            first_lines = '\n'.join(text.split('\n')[:5])
            doc = self.nlp(first_lines)
            
            for ent in doc.ents:
                if ent.label_ == "PERSON" and len(ent.text.split()) >= 2:
                    # Basic validation
                    name_parts = ent.text.strip().split()
                    if len(name_parts) >= 2 and all(part.isalpha() for part in name_parts[:2]):
                        contact.name = ent.text.strip()
                        break
        
        return contact
    
    def _extract_summary(self, text: str) -> Optional[str]:
        """Extract professional summary."""
        if not text.strip():
            return None
        
        # Clean up the text
        summary = text.strip()
        
        # Remove common header words if they appear at start
        summary = re.sub(r'^(professional\s+summary|summary|objective|profile)[\s:]*', '', summary, flags=re.IGNORECASE)
        
        return summary.strip() if summary.strip() else None
    
    def _extract_experience(self, text: str) -> List[ExperienceEntry]:
        """Extract work experience entries with enhanced bullet and metrics parsing."""
        experiences = []
        
        # Split into job entries (separated by double newlines or clear job patterns)
        job_chunks = re.split(r'\n\s*\n', text)
        
        for chunk in job_chunks:
            if len(chunk.strip()) < 30:  # Skip very short chunks
                continue
            
            experience = self._parse_single_experience(chunk)
            if experience:
                experiences.append(experience)
        
        return experiences
    
    def _parse_single_experience(self, chunk: str) -> Optional[ExperienceEntry]:
        """Parse a single experience entry."""
        lines = chunk.strip().split('\n')
        header = lines[0] if lines else ""
        body_lines = lines[1:] if len(lines) > 1 else []
        
        experience = ExperienceEntry(raw_text=chunk)
        
        # Parse header for position, company, dates, location
        # Patterns like: "Senior Engineer @ Google (Jan 2020 - Present) | Remote"
        header_patterns = [
            r'(.+?)\s+@\s+(.+?)\s+\(([^)]+)\)\s*\|\s*(.+)',
            r'(.+?)\s+at\s+(.+?)\s+\(([^)]+)\)\s*\|\s*(.+)',
            r'(.+?)\s*\|\s*(.+?)\s*\|\s*([^|]+)',
            r'(.+?)\s+@\s+(.+?)\s+\(([^)]+)\)',
            r'(.+?)\s+at\s+(.+?)\s+\(([^)]+)\)'
        ]
        
        for pattern in header_patterns:
            match = re.search(pattern, header)
            if match:
                groups = match.groups()
                experience.position = groups[0].strip()
                experience.company = groups[1].strip()
                
                if len(groups) >= 3:
                    date_range = groups[2].strip()
                    start_date, end_date = self._parse_date_range(date_range)
                    experience.start_date = start_date
                    experience.end_date = end_date
                
                if len(groups) >= 4:
                    experience.location = groups[3].strip()
                
                break
        
        # If header parsing failed, use spaCy NER as fallback
        if not experience.company and self.nlp:
            doc = self.nlp(header)
            orgs = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
            if orgs:
                experience.company = orgs[0]
                experience.position = header.replace(orgs[0], "").strip()
        
        # Extract bullets, metrics, and technologies from body
        bullets = []
        for line in body_lines:
            clean_line = line.strip().lstrip('•-*').strip()
            if clean_line and len(clean_line) > 10:
                bullets.append(clean_line)
        
        experience.bullets = bullets
        experience.metrics = self.metrics_pattern.findall(chunk)
        experience.technologies = self._extract_technologies_from_text(chunk)
        
        return experience if experience.position or experience.company else None
    
    def _extract_projects(self, text: str) -> List[ProjectEntry]:
        """Extract project entries with structured data."""
        projects = []
        
        # Split into project chunks
        project_chunks = re.split(r'\n\s*\n', text)
        
        for chunk in project_chunks:
            if len(chunk.strip()) < 20:
                continue
            
            project = self._parse_single_project(chunk)
            if project:
                projects.append(project)
        
        return projects
    
    def _parse_single_project(self, chunk: str) -> Optional[ProjectEntry]:
        """Parse a single project entry."""
        lines = chunk.strip().split('\n')
        header = lines[0] if lines else ""
        body_lines = lines[1:] if len(lines) > 1 else []
        
        project = ProjectEntry(raw_text=chunk)
        
        # Parse header for name, URL, dates
        # Patterns like: "ProjectName: Description | URL | Dates"
        header_parts = header.split('|')
        if len(header_parts) >= 1:
            name_part = header_parts[0].strip()
            # Remove common prefixes
            name_part = re.sub(r'^\d+\.\s*', '', name_part)  # Remove "1. "
            if ':' in name_part:
                project.name = name_part.split(':')[0].strip()
                project.description = name_part.split(':', 1)[1].strip()
            else:
                project.name = name_part
        
        # Extract URL
        url_match = self.url_pattern.search(chunk)
        if url_match:
            project.url = url_match.group(0)
        
        # Extract dates from header or body
        if self.nlp:
            doc = self.nlp(header)
            dates = [ent.text for ent in doc.ents if ent.label_ == "DATE"]
            if len(dates) >= 2:
                project.start_date = self._parse_single_date(dates[0])
                project.end_date = self._parse_single_date(dates[1])
            elif len(dates) == 1:
                project.end_date = self._parse_single_date(dates[0])
        
        # Extract bullets and technologies
        bullets = []
        for line in body_lines:
            clean_line = line.strip().lstrip('•-*').strip()
            if clean_line:
                bullets.append(clean_line)
        
        project.bullets = bullets
        project.metrics = self.metrics_pattern.findall(chunk)
        project.technologies = self._extract_technologies_from_text(chunk)
        
        # If no description from header, use first bullet
        if not project.description and bullets:
            project.description = bullets[0]
        
        return project if project.name else None
    
    def _extract_education(self, text: str) -> List[EducationEntry]:
        """Extract education entries."""
        education_entries = []
        
        # Split into education chunks
        edu_chunks = re.split(r'\n\s*\n', text)
        
        for chunk in edu_chunks:
            if len(chunk.strip()) < 15:
                continue
            
            education = self._parse_single_education(chunk)
            if education:
                education_entries.append(education)
        
        return education_entries
    
    def _parse_single_education(self, chunk: str) -> Optional[EducationEntry]:
        """Parse a single education entry."""
        education = EducationEntry(raw_text=chunk)
        
        # Common degree patterns
        degree_patterns = [
            r'(Bachelor|Master|PhD|Doctorate|MBA|BS|MS|BA|MA|M\.S\.|B\.S\.|Ph\.D\.)\s+(?:of\s+)?(?:Science\s+)?(?:in\s+)?([^,\n]+)',
            r'(B\.?A\.?|M\.?A\.?|B\.?S\.?|M\.?S\.?|MBA|PhD)\s+in\s+([^,\n]+)',
            r'(Bachelor|Master)\'?s?\s+(?:Degree\s+)?(?:in\s+)?([^,\n]+)'
        ]
        
        for pattern in degree_patterns:
            match = re.search(pattern, chunk, re.IGNORECASE)
            if match:
                education.degree = f"{match.group(1)} in {match.group(2)}".strip()
                education.field_of_study = match.group(2).strip()
                break
        
        # Extract institution using spaCy NER
        if self.nlp:
            doc = self.nlp(chunk)
            orgs = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
            if orgs:
                education.institution = orgs[0]
        
        # Extract GPA
        gpa_match = re.search(r'GPA[\s:]*(\d+\.?\d*)', chunk, re.IGNORECASE)
        if gpa_match:
            education.gpa = gpa_match.group(1)
        
        # Extract dates
        if self.nlp:
            doc = self.nlp(chunk)
            dates = [ent.text for ent in doc.ents if ent.label_ == "DATE"]
            if len(dates) >= 2:
                education.start_date = self._parse_single_date(dates[0])
                education.end_date = self._parse_single_date(dates[1])
            elif len(dates) == 1:
                education.end_date = self._parse_single_date(dates[0])
        
        return education if education.degree or education.institution else None
    
    def _extract_skills(self, text: str) -> List[SkillCategory]:
        """Extract and categorize skills using fuzzy matching."""
        skill_categories = []
        found_skills = {}
        
        # Split text into potential skill tokens
        tokens = re.split(r'[,\n•;:]', text)
        
        for token in tokens:
            token = token.strip()
            if len(token) < 2 or len(token) > 30:  # Skip very short or very long tokens
                continue
            
            # Skip generic words that aren't skills
            if token.lower() in ['and', 'or', 'with', 'using', 'including', 'such', 'as', 'the', 'a', 'an']:
                continue
            
            # Find best matching category
            best_category = None
            best_score = 0
            matched_skill = None
            
            for category, skills_list in self.master_skills.items():
                # Check if token fuzzy matches any skill in this category
                match = process.extractOne(token, skills_list)
                if match and match[1] > 80:  # 80% similarity threshold
                    if match[1] > best_score:
                        best_score = match[1]
                        best_category = category
                        matched_skill = match[0]  # Use the canonical skill name
            
            if best_category and matched_skill:
                if best_category not in found_skills:
                    found_skills[best_category] = set()
                found_skills[best_category].add(matched_skill)
        
        # Convert to SkillCategory objects
        for category, skills in found_skills.items():
            if skills:
                skill_categories.append(SkillCategory(
                    category=category,
                    skills=sorted(list(skills))  # Sort skills for consistency
                ))
        
        return skill_categories
    
    def _extract_certifications(self, text: str) -> List[CertificationEntry]:
        """Extract certifications using keyword heuristics."""
        certifications = []
        
        if not text.strip():
            return certifications
        
        lines = text.split('\n')
        for line in lines:
            line = line.strip().lstrip('•-*').strip()
            if len(line) < 5:
                continue
            
            # Check if line mentions certification keywords or common cert patterns
            cert_indicators = [
                'certified', 'certificate', 'certification', 'license', 'credential',
                'AWS', 'Google Cloud', 'Microsoft', 'Oracle', 'Cisco', 'CKA', 'Professional'
            ]
            
            # Also check if it contains typical cert formats
            cert_patterns = [
                r'[A-Z]{2,}\s+Certified',  # AWS Certified, etc.
                r'Certified\s+[A-Z]',      # Certified Kubernetes
                r'Professional\s+[A-Z]',   # Professional Cloud
                r'\bCKA\b|\bCKS\b|\bCKAD\b'  # Kubernetes certs
            ]
            
            is_cert = (any(keyword.lower() in line.lower() for keyword in cert_indicators) or
                      any(re.search(pattern, line) for pattern in cert_patterns))
            
            # Skip generic achievement lines that aren't certifications
            achievement_keywords = ['award', 'winner', 'honor', 'dean\'s list', 'top performer']
            if any(keyword.lower() in line.lower() for keyword in achievement_keywords):
                is_cert = False
            
            if is_cert:
                cert = CertificationEntry(name=line)
                
                # Try to extract issuer and date
                parts = re.split(r'\s*[|\-–]\s*', line)
                if len(parts) >= 2:
                    cert.name = parts[0].strip()
                    remaining = ' | '.join(parts[1:])
                    
                    # Look for dates in remaining parts
                    if self.nlp:
                        doc = self.nlp(remaining)
                        dates = [ent.text for ent in doc.ents if ent.label_ == "DATE"]
                        if dates:
                            cert.issue_date = self._parse_single_date(dates[0])
                    
                    # Look for issuer (common certification providers)
                    issuers = ['AWS', 'Amazon Web Services', 'Google', 'Google Cloud', 'Microsoft', 'Oracle', 'Cisco', 'VMware', 'Red Hat', 'CNCF']
                    for issuer in issuers:
                        if issuer.lower() in remaining.lower():
                            cert.issuer = issuer
                            break
                
                certifications.append(cert)
        
        return certifications
    
    def _extract_achievements(self, text: str) -> List[str]:
        """Extract achievements/awards."""
        achievements = []
        
        if not text.strip():
            return achievements
        
        lines = text.split('\n')
        for line in lines:
            line = line.strip().lstrip('•-*').strip()
            if len(line) < 5:
                continue
            
            # Look for achievement indicators
            achievement_indicators = [
                'award', 'winner', 'honor', 'dean\'s list', 'top performer', 'distinguished',
                'scholarship', 'recognition', 'magna cum laude', 'summa cum laude',
                'employee of the', 'best', 'first place', 'finalist'
            ]
            
            # Skip certification lines
            cert_keywords = ['certified', 'certificate', 'certification', 'license', 'credential']
            is_cert = any(keyword.lower() in line.lower() for keyword in cert_keywords)
            
            if not is_cert and any(indicator.lower() in line.lower() for indicator in achievement_indicators):
                achievements.append(line)
        
        # Deduplicate achievements
        achievements = list(dict.fromkeys(achievements))  # Preserves order
        
        return achievements
    
    def _detect_domains(self, text: str) -> List[str]:
        """Detect professional domains based on keywords and skills."""
        detected_domains = []
        text_lower = text.lower()
        
        for domain, keywords in self.domain_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    score += 1
            
            # If enough keywords found, add domain
            if score >= 2:
                detected_domains.append(domain)
        
        return detected_domains
    
    def _extract_technologies_from_text(self, text: str) -> List[str]:
        """Extract technology mentions from text using fuzzy matching."""
        technologies = set()
        
        # Get all skills from master skills database
        all_skills = []
        for skills_list in self.master_skills.values():
            all_skills.extend(skills_list)
        
        # Split text into tokens
        tokens = re.split(r'[,\s\n•;]', text)
        
        for token in tokens:
            token = token.strip('(),')
            if len(token) < 2:
                continue
            
            # Fuzzy match against all skills
            match = process.extractOne(token, all_skills)
            if match and match[1] > 85:  # High threshold for tech extraction
                technologies.add(match[0])
        
        return list(technologies)
    
    def _parse_date_range(self, date_range: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse date range like 'Jan 2020 - Present'."""
        # Split on common separators
        parts = re.split(r'[-–—to]', date_range, maxsplit=1)
        
        start_date = self._parse_single_date(parts[0].strip()) if parts else None
        
        if len(parts) > 1:
            end_part = parts[1].strip()
            if re.search(r'present|current', end_part, re.IGNORECASE):
                end_date = "Present"
            else:
                end_date = self._parse_single_date(end_part)
        else:
            end_date = None
        
        return start_date, end_date
    
    def _parse_single_date(self, date_str: str) -> Optional[str]:
        """Parse a single date string to ISO format."""
        try:
            parsed_date = dateparser.parse(date_str)
            return parsed_date.date().isoformat() if parsed_date else None
        except:
            return None
    
    def _enhance_with_llm(self, text: str, extracted_data: Dict) -> Dict:
        """Use OpenAI o1-mini to enhance extraction (optional)."""
        if not self.openai_api_key:
            logger.warning("OpenAI API key not provided for LLM enhancement")
            return extracted_data
        
        # Skip LLM if confidence is already high (cost optimization)
        current_confidence = self._calculate_preliminary_confidence(extracted_data)
        if current_confidence > 0.8:
            logger.info(f"Skipping LLM enhancement - confidence already high ({current_confidence:.2%})")
            return extracted_data
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_api_key)
            
            # Create a focused prompt for enhancement
            enhancement_prompt = self._create_llm_enhancement_prompt(text, extracted_data)
            
            response = client.chat.completions.create(
                model="o1-mini",  # Using o1-mini as requested
                messages=[
                    {
                        "role": "user",
                        "content": enhancement_prompt
                    }
                ],
                max_completion_tokens=2000  # Fixed parameter name for o1-mini
            )
            
            # Parse LLM response and merge with existing data
            llm_suggestions = self._parse_llm_response(response.choices[0].message.content)
            enhanced_data = self._merge_llm_suggestions(extracted_data, llm_suggestions)
            
            logger.info("Successfully enhanced extraction with LLM")
            return enhanced_data
            
        except Exception as e:
            logger.error(f"LLM enhancement failed: {str(e)}")
            return extracted_data
    
    def _calculate_preliminary_confidence(self, extracted_data: Dict) -> float:
        """Calculate preliminary confidence to decide if LLM enhancement is needed."""
        score = 0.0
        
        # Contact information (30%)
        contact = extracted_data.get('contact')
        if contact:
            if hasattr(contact, 'name') and contact.name:
                score += 0.1
            if hasattr(contact, 'email') and contact.email:
                score += 0.1
            if hasattr(contact, 'phone') and contact.phone:
                score += 0.1
        
        # Experience (40%)
        experience = extracted_data.get('experience', [])
        if experience:
            score += min(0.4, len(experience) * 0.2)
        
        # Skills (20%)
        skills = extracted_data.get('skills', [])
        if skills:
            score += min(0.2, len(skills) * 0.05)
        
        # Education (10%)
        education = extracted_data.get('education', [])
        if education:
            score += min(0.1, len(education) * 0.05)
        
        return score
    
    def _create_llm_enhancement_prompt(self, text: str, extracted_data: Dict) -> str:
        """Create a focused prompt for LLM enhancement."""
        return f"""
You are an expert resume parser. Review the resume text and the extracted data, then provide improvements and missing information.

RESUME TEXT:
{text[:2000]}...  # Truncate to avoid token limits

CURRENT EXTRACTED DATA:
- Contact: {extracted_data.get('contact', {}).dict() if hasattr(extracted_data.get('contact', {}), 'dict') else extracted_data.get('contact', {})}
- Experience: {len(extracted_data.get('experience', []))} entries found
- Projects: {len(extracted_data.get('projects', []))} entries found
- Skills: {len(extracted_data.get('skills', []))} categories found
- Domains: {extracted_data.get('domains', [])}

ENHANCEMENT TASKS:
1. Fix any missing or incorrect contact information (name, email, phone)
2. Identify any missed skills or technologies
3. Suggest additional professional domains based on experience
4. Identify any missed certifications or achievements
5. Improve job titles or company names if they seem incomplete

Respond in JSON format with these fields:
{{
    "contact_fixes": {{"name": "...", "email": "...", "phone": "..."}},
    "missing_skills": ["skill1", "skill2"],
    "additional_domains": ["domain1", "domain2"],
    "missed_certifications": ["cert1", "cert2"],
    "missed_achievements": ["achievement1", "achievement2"],
    "confidence_notes": "explanation of parsing quality"
}}

Only include fields where you found improvements. Keep responses concise.
"""
    
    def _parse_llm_response(self, response_text: str) -> Dict:
        """Parse LLM response into structured suggestions."""
        try:
            import json
            # Try to extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)
            else:
                logger.warning("No valid JSON found in LLM response")
                return {}
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {str(e)}")
            return {}
    
    def _merge_llm_suggestions(self, original_data: Dict, suggestions: Dict) -> Dict:
        """Merge LLM suggestions with original extracted data."""
        enhanced_data = original_data.copy()
        
        # Apply contact fixes
        if "contact_fixes" in suggestions:
            contact = enhanced_data.get('contact')
            if contact and hasattr(contact, '__dict__'):
                for field, value in suggestions["contact_fixes"].items():
                    if value and value.strip():  # Only apply non-empty suggestions
                        setattr(contact, field, value)
        
        # Add missing skills
        if "missing_skills" in suggestions and suggestions["missing_skills"]:
            skills = enhanced_data.get('skills', [])
            # Add to "Additional Skills" category
            additional_category = next((s for s in skills if s.category == "Additional Skills"), None)
            if not additional_category:
                from ..schema import SkillCategory
                additional_category = SkillCategory(category="Additional Skills", skills=[])
                skills.append(additional_category)
            
            for skill in suggestions["missing_skills"]:
                if skill not in additional_category.skills:
                    additional_category.skills.append(skill)
        
        # Add additional domains
        if "additional_domains" in suggestions:
            current_domains = enhanced_data.get('domains', [])
            for domain in suggestions["additional_domains"]:
                if domain not in current_domains:
                    current_domains.append(domain)
            enhanced_data['domains'] = current_domains
        
        # Add missed certifications
        if "missed_certifications" in suggestions:
            current_certs = enhanced_data.get('certifications', [])
            from ..schema import CertificationEntry
            for cert_name in suggestions["missed_certifications"]:
                current_certs.append(CertificationEntry(name=cert_name))
        
        # Add missed achievements
        if "missed_achievements" in suggestions:
            current_achievements = enhanced_data.get('achievements', [])
            for achievement in suggestions["missed_achievements"]:
                if achievement not in current_achievements:
                    current_achievements.append(achievement)
        
        # Add LLM enhancement flag
        enhanced_data['llm_enhanced'] = True
        enhanced_data['llm_notes'] = suggestions.get('confidence_notes', 'Enhanced with LLM')
        
        return enhanced_data

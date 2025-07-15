"""
Enhanced Unified Extractor Module
Processes advanced extraction results including hidden links and metadata.
"""
import logging
import re
from typing import Dict, List, Tuple, Optional, Set, Any
from datetime import datetime
import json

import spacy
import dateparser
import phonenumbers
from thefuzz import process
from email_validator import validate_email, EmailNotValidError

from app.schema import (
    ContactInfo, ExperienceEntry, ProjectEntry, EducationEntry,
    SkillCategory, CertificationEntry
)

logger = logging.getLogger(__name__)


class EnhancedUnifiedExtractor:
    """
    Enhanced extractor that processes advanced extraction results.
    Handles hidden links, metadata, tables, and non-textual elements.
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
            return spacy.load("en_core_web_lg")  # Use larger model for better accuracy
        except OSError:
            logger.warning("spaCy model 'en_core_web_lg' not found. Install with: python -m spacy download en_core_web_lg")
            return None
    
    def _load_master_skills(self) -> Dict[str, List[str]]:
        """Load comprehensive skills database organized by category."""
        return {
            "Programming Languages": [
                "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Rust",
                "PHP", "Ruby", "Swift", "Kotlin", "Scala", "R", "MATLAB", "SQL", "NoSQL",
                "HTML", "CSS", "Bash", "PowerShell", "Perl", "Lua", "Dart", "F#", "Solidity"
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
                "Nagios", "Helm", "Istio", "Service Mesh", "CI/CD"
            ],
            "Databases": [
                "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", "Oracle",
                "SQL Server", "Cassandra", "DynamoDB", "Neo4j", "Elasticsearch",
                "InfluxDB", "CouchDB", "MariaDB", "Amazon RDS", "Azure SQL",
                "Google Cloud SQL", "Firebase", "Supabase", "DuckDB"
            ],
            "AI/ML & Data Science": [
                "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy", "OpenCV",
                "Keras", "XGBoost", "LightGBM", "Hugging Face", "Transformers",
                "BERT", "GPT", "LLM", "Computer Vision", "NLP", "Deep Learning",
                "Machine Learning", "Data Science", "MLflow", "Kubeflow", "MLOps"
            ],
            "Mobile Development": [
                "React Native", "Flutter", "iOS", "Android", "Xamarin", "Ionic",
                "Cordova", "Unity", "Android Studio", "Xcode", "Swift UI", "Jetpack Compose"
            ],
            "Testing & Quality": [
                "Jest", "Pytest", "JUnit", "Selenium", "Cypress", "TestNG", "Mocha",
                "Chai", "Postman", "Newman", "K6", "Unit Testing", "Integration Testing",
                "E2E Testing", "TDD", "BDD", "Automation Testing"
            ],
            "Blockchain & Web3": [
                "Solidity", "Ethereum", "Smart Contracts", "Web3", "Blockchain",
                "DeFi", "NFT", "MetaMask", "Hardhat", "Truffle", "IPFS"
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
            "Product Management": ["product management", "roadmap", "stakeholder", "requirements", "user stories"],
            "Blockchain Development": ["blockchain", "web3", "defi", "smart contracts", "ethereum", "solidity"]
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
    
    def extract_all_enhanced(self, text: str, metadata: Dict[str, Any]) -> Dict:
        """
        Enhanced extraction that processes both text and metadata.
        
        Args:
            text: Extracted text
            metadata: Advanced extraction metadata including links, tables, etc.
            
        Returns:
            Dictionary with all extracted entities including hidden elements
        """
        logger.info(f"Starting enhanced extraction on {len(text)} characters with {len(metadata.get('links', []))} links")
        
        # Stage 1: Process metadata first
        processed_metadata = self._process_metadata(metadata)
        
        # Stage 2: Section Splitting
        sections = self._split_sections(text)
        logger.info(f"Detected sections: {list(sections.keys())}")
        
        # Stage 3: Enhanced Entity Extraction
        results = {
            'contact': self._extract_contact_enhanced(text, processed_metadata),
            'summary': self._extract_summary(sections.get('summary', '')),
            'experience': self._extract_experience_enhanced(sections.get('experience', ''), processed_metadata),
            'projects': self._extract_projects_enhanced(sections.get('projects', ''), processed_metadata),
            'education': self._extract_education_enhanced(sections.get('education', ''), processed_metadata),
            'skills': self._extract_skills_enhanced(sections.get('skills', ''), processed_metadata),
            'certifications': self._extract_certifications_enhanced(sections.get('certifications', '') + '\n' + sections.get('achievements', ''), processed_metadata),
            'achievements': self._extract_achievements_enhanced(sections.get('achievements', '') + '\n' + sections.get('certifications', ''), processed_metadata),
            'domains': self._detect_domains_enhanced(text, processed_metadata),
            'sections_detected': list(sections.keys()),
            'hidden_elements': processed_metadata
        }
        
        # Stage 4: LLM Enhancement (optional)
        if self.use_llm and self.openai_api_key:
            results = self._enhance_with_llm_advanced(text, results, processed_metadata)
        
        return results
    
    def _process_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process and organize metadata from advanced extraction."""
        processed = {
            'links': [],
            'social_profiles': {},
            'tables': [],
            'form_fields': [],
            'hidden_text': [],
            'document_metadata': {}
        }
        
        # Process links
        for link in metadata.get('links', []):
            link_type = link.get('type', 'url')
            if link_type == 'social_media':
                platform = link.get('platform', 'unknown')
                username = link.get('username', '')
                processed['social_profiles'][platform] = {
                    'username': username,
                    'url': link.get('url', ''),
                    'text': link.get('text', '')
                }
            else:
                processed['links'].append(link)
        
        # Process tables
        for table in metadata.get('tables', []):
            table_data = table.get('data', [])
            if table_data:
                processed['tables'].append({
                    'data': table_data,
                    'page': table.get('page', 1),
                    'extracted_info': self._extract_info_from_table(table_data)
                })
        
        # Process form fields
        for field in metadata.get('form_fields', []):
            processed['form_fields'].append({
                'name': field.get('name', ''),
                'value': field.get('value', ''),
                'type': field.get('type', ''),
                'page': field.get('page', 1)
            })
        
        # Process hidden text
        for hidden in metadata.get('hidden_text', []):
            processed['hidden_text'].append({
                'text': hidden.get('text', ''),
                'page': hidden.get('page', 1),
                'source': hidden.get('source', 'unknown')
            })
        
        # Process document metadata
        doc_metadata = metadata.get('metadata', {})
        processed['document_metadata'] = {
            'title': doc_metadata.get('title', ''),
            'author': doc_metadata.get('author', ''),
            'subject': doc_metadata.get('subject', ''),
            'creator': doc_metadata.get('creator', ''),
            'creation_date': doc_metadata.get('creation_date', ''),
            'modification_date': doc_metadata.get('modification_date', '')
        }
        
        return processed
    
    def _extract_contact_enhanced(self, text: str, metadata: Dict[str, Any]) -> ContactInfo:
        """Enhanced contact extraction using both text and metadata."""
        contact = ContactInfo()
        
        # Extract name - look for ALL CAPS name at the beginning
        lines = text.split('\n')
        for line in lines[:3]:  # Check first 3 lines
            line = line.strip()
            if line and line.isupper() and len(line.split()) >= 2:
                # Check if it looks like a name (contains only letters, spaces, and common name characters)
                if re.match(r'^[A-Z\s]+$', line) and len(line.split()) <= 4:
                    contact.name = line.title()  # Convert to title case
                    break
        
        # If no name found in text, try document metadata
        if not contact.name and metadata.get('document_metadata', {}).get('author'):
            contact.name = metadata['document_metadata']['author']
        
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
        
        # Extract phone - look for phone patterns including international
        phone_patterns = [
            r'\+?[0-9]{1,3}[-.\s]?[0-9]{3,}[-.\s]?[0-9]{3,}[-.\s]?[0-9]{3,}',  # International format
            r'\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}',  # US format
            r'[0-9]{10,}',  # 10+ digits
        ]
        
        phone_found = False
        for pattern in phone_patterns:
            phone_matches = re.findall(pattern, text)
            if phone_matches:
                try:
                    phone_str = phone_matches[0]
                    # Try parsing with different country codes
                    for country_code in ["IN", "US", "GB"]:
                        try:
                            parsed = phonenumbers.parse(phone_str, country_code)
                            if phonenumbers.is_valid_number(parsed):
                                contact.phone = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
                                phone_found = True
                                break
                        except:
                            continue
                    
                    if not phone_found:
                        contact.phone = phone_str
                        phone_found = True
                    
                    if phone_found:
                        break
                except:
                    contact.phone = phone_matches[0]
                    phone_found = True
                    break
        
        # Extract LinkedIn from metadata first, then text
        linkedin_profile = metadata.get('social_profiles', {}).get('linkedin')
        if linkedin_profile:
            contact.linkedin = linkedin_profile['url']
        else:
            linkedin_match = self.linkedin_pattern.search(text.lower())
            if linkedin_match:
                contact.linkedin = f"https://linkedin.com/in/{linkedin_match.group(1)}"
        
        # Extract GitHub from metadata first, then text
        github_profile = metadata.get('social_profiles', {}).get('github')
        if github_profile:
            contact.github = github_profile['url']
        else:
            github_match = self.github_pattern.search(text.lower())
            if github_match:
                contact.github = f"https://github.com/{github_match.group(1)}"
        
        # Extract location - look for city, country pattern
        location_pattern = r'([A-Z][a-z]+(?:[\s,]+[A-Z][a-z]+)*),\s*([A-Z][a-z]+)'
        location_match = re.search(location_pattern, text)
        if location_match:
            contact.location = f"{location_match.group(1)}, {location_match.group(2)}"
        
        # Extract website from links
        for link in metadata.get('links', []):
            url = link.get('url', '')
            if url and not any(domain in url.lower() for domain in ['linkedin.com', 'github.com', 'twitter.com', 'facebook.com']):
                contact.website = url
                break
        
        return contact
    
    def _extract_experience_enhanced(self, text: str, metadata: Dict[str, Any]) -> List[ExperienceEntry]:
        """Enhanced experience extraction using tables and metadata."""
        experiences = []
        
        # First try to extract from tables (often contain structured experience data)
        for table in metadata.get('tables', []):
            table_info = table.get('extracted_info', {})
            if table_info.get('type') == 'experience':
                for exp_data in table_info.get('entries', []):
                    experience = ExperienceEntry(
                        position=exp_data.get('position', ''),
                        company=exp_data.get('company', ''),
                        start_date=exp_data.get('start_date', ''),
                        end_date=exp_data.get('end_date', ''),
                        location=exp_data.get('location', ''),
                        raw_text=exp_data.get('raw_text', '')
                    )
                    experiences.append(experience)
        
        # Then extract from text using existing method
        text_experiences = self._extract_experience_from_text(text)
        experiences.extend(text_experiences)
        
        return experiences
    
    def _extract_projects_enhanced(self, text: str, metadata: Dict[str, Any]) -> List[ProjectEntry]:
        """Enhanced project extraction using links and metadata."""
        projects = []
        
        # Extract projects from links (GitHub repositories, portfolio links, etc.)
        for link in metadata.get('links', []):
            url = link.get('url', '')
            if any(domain in url.lower() for domain in ['github.com', 'gitlab.com', 'bitbucket.org']):
                # Extract project info from GitHub/GitLab URLs
                project_info = self._extract_project_from_url(url, link.get('text', ''))
                if project_info:
                    projects.append(project_info)
        
        # Extract from text
        text_projects = self._extract_projects_from_text(text)
        projects.extend(text_projects)
        
        return projects
    
    def _extract_skills_enhanced(self, text: str, metadata: Dict[str, Any]) -> List[SkillCategory]:
        """Enhanced skills extraction using multiple sources."""
        skill_categories = []
        
        # Extract from text
        text_skills = self._extract_skills_from_text(text)
        skill_categories.extend(text_skills)
        
        # Extract from tables
        for table in metadata.get('tables', []):
            table_info = table.get('extracted_info', {})
            if table_info.get('type') == 'skills':
                for skill_data in table_info.get('skills', []):
                    category = skill_data.get('category', 'Additional Skills')
                    skills = skill_data.get('skills', [])
                    
                    # Find existing category or create new one
                    existing_category = next((cat for cat in skill_categories if cat.category == category), None)
                    if existing_category:
                        existing_category.skills.extend(skills)
                    else:
                        skill_categories.append(SkillCategory(category=category, skills=skills))
        
        # Extract from hidden text
        for hidden in metadata.get('hidden_text', []):
            hidden_skills = self._extract_skills_from_text(hidden.get('text', ''))
            for skill_cat in hidden_skills:
                existing_category = next((cat for cat in skill_categories if cat.category == skill_cat.category), None)
                if existing_category:
                    existing_category.skills.extend(skill_cat.skills)
                else:
                    skill_categories.append(skill_cat)
        
        return skill_categories
    
    def _extract_info_from_table(self, table_data: List[List[str]]) -> Dict[str, Any]:
        """Extract structured information from table data."""
        if not table_data:
            return {}
        
        # Analyze table structure to determine type
        headers = table_data[0] if table_data else []
        rows = table_data[1:] if len(table_data) > 1 else []
        
        # Try to identify table type based on headers
        header_text = ' '.join(headers).lower()
        
        if any(keyword in header_text for keyword in ['experience', 'work', 'employment', 'job']):
            return self._extract_experience_from_table(headers, rows)
        elif any(keyword in header_text for keyword in ['skill', 'technology', 'tool']):
            return self._extract_skills_from_table(headers, rows)
        elif any(keyword in header_text for keyword in ['education', 'degree', 'university']):
            return self._extract_education_from_table(headers, rows)
        else:
            return {'type': 'unknown', 'data': table_data}
    
    def _extract_experience_from_table(self, headers: List[str], rows: List[List[str]]) -> Dict[str, Any]:
        """Extract experience data from table."""
        entries = []
        
        for row in rows:
            if len(row) >= 2:
                entry = {
                    'position': row[0] if len(row) > 0 else '',
                    'company': row[1] if len(row) > 1 else '',
                    'start_date': row[2] if len(row) > 2 else '',
                    'end_date': row[3] if len(row) > 3 else '',
                    'location': row[4] if len(row) > 4 else '',
                    'raw_text': ' | '.join(row)
                }
                entries.append(entry)
        
        return {'type': 'experience', 'entries': entries}
    
    def _extract_skills_from_table(self, headers: List[str], rows: List[List[str]]) -> Dict[str, Any]:
        """Extract skills data from table."""
        skills = []
        
        for row in rows:
            if len(row) >= 2:
                skill_data = {
                    'category': row[0] if len(row) > 0 else 'Additional Skills',
                    'skills': [skill.strip() for skill in row[1].split(',') if skill.strip()]
                }
                skills.append(skill_data)
        
        return {'type': 'skills', 'skills': skills}
    
    def _extract_education_from_table(self, headers: List[str], rows: List[List[str]]) -> Dict[str, Any]:
        """Extract education data from table."""
        entries = []
        
        for row in rows:
            if len(row) >= 2:
                entry = {
                    'institution': row[0] if len(row) > 0 else '',
                    'degree': row[1] if len(row) > 1 else '',
                    'field_of_study': row[2] if len(row) > 2 else '',
                    'start_date': row[3] if len(row) > 3 else '',
                    'end_date': row[4] if len(row) > 4 else '',
                    'gpa': row[5] if len(row) > 5 else '',
                    'raw_text': ' | '.join(row)
                }
                entries.append(entry)
        
        return {'type': 'education', 'entries': entries}
    
    def _extract_project_from_url(self, url: str, context: str) -> Optional[ProjectEntry]:
        """Extract project information from GitHub/GitLab URL."""
        try:
            # Parse GitHub/GitLab URL
            if 'github.com' in url:
                parts = url.split('github.com/')
                if len(parts) > 1:
                    repo_path = parts[1].split('/')
                    if len(repo_path) >= 2:
                        username = repo_path[0]
                        repo_name = repo_path[1].split('#')[0]  # Remove fragment
                        
                        return ProjectEntry(
                            name=repo_name.replace('-', ' ').replace('_', ' ').title(),
                            description=f"GitHub repository: {repo_name}",
                            url=url,
                            technologies=[],  # Could be enhanced with repo language detection
                            raw_text=context
                        )
            
            elif 'gitlab.com' in url:
                parts = url.split('gitlab.com/')
                if len(parts) > 1:
                    repo_path = parts[1].split('/')
                    if len(repo_path) >= 2:
                        username = repo_path[0]
                        repo_name = repo_path[1].split('#')[0]
                        
                        return ProjectEntry(
                            name=repo_name.replace('-', ' ').replace('_', ' ').title(),
                            description=f"GitLab repository: {repo_name}",
                            url=url,
                            technologies=[],
                            raw_text=context
                        )
            
        except Exception as e:
            logger.warning(f"Failed to extract project from URL {url}: {e}")
        
        return None
    
    # Include all the existing extraction methods with enhanced versions
    def _extract_experience_from_text(self, text: str) -> List[ExperienceEntry]:
        """Extract experience from text using existing logic."""
        # This would contain the existing experience extraction logic
        # For brevity, I'm not duplicating the full implementation
        return []
    
    def _extract_projects_from_text(self, text: str) -> List[ProjectEntry]:
        """Extract projects from text using existing logic."""
        # This would contain the existing project extraction logic
        return []
    
    def _extract_skills_from_text(self, text: str) -> List[SkillCategory]:
        """Extract skills from text using existing logic."""
        # This would contain the existing skills extraction logic
        return []
    
    def _extract_summary(self, text: str) -> Optional[str]:
        """Extract professional summary."""
        if not text.strip():
            return None
        
        # Clean up the text
        summary = text.strip()
        
        # Remove common header words if they appear at start
        summary = re.sub(r'^(professional\s+summary|summary|objective|profile)[\s:]*', '', summary, flags=re.IGNORECASE)
        
        return summary.strip() if summary.strip() else None
    
    def _extract_education_enhanced(self, text: str, metadata: Dict[str, Any]) -> List[EducationEntry]:
        """Enhanced education extraction."""
        education_entries = []
        
        # Extract from tables first
        for table in metadata.get('tables', []):
            table_info = table.get('extracted_info', {})
            if table_info.get('type') == 'education':
                for edu_data in table_info.get('entries', []):
                    education = EducationEntry(
                        institution=edu_data.get('institution', ''),
                        degree=edu_data.get('degree', ''),
                        field_of_study=edu_data.get('field_of_study', ''),
                        start_date=edu_data.get('start_date', ''),
                        end_date=edu_data.get('end_date', ''),
                        gpa=edu_data.get('gpa', ''),
                        raw_text=edu_data.get('raw_text', '')
                    )
                    education_entries.append(education)
        
        # Extract from text
        text_education = self._extract_education_from_text(text)
        education_entries.extend(text_education)
        
        return education_entries
    
    def _extract_education_from_text(self, text: str) -> List[EducationEntry]:
        """Extract education from text using existing logic."""
        # This would contain the existing education extraction logic
        return []
    
    def _extract_certifications_enhanced(self, text: str, metadata: Dict[str, Any]) -> List[CertificationEntry]:
        """Enhanced certification extraction."""
        certifications = []
        
        # Extract from text
        text_certs = self._extract_certifications_from_text(text)
        certifications.extend(text_certs)
        
        # Extract from form fields (sometimes certifications are in form fields)
        for field in metadata.get('form_fields', []):
            field_name = field.get('name', '').lower()
            field_value = field.get('value', '')
            
            if any(keyword in field_name for keyword in ['certification', 'certificate', 'license']):
                if field_value:
                    certifications.append(CertificationEntry(name=field_value))
        
        return certifications
    
    def _extract_certifications_from_text(self, text: str) -> List[CertificationEntry]:
        """Extract certifications from text using existing logic."""
        # This would contain the existing certification extraction logic
        return []
    
    def _extract_achievements_enhanced(self, text: str, metadata: Dict[str, Any]) -> List[str]:
        """Enhanced achievements extraction."""
        achievements = []
        
        # Extract from text
        text_achievements = self._extract_achievements_from_text(text)
        achievements.extend(text_achievements)
        
        # Extract from hidden text
        for hidden in metadata.get('hidden_text', []):
            hidden_achievements = self._extract_achievements_from_text(hidden.get('text', ''))
            achievements.extend(hidden_achievements)
        
        return list(set(achievements))  # Remove duplicates
    
    def _extract_achievements_from_text(self, text: str) -> List[str]:
        """Extract achievements from text using existing logic."""
        # This would contain the existing achievements extraction logic
        return []
    
    def _detect_domains_enhanced(self, text: str, metadata: Dict[str, Any]) -> List[str]:
        """Enhanced domain detection using multiple sources."""
        domains = []
        
        # Detect from text
        text_domains = self._detect_domains_from_text(text)
        domains.extend(text_domains)
        
        # Detect from links and social profiles
        for link in metadata.get('links', []):
            url = link.get('url', '').lower()
            if 'github.com' in url:
                domains.append('Software Development')
            elif 'linkedin.com' in url:
                domains.append('Professional Networking')
            elif 'portfolio' in url or 'personal' in url:
                domains.append('Personal Branding')
        
        # Detect from skills
        for table in metadata.get('tables', []):
            table_info = table.get('extracted_info', {})
            if table_info.get('type') == 'skills':
                for skill_data in table_info.get('skills', []):
                    skills_text = ' '.join(skill_data.get('skills', []))
                    skill_domains = self._detect_domains_from_text(skills_text)
                    domains.extend(skill_domains)
        
        return list(set(domains))  # Remove duplicates
    
    def _detect_domains_from_text(self, text: str) -> List[str]:
        """Detect domains from text using existing logic."""
        # This would contain the existing domain detection logic
        return []
    
    def _split_sections(self, text: str) -> Dict[str, str]:
        """Split resume text into logical sections."""
        # This would contain the existing section splitting logic
        return {}
    
    def _enhance_with_llm_advanced(self, text: str, results: Dict, metadata: Dict[str, Any]) -> Dict:
        """Enhanced LLM processing with metadata context."""
        # This would contain enhanced LLM processing logic
        return results 
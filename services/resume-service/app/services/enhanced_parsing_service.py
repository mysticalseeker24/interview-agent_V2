"""
Enhanced Resume Parsing Service with Domain-Aware Classification.

This production-ready parser combines:
- Multiple PDF extraction methods (pypdf + Tika fallback)
- Advanced section detection and entity extraction
- Domain-aware skill classification across 11 specialized domains
- Fuzzy matching for skill recognition
- Comprehensive confidence scoring
- Support for modern resume templates (Deedy, RenderCV, etc.)
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import dateparser
import spacy
from thefuzz import process
from tika import parser as tika_parser

from app.core.config import get_settings
from app.schemas.resume import (
    ResumeParseResult, ContactInfo, ExperienceEntry,
    ProjectEntry, EducationEntry, SkillCategory,
    CertificationEntry, LanguageEntry
)

logger = logging.getLogger(__name__)
settings = get_settings()


# Section header patterns for modern resume templates
SECTION_HEADERS = {
    "summary": r'(professional summary|summary|profile|objective|career objective)',
    "contact": r'(contact|contact information|personal information)',
    "experience": r'(experience|work history|professional experience|employment|career history)',
    "projects": r'(projects|personal projects|notable projects|key projects)',
    "education": r'(education|academic background|educational background)',
    "skills": r'(skills|technical skills|core competencies|technologies|expertise)',
    "certifications": r'(certifications|licenses|credentials)',
    "achievements": r'(achievements|awards|honors|recognition)',
    "publications": r'(publications|papers|research|articles)',
    "societies": r'(societies|organizations|memberships|affiliations)',
    "service": r'(community service|volunteer experience|volunteering)',
    "languages": r'(languages|language proficiency)'
}


class DomainAwareResumeParser:
    """Enhanced resume parser with domain classification capabilities."""
    
    def __init__(self):
        """Initialize the parser with domain taxonomy and NLP models."""
        self.nlp = None
        self.domain_taxonomy = {}
        self.skill_to_domains: Dict[str, Set[str]] = {}
        self.master_skills: List[str] = []
        
        self._load_spacy_model()
        self._load_domain_taxonomy()
        self._build_inverse_skill_map()
    
    def _load_spacy_model(self):
        """Load spaCy model for NLP processing."""
        try:
            logger.info(f"Loading spaCy model: {settings.SPACY_MODEL}")
            self.nlp = spacy.load(settings.SPACY_MODEL)
            logger.info("spaCy model loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load spaCy model: {e}. NER features may be limited.")
            self.nlp = None
    
    def _load_domain_taxonomy(self):
        """Load domain taxonomy from configuration file."""
        try:
            config_path = Path(__file__).parent.parent.parent / "config" / "domain_taxonomy.json"
            with open(config_path, 'r', encoding='utf-8') as f:
                self.domain_taxonomy = json.load(f)
            
            # Build master skills list for fuzzy matching
            self.master_skills = []
            for domain_info in self.domain_taxonomy.values():
                self.master_skills.extend(domain_info["skills"])
            
            logger.info(f"Loaded domain taxonomy with {len(self.domain_taxonomy)} domains")
            logger.info(f"Master skills list contains {len(self.master_skills)} skills")
            
        except Exception as e:
            logger.error(f"Failed to load domain taxonomy: {e}")
            self.domain_taxonomy = {}
            self.master_skills = []
    
    def _build_inverse_skill_map(self):
        """Build inverse mapping from skills to domains for fast lookup."""
        self.skill_to_domains = {}
        for domain, info in self.domain_taxonomy.items():
            for skill in info["skills"]:
                skill_lower = skill.lower()
                if skill_lower not in self.skill_to_domains:
                    self.skill_to_domains[skill_lower] = set()
                self.skill_to_domains[skill_lower].add(domain)
        
        logger.info(f"Built inverse skill map with {len(self.skill_to_domains)} unique skills")
    
    def extract_text_with_fallback(self, file_path: str) -> str:
        """
        Extract text using pypdf first, fall back to Tika for better layout handling.
        """
        text = ""
        
        # Try pypdf first (faster)
        try:
            import pypdf
            with open(file_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\\n\\n"
            
            # Check if we got meaningful content
            if len(text.strip()) < 200:
                raise ValueError("Insufficient text extracted, trying Tika")
                
            logger.info(f"Successfully extracted {len(text)} characters using pypdf")
            return text.strip()
            
        except Exception as e:
            logger.warning(f"pypdf extraction failed: {e}. Falling back to Tika")
            
            # Fallback to Tika for better layout handling
            try:
                result = tika_parser.from_file(file_path)
                text = result.get("content", "") if result else ""
                logger.info(f"Successfully extracted {len(text)} characters using Tika")
                return text.strip()
            except Exception as e2:
                logger.error(f"Both pypdf and Tika extraction failed: {e2}")
                return ""
    
    def split_sections(self, text: str) -> Dict[str, str]:
        """
        Split resume text into logical sections using regex patterns.
        """
        sections = {}
        
        # Create a combined regex pattern for all section headers
        all_patterns = '|'.join(pattern for pattern in SECTION_HEADERS.values())
        header_regex = f'(?im)^\\s*({all_patterns})\\s*$'
        
        try:
            # Split text by section headers
            parts = re.split(header_regex, text)
            
            # Process the split parts
            i = 1
            while i < len(parts):
                if i + 1 < len(parts):
                    header = parts[i].strip().lower()
                    content = parts[i + 1].strip()
                    
                    # Map header to section key
                    for section_key, pattern in SECTION_HEADERS.items():
                        if re.search(pattern, header, flags=re.IGNORECASE):
                            sections[section_key] = content
                            break
                i += 2
                
        except Exception as e:
            logger.warning(f"Error in section splitting: {e}. Using simple fallback.")
            # Simple fallback: just look for skill section
            skills_match = re.search(r'(?i)(skills|technical skills)[:\s]*\n(.*?)(?=\n[A-Z]|$)', text, re.DOTALL)
            if skills_match:
                sections["skills"] = skills_match.group(2).strip()
        
        logger.info(f"Detected sections: {list(sections.keys())}")
        return sections
    
    def extract_contact_info(self, text: str) -> ContactInfo:
        """Extract contact information from resume text."""
        contact = ContactInfo()
        
        try:
            # Extract email
            email_pattern = r'\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b'
            emails = re.findall(email_pattern, text)
            if emails:
                contact.email = emails[0]
            
            # Extract phone number
            phone_patterns = [
                r'\\+?1?[-\\s]?\\(?\\d{3}\\)?[-\\s]?\\d{3}[-\\s]?\\d{4}',
                r'\\+?\\d{1,3}[-\\s]?\\(?\\d{2,4}\\)?[-\\s]?\\d{3,4}[-\\s]?\\d{3,4}'
            ]
            for pattern in phone_patterns:
                match = re.search(pattern, text)
                if match:
                    contact.phone = match.group(0).strip()
                    break
            
            # Extract LinkedIn
            linkedin_pattern = r'(?:linkedin\\.com/in/|linkedin\\.com/pub/)([a-zA-Z0-9-]+)'
            linkedin_match = re.search(linkedin_pattern, text.lower())
            if linkedin_match:
                contact.linkedin = f"https://linkedin.com/in/{linkedin_match.group(1)}"
            
            # Extract GitHub
            github_pattern = r'(?:github\\.com/)([a-zA-Z0-9-]+)'
            github_match = re.search(github_pattern, text.lower())
            if github_match:
                contact.github = f"https://github.com/{github_match.group(1)}"
        
        except Exception as e:
            logger.warning(f"Error extracting contact info: {e}")
        
        # Extract name (using spaCy if available)
        try:
            if self.nlp:
                # Process first few lines where name is usually located
                lines = text.split('\\n')[:5]
                sample_text = ' '.join(lines)
                doc = self.nlp(sample_text)
                
                for ent in doc.ents:
                    if ent.label_ == "PERSON" and len(ent.text.split()) >= 2:
                        # Basic validation for name
                        name_parts = ent.text.strip().split()
                        if len(name_parts) >= 2 and all(part.isalpha() for part in name_parts[:2]):
                            contact.name = ent.text.strip()
                            break
        except Exception as e:
            logger.warning(f"Error extracting name: {e}")
        
        return contact
    
    def parse_experience(self, block: str) -> List[ExperienceEntry]:
        """Parse work experience entries from text block."""
        entries = []
        
        # Split by double newlines or clear separators
        chunks = re.split(r'\\n{2,}|(?=\\n[A-Z][^\\n]*(?:at|@)[^\\n]*)', block)
        
        for chunk in chunks:
            if len(chunk.strip()) < 20:  # Skip very short chunks
                continue
            
            entry = ExperienceEntry()
            lines = chunk.strip().split('\\n')
            
            # Try to parse the header line (position @ company | dates)
            header_line = lines[0] if lines else ""
            
            # Pattern: "Position at Company (Date - Date)" or "Position | Company | Date - Date"
            patterns = [
                r'(.+?)\\s+@\\s+(.+?)\\s+\\(([^–]+)–([^)]+)\\)',
                r'(.+?)\\s+at\\s+(.+?)\\s+\\(([^–]+)–([^)]+)\\)',
                r'(.+?)\\s*\\|\\s*(.+?)\\s*\\|\\s*([^–]+)–(.+)',
                r'(.+?)\\s*[-–]\\s*(.+?)\\s*\\|\\s*([^–]+)–(.+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, header_line)
                if match:
                    entry.position = match.group(1).strip()
                    entry.company = match.group(2).strip()
                    entry.start_date = self._parse_date(match.group(3).strip())
                    entry.end_date = self._parse_date(match.group(4).strip())
                    break
            
            # Extract description from remaining lines
            if len(lines) > 1:
                entry.description = '\\n'.join(lines[1:]).strip()
            
            # Extract technologies mentioned in description
            entry.technologies = self._extract_technologies_from_text(chunk)
            
            if entry.position or entry.company:  # Only add if we extracted meaningful data
                entries.append(entry)
        
        return entries
    
    def parse_education(self, block: str) -> List[EducationEntry]:
        """Parse education entries from text block."""
        entries = []
        
        # Split by double newlines
        chunks = re.split(r'\\n{2,}', block)
        
        for chunk in chunks:
            if len(chunk.strip()) < 10:
                continue
            
            entry = EducationEntry()
            lines = chunk.strip().split('\\n')
            
            # Try to extract degree and institution
            for line in lines:
                # Pattern: "Degree in Field, Institution, Year"
                if re.search(r'(bachelor|master|phd|doctorate|mba|bs|ms|ba|ma)', line, re.IGNORECASE):
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 2:
                        entry.degree = parts[0]
                        entry.institution = parts[1]
                        if len(parts) >= 3:
                            entry.end_date = self._parse_date(parts[2])
                    break
            
            if entry.degree or entry.institution:
                entries.append(entry)
        
        return entries
    
    def parse_skills_with_domains(self, block: str) -> Tuple[List[SkillCategory], Set[str]]:
        """
        Parse skills and classify them by domain using fuzzy matching.
        Skills that belong to multiple domains will appear under combined domain categories.
        """
        # Split text into potential skill tokens
        raw_tokens = re.split(r'[\\n,•;]', block)
        found_skills = {}
        
        for token in raw_tokens:
            token = token.strip()
            if len(token) < 2:
                continue
            
            # Fuzzy match against master skills list
            if self.master_skills:
                match, score = process.extractOne(token, self.skill_to_domains.keys())
                if score > 85:  # High confidence threshold
                    # Get all domains this skill belongs to
                    domains = self.skill_to_domains[match.lower()]
                    domain_tuple = tuple(sorted(domains))
                    
                    if domain_tuple not in found_skills:
                        found_skills[domain_tuple] = []
                    found_skills[domain_tuple].append(match)
        
        # Build SkillCategory per domain-set
        categories = []
        detected_domains = set()
        
        for domain_tuple, skills in found_skills.items():
            # If a skill belongs to multiple domains, show them combined
            category_name = " & ".join(domain_tuple)
            categories.append(SkillCategory(
                category=category_name,
                skills=sorted(set(skills))
            ))
            detected_domains.update(domain_tuple)
        
        return categories, detected_domains
    
    def detect_domains(self, raw_text: str, entries: List[ExperienceEntry]) -> List[str]:
        """
        Look for keywords in raw text and in each experience description
        to see which domains are actively demonstrated.
        """
        hit_domains: Set[str] = set()
        text_lower = raw_text.lower()
        
        # Global keyword scan
        for domain, info in self.domain_taxonomy.items():
            for kw in info["keywords"]:
                if kw.lower() in text_lower:
                    hit_domains.add(domain)
                    break
        
        # Per-entry tech scan
        for entry in entries:
            desc = (entry.description or "").lower()
            for domain, info in self.domain_taxonomy.items():
                for tech in info["skills"]:
                    if tech.lower() in desc:
                        hit_domains.add(domain)
                        break
        
        return sorted(hit_domains)
    
    def detect_domains_from_content(self, text: str, experience: List[ExperienceEntry]) -> Dict[str, float]:
        """
        Detect domains from full text content and experience descriptions.
        Returns domain confidence scores.
        """
        domain_scores = {}
        text_lower = text.lower()
        
        for domain, info in self.domain_taxonomy.items():
            score = 0.0
            keyword_hits = 0
            skill_hits = 0
            
            # Check for domain keywords in full text
            for keyword in info["keywords"]:
                if keyword.lower() in text_lower:
                    keyword_hits += 1
                    score += 0.5
            
            # Check for domain skills in full text
            for skill in info["skills"]:
                if skill.lower() in text_lower:
                    skill_hits += 1
                    score += 1.0
            
            # Check experience descriptions for domain-specific content
            for exp in experience:
                if exp.description:
                    exp_text = exp.description.lower()
                    for keyword in info["keywords"]:
                        if keyword.lower() in exp_text:
                            score += 0.3
                    for skill in info["skills"]:
                        if skill.lower() in exp_text:
                            score += 0.5
            
            # Normalize score (simple approach)
            max_possible = len(info["keywords"]) * 0.5 + len(info["skills"]) * 1.0
            if max_possible > 0:
                normalized_score = min(score / max_possible, 1.0)
                if normalized_score > 0.1:  # Only include domains with meaningful presence
                    domain_scores[domain] = round(normalized_score, 2)
        
        return domain_scores
    
    def parse_projects(self, block: str) -> List[ProjectEntry]:
        """Parse project entries from text block."""
        projects = []
        
        # Split by double newlines or project markers
        chunks = re.split(r'\\n{2,}|(?=\\n[•\\-])', block)
        
        for chunk in chunks:
            chunk = chunk.strip()
            if len(chunk) < 15:
                continue
            
            project = ProjectEntry()
            lines = chunk.split('\\n')
            
            # First line is usually project name
            project.name = lines[0].strip('•\\-— ').strip()
            
            # Remaining lines are description
            if len(lines) > 1:
                project.description = '\\n'.join(lines[1:]).strip()
            
            # Extract technologies
            project.technologies = self._extract_technologies_from_text(chunk)
            
            # Try to extract URL (for modern templates like Deedy)
            url_match = re.search(r'(https?://[^\\s]+)', chunk)
            if url_match:
                project.url = url_match.group(1)
            
            projects.append(project)
        
        return projects
    
    def parse_certifications(self, block: str) -> List[CertificationEntry]:
        """Parse certification entries."""
        certifications = []
        
        for line in block.split('\\n'):
            line = line.strip('•\\-— ').strip()
            if len(line) > 5:
                cert = CertificationEntry(name=line)
                
                # Try to extract issuer and date
                parts = line.split(' - ')
                if len(parts) >= 2:
                    cert.name = parts[0].strip()
                    remaining = ' - '.join(parts[1:])
                    
                    # Look for date patterns
                    date_match = re.search(r'\\b(\\d{4}|\\w+\\s+\\d{4})\\b', remaining)
                    if date_match:
                        cert.issue_date = self._parse_date(date_match.group(1))
                
                certifications.append(cert)
        
        return certifications
    
    def parse_simple_list(self, block: str) -> List[str]:
        """Parse simple list items (awards, publications, etc.)."""
        items = []
        for line in block.split('\\n'):
            line = line.strip('•\\-— ').strip()
            if len(line) > 3:
                items.append(line)
        return items
    
    def _extract_technologies_from_text(self, text: str) -> List[str]:
        """Extract technology names from text using fuzzy matching."""
        technologies = []
        
        if not self.master_skills:
            return technologies
        
        # Split text into potential technology tokens
        words = re.findall(r'\\b[A-Za-z\\+#\\.\\-]{2,}\\b', text)
        
        for word in words:
            if len(word) < 2:
                continue
            
            # Fuzzy match against master skills
            match, score = process.extractOne(word, self.master_skills)
            if score > 75:  # Lower threshold for technology extraction
                technologies.append(match)
        
        return list(set(technologies))  # Remove duplicates
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string into standardized format."""
        if not date_str or date_str.lower() in ['present', 'current', 'now']:
            return None
        
        try:
            parsed_date = dateparser.parse(date_str)
            return parsed_date.date().isoformat() if parsed_date else None
        except Exception:
            return None
    
    def compute_total_experience(self, experiences: List[ExperienceEntry]) -> Optional[float]:
        """Compute total years of experience from experience entries."""
        total_days = 0
        
        for exp in experiences:
            start_date = dateparser.parse(exp.start_date) if exp.start_date else None
            end_date = dateparser.parse(exp.end_date) if exp.end_date else dateparser.parse("today")
            
            if start_date and end_date:
                days = (end_date - start_date).days
                total_days += max(0, days)
        
        return round(total_days / 365.25, 1) if total_days > 0 else None
    
    def compute_parsing_confidence(self, result: ResumeParseResult) -> float:
        """Compute overall parsing confidence score."""
        score = 0.0
        
        # Contact information completeness
        if result.contact_info.name:
            score += 0.15
        if result.contact_info.email:
            score += 0.15
        if result.contact_info.phone:
            score += 0.1
        
        # Content completeness
        score += min(len(result.skills) * 0.1, 0.2)  # Up to 0.2 for skills
        score += min(len(result.experience) * 0.1, 0.3)  # Up to 0.3 for experience
        score += min(len(result.education) * 0.1, 0.15)  # Up to 0.15 for education
        score += min(len(result.projects) * 0.05, 0.1)  # Up to 0.1 for projects
        
        # Domain detection bonus
        if result.domains_supported:
            score += min(len(result.domains_supported) * 0.02, 0.1)
        
        return round(min(score, 1.0), 2)
    
    def parse_resume(self, file_path: str, file_type: str = "pdf") -> ResumeParseResult:
        """
        Main parsing method that orchestrates the entire parsing process.
        """
        logger.info(f"Starting enhanced resume parsing for {file_path}")
        
        try:
            # Extract text
            if file_type.lower() == "pdf":
                raw_text = self.extract_text_with_fallback(file_path)
            else:
                # Handle other file types (DOCX, TXT)
                raw_text = self._extract_text_fallback(file_path, file_type)
            
            if not raw_text or len(raw_text) < 50:
                logger.warning("Insufficient text extracted from resume")
                return ResumeParseResult(raw_text_length=len(raw_text))
            
            # Split into sections
            sections = self.split_sections(raw_text)
            
            # Extract contact information and summary
            contact_info = self.extract_contact_info(raw_text)
            summary = sections.get("summary", "")
            
            # Parse main sections
            experience = self.parse_experience(sections.get("experience", ""))
            education = self.parse_education(sections.get("education", ""))
            projects = self.parse_projects(sections.get("projects", ""))
            
            # Parse skills with domain classification
            skills, skill_domains = self.parse_skills_with_domains(sections.get("skills", ""))
            
            # Parse other sections
            certifications = self.parse_certifications(sections.get("certifications", ""))
            awards = self.parse_simple_list(sections.get("achievements", ""))
            publications = self.parse_simple_list(sections.get("publications", ""))
            volunteer = self.parse_simple_list(sections.get("service", ""))
            
            # Compute total experience
            total_experience = self.compute_total_experience(experience)
            
            # Domain detection using the new method
            domains = self.detect_domains(raw_text, experience)
            domain_confidence = self.detect_domains_from_content(raw_text, experience)
            
            # Create result
            result = ResumeParseResult(
                contact_info=contact_info,
                summary=summary if summary else None,
                skills=skills,
                experience=experience,
                education=education,
                projects=projects,
                certifications=certifications,
                awards=awards,
                publications=publications,
                volunteer_experience=volunteer,
                total_experience_years=total_experience,
                domains_supported=domains,
                domain_confidence=domain_confidence,
                sections_found=list(sections.keys()),
                raw_text_length=len(raw_text)
            )
            
            # Compute final confidence score
            result.parsing_confidence = self.compute_parsing_confidence(result)
            
            logger.info(f"Parsing completed successfully. Confidence: {result.parsing_confidence}")
            logger.info(f"Detected domains: {result.domains_supported}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error during resume parsing: {str(e)}")
            return ResumeParseResult(
                raw_text_length=0,
                parsing_confidence=0.0
            )
    
    def parse_resume_from_text(self, text: str) -> ResumeParseResult:
        """
        Parse resume from text string (for legacy compatibility).
        """
        try:
            sections = self.split_sections(text)
            contact_info = self.extract_contact_info(text)
            
            experience = self.parse_experience(sections.get("experience", ""))
            skills, skill_domains = self.parse_skills_with_domains(sections.get("skills", ""))
            education = self.parse_education(sections.get("education", ""))
            projects = self.parse_projects(sections.get("projects", ""))
            certifications = self.parse_certifications(sections.get("certifications", ""))
            
            # Use the new domain detection method
            domains = self.detect_domains(text, experience)
            domain_confidence = self.detect_domains_from_content(text, experience)
            
            result = ResumeParseResult(
                contact_info=contact_info,
                skills=skills,
                experience=experience,
                education=education,
                projects=projects,
                certifications=certifications,
                total_experience_years=self.compute_total_experience(experience),
                domains_supported=domains,
                domain_confidence=domain_confidence,
                sections_found=list(sections.keys()),
                raw_text_length=len(text)
            )
            
            result.parsing_confidence = self.compute_parsing_confidence(result)
            return result
            
        except Exception as e:
            logger.error(f"Error in text parsing: {str(e)}")
            return ResumeParseResult(raw_text_length=len(text))
        """Fallback text extraction for non-PDF files."""
        text = ""
        
        try:
            if file_type.lower() in ["docx", "doc"]:
                from docx import Document
                doc = Document(file_path)
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\\n"
            elif file_type.lower() == "txt":
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
        except Exception as e:
            logger.error(f"Error extracting text from {file_type} file: {e}")
        
        return text.strip()


# Legacy wrapper for backward compatibility
class ResumeParsingService(DomainAwareResumeParser):
    """Legacy wrapper maintaining backward compatibility."""
    
    def __init__(self):
        super().__init__()
        logger.info("Initialized enhanced domain-aware resume parsing service")
    
    def parse_resume(self, text: str) -> ResumeParseResult:
        """
        Legacy method that accepts text directly.
        For file-based parsing, use parse_resume_from_file.
        """
        # Create a temporary text processing pipeline
        try:
            sections = self.split_sections(text)
            contact_info = self.extract_contact_info(text)
            
            experience = self.parse_experience(sections.get("experience", ""))
            skills, skill_domains = self.parse_skills_with_domains(sections.get("skills", ""))
            education = self.parse_education(sections.get("education", ""))
            projects = self.parse_projects(sections.get("projects", ""))
            certifications = self.parse_certifications(sections.get("certifications", ""))
            
            # Use the new domain detection method
            domains = self.detect_domains(text, experience)
            domain_confidence = self.detect_domains_from_content(text, experience)
            
            result = ResumeParseResult(
                contact_info=contact_info,
                skills=skills,
                experience=experience,
                education=education,
                projects=projects,
                certifications=certifications,
                total_experience_years=self.compute_total_experience(experience),
                domains_supported=domains,
                domain_confidence=domain_confidence,
                sections_found=list(sections.keys()),
                raw_text_length=len(text)
            )
            
            result.parsing_confidence = self.compute_parsing_confidence(result)
            return result
            
        except Exception as e:
            logger.error(f"Error in legacy parsing method: {str(e)}")
            return ResumeParseResult(raw_text_length=len(text))
    
    def parse_resume_from_file(self, file_path: str, file_type: str = "pdf") -> ResumeParseResult:
        """New method for file-based parsing with full feature support."""
        return super().parse_resume(file_path, file_type)

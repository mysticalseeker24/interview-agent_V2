"""
Stage 3: JSON Formatter
Marshals extracted entities into structured JSON schema.
"""
import logging
from typing import Dict, Any
from datetime import datetime

from app.schema import ResumeJSON, ContactInfo, ExperienceEntry, ProjectEntry, EducationEntry, SkillCategory, CertificationEntry

logger = logging.getLogger(__name__)


class JSONFormatter:
    """
    Formats extracted entities into the unified ResumeJSON schema.
    Handles validation, normalization, and confidence scoring.
    """
    
    def format_to_json(self, extracted_data: Dict[str, Any], raw_text_length: int, 
                      extraction_method: str = "pypdf") -> ResumeJSON:
        """
        Convert extracted data to structured JSON format.
        
        Args:
            extracted_data: Output from UnifiedExtractor
            raw_text_length: Length of original text
            extraction_method: Method used for text extraction
            
        Returns:
            ResumeJSON object with all structured data
        """
        logger.info("Formatting extracted data to JSON schema")
        
        # Create ResumeJSON object
        resume_json = ResumeJSON(
            raw_text_length=raw_text_length,
            text_extraction_method=extraction_method,
            extraction_timestamp=datetime.now()
        )
        
        # Map extracted data to schema
        resume_json.contact = self._format_contact(extracted_data.get('contact'))
        resume_json.summary = extracted_data.get('summary')
        resume_json.experience = self._format_experience(extracted_data.get('experience', []))
        resume_json.projects = self._format_projects(extracted_data.get('projects', []))
        resume_json.education = self._format_education(extracted_data.get('education', []))
        resume_json.skills = self._format_skills(extracted_data.get('skills', []))
        resume_json.certifications = self._format_certifications(extracted_data.get('certifications', []))
        resume_json.achievements = extracted_data.get('achievements', [])
        resume_json.domains = extracted_data.get('domains', [])
        resume_json.sections_detected = extracted_data.get('sections_detected', [])
        
        # Calculate confidence score
        resume_json.parsing_confidence = self._calculate_confidence(resume_json)
        
        # Validate and clean data
        resume_json = self._validate_and_clean(resume_json)
        
        logger.info(f"JSON formatting complete. Confidence: {resume_json.parsing_confidence:.2%}")
        return resume_json
    
    def format_to_json_enhanced(self, extracted_data: Dict[str, Any], raw_text_length: int, 
                               extraction_method: str = "pypdf", metadata: Dict[str, Any] = None) -> ResumeJSON:
        """
        Enhanced JSON formatting with metadata support.
        
        Args:
            extracted_data: Dictionary with extracted entities
            raw_text_length: Length of original text
            extraction_method: Method used for text extraction
            metadata: Advanced extraction metadata
            
        Returns:
            ResumeJSON object with enhanced structured data
        """
        logger.info("Formatting extracted data to enhanced JSON schema")
        
        # Create ResumeJSON object
        resume_json = ResumeJSON(
            raw_text_length=raw_text_length,
            text_extraction_method=extraction_method,
            extraction_timestamp=datetime.now()
        )
        
        # Map extracted data to schema with enhanced processing
        resume_json.contact = self._format_contact_enhanced(extracted_data.get('contact'), metadata or {})
        resume_json.summary = extracted_data.get('summary')
        resume_json.experience = self._format_experience(extracted_data.get('experience', []))
        resume_json.projects = self._format_projects_enhanced(extracted_data.get('projects', []), metadata or {})
        resume_json.education = self._format_education(extracted_data.get('education', []))
        resume_json.skills = self._format_skills_enhanced(extracted_data.get('skills', []), metadata or {})
        resume_json.certifications = self._format_certifications(extracted_data.get('certifications', []))
        resume_json.achievements = extracted_data.get('achievements', [])
        resume_json.domains = extracted_data.get('domains', [])
        resume_json.sections_detected = extracted_data.get('sections_detected', [])
        resume_json.llm_enhanced = extracted_data.get('llm_enhanced', False)
        
        # Calculate enhanced confidence score
        resume_json.parsing_confidence = self._calculate_enhanced_confidence(resume_json, metadata or {})
        
        # Validate and clean data with enhanced validation
        resume_json = self._validate_and_clean_enhanced(resume_json, metadata or {})
        
        logger.info(f"Enhanced JSON formatting complete. Confidence: {resume_json.parsing_confidence:.2%}")
        return resume_json
    
    def _format_contact(self, contact_data) -> ContactInfo:
        """Format contact information."""
        if isinstance(contact_data, ContactInfo):
            return contact_data
        elif isinstance(contact_data, dict):
            return ContactInfo(**contact_data)
        else:
            return ContactInfo()
    
    def _format_experience(self, experience_data) -> list[ExperienceEntry]:
        """Format experience entries."""
        formatted_experience = []
        
        for exp in experience_data:
            if isinstance(exp, ExperienceEntry):
                formatted_experience.append(exp)
            elif isinstance(exp, dict):
                formatted_experience.append(ExperienceEntry(**exp))
        
        return formatted_experience
    
    def _format_projects(self, projects_data) -> list[ProjectEntry]:
        """Format project entries."""
        formatted_projects = []
        
        for proj in projects_data:
            if isinstance(proj, ProjectEntry):
                formatted_projects.append(proj)
            elif isinstance(proj, dict):
                formatted_projects.append(ProjectEntry(**proj))
        
        return formatted_projects
    
    def _format_education(self, education_data) -> list[EducationEntry]:
        """Format education entries."""
        formatted_education = []
        
        for edu in education_data:
            if isinstance(edu, EducationEntry):
                formatted_education.append(edu)
            elif isinstance(edu, dict):
                formatted_education.append(EducationEntry(**edu))
        
        return formatted_education
    
    def _format_skills(self, skills_data) -> list[SkillCategory]:
        """Format skill categories."""
        formatted_skills = []
        
        for skill_cat in skills_data:
            if isinstance(skill_cat, SkillCategory):
                formatted_skills.append(skill_cat)
            elif isinstance(skill_cat, dict):
                formatted_skills.append(SkillCategory(**skill_cat))
        
        return formatted_skills
    
    def _format_certifications(self, certifications_data) -> list[CertificationEntry]:
        """Format certifications."""
        formatted_certs = []
        
        for cert in certifications_data:
            if isinstance(cert, CertificationEntry):
                formatted_certs.append(cert)
            elif isinstance(cert, dict):
                formatted_certs.append(CertificationEntry(**cert))
        
        return formatted_certs
    
    def _format_contact_enhanced(self, contact_data, metadata: Dict[str, Any]) -> ContactInfo:
        """Enhanced contact formatting with metadata support."""
        contact = self._format_contact(contact_data)
        
        # Enhance with social media profiles from metadata
        social_profiles = metadata.get('social_profiles', {})
        
        if not contact.linkedin and 'linkedin' in social_profiles:
            contact.linkedin = social_profiles['linkedin']['url']
        
        if not contact.github and 'github' in social_profiles:
            contact.github = social_profiles['github']['url']
        
        # Add website from links if not already set
        if not contact.website:
            for link in metadata.get('links', []):
                url = link.get('url', '')
                if url and not any(domain in url.lower() for domain in ['linkedin.com', 'github.com', 'twitter.com', 'facebook.com']):
                    contact.website = url
                    break
        
        return contact
    
    def _format_projects_enhanced(self, projects_data, metadata: Dict[str, Any]) -> list[ProjectEntry]:
        """Enhanced project formatting with metadata support."""
        projects = self._format_projects(projects_data)
        
        # Enhance projects with link information from metadata
        for project in projects:
            if not project.url:
                # Try to find matching URL from metadata
                for link in metadata.get('links', []):
                    url = link.get('url', '')
                    if project.name and project.name.lower() in url.lower():
                        project.url = url
                        break
        
        return projects
    
    def _format_skills_enhanced(self, skills_data, metadata: Dict[str, Any]) -> list[SkillCategory]:
        """Enhanced skills formatting with metadata support."""
        skills = self._format_skills(skills_data)
        
        # Add skills from hidden text in metadata
        hidden_skills = []
        for hidden in metadata.get('hidden_text', []):
            hidden_text = hidden.get('text', '')
            # Extract potential skills from hidden text
            # This could be enhanced with more sophisticated skill extraction
            if any(skill_keyword in hidden_text.lower() for skill_keyword in ['python', 'java', 'react', 'aws', 'docker']):
                hidden_skills.extend(hidden_text.split())
        
        if hidden_skills:
            # Add to "Additional Skills" category
            additional_category = next((s for s in skills if s.category == "Additional Skills"), None)
            if not additional_category:
                additional_category = SkillCategory(category="Additional Skills", skills=[])
                skills.append(additional_category)
            
            for skill in hidden_skills:
                if skill not in additional_category.skills:
                    additional_category.skills.append(skill)
        
        return skills
    
    def _calculate_enhanced_confidence(self, resume_json: ResumeJSON, metadata: Dict[str, Any]) -> float:
        """
        Calculate enhanced parsing confidence with metadata consideration.
        """
        # Start with base confidence
        confidence = self._calculate_confidence(resume_json)
        
        # Boost confidence based on metadata findings
        metadata_boost = 0.0
        
        # Links found
        links_count = len(metadata.get('links', []))
        if links_count > 0:
            metadata_boost += min(0.1, links_count * 0.02)
        
        # Tables found
        tables_count = len(metadata.get('tables', []))
        if tables_count > 0:
            metadata_boost += min(0.05, tables_count * 0.01)
        
        # Hidden text found
        hidden_text_count = len(metadata.get('hidden_text', []))
        if hidden_text_count > 0:
            metadata_boost += min(0.05, hidden_text_count * 0.01)
        
        # Social media profiles
        social_profiles = metadata.get('social_profiles', {})
        if social_profiles:
            metadata_boost += min(0.05, len(social_profiles) * 0.01)
        
        # Document metadata
        doc_metadata = metadata.get('document_metadata', {})
        if any(doc_metadata.values()):
            metadata_boost += 0.02
        
        # Apply metadata boost
        confidence = min(1.0, confidence + metadata_boost)
        
        return confidence
    
    def _validate_and_clean_enhanced(self, resume_json: ResumeJSON, metadata: Dict[str, Any]) -> ResumeJSON:
        """
        Enhanced validation and cleaning with metadata consideration.
        """
        # Apply base validation
        resume_json = self._validate_and_clean(resume_json)
        
        # Additional validation based on metadata
        if metadata:
            # Validate links
            for link in metadata.get('links', []):
                url = link.get('url', '')
                if url and not url.startswith(('http://', 'https://', 'mailto:')):
                    # Fix malformed URLs
                    if '@' in url:
                        url = f"mailto:{url}"
                    else:
                        url = f"https://{url}"
        
        return resume_json
    
    def _calculate_confidence(self, resume_json: ResumeJSON) -> float:
        """
        Calculate parsing confidence based on extracted data quality.
        Formula from user specification.
        """
        confidence = 0.0
        
        # Basic presence scoring
        if resume_json.summary:
            confidence += 0.1
        
        if resume_json.experience:
            confidence += 0.2 * min(1, len(resume_json.experience))
        
        if resume_json.projects:
            confidence += 0.1 * min(1, len(resume_json.projects))
        
        if resume_json.skills:
            confidence += 0.1 * min(1, len(resume_json.skills))
        
        if resume_json.education:
            confidence += 0.05 * min(1, len(resume_json.education))
        
        # Contact information quality
        contact_score = 0
        if resume_json.contact.name:
            contact_score += 0.25
        if resume_json.contact.email:
            contact_score += 0.25
        if resume_json.contact.phone:
            contact_score += 0.15
        if resume_json.contact.linkedin:
            contact_score += 0.15
        if resume_json.contact.github:
            contact_score += 0.1
        
        confidence += 0.15 * contact_score
        
        # Detailed data quality scoring
        if resume_json.experience:
            exp_quality = 0
            for exp in resume_json.experience:
                if exp.position and exp.company:
                    exp_quality += 0.3
                if exp.start_date:
                    exp_quality += 0.1
                if exp.bullets:
                    exp_quality += 0.2
                if exp.technologies:
                    exp_quality += 0.1
            
            avg_exp_quality = exp_quality / len(resume_json.experience)
            confidence += 0.15 * min(1, avg_exp_quality)
        
        # Domains detected
        if resume_json.domains:
            confidence += 0.05 * min(1, len(resume_json.domains) / 3)
        
        # Ensure confidence is between 0 and 1
        return min(1.0, max(0.0, confidence))
    
    def _validate_and_clean(self, resume_json: ResumeJSON) -> ResumeJSON:
        """
        Validate data and clean up any inconsistencies.
        """
        # Clean up empty strings
        if resume_json.summary == "":
            resume_json.summary = None
        
        # Validate email format
        if resume_json.contact.email:
            if "@" not in resume_json.contact.email:
                resume_json.contact.email = None
        
        # Clean up experience entries
        valid_experience = []
        for exp in resume_json.experience:
            if exp.position or exp.company:  # Must have at least position or company
                valid_experience.append(exp)
        resume_json.experience = valid_experience
        
        # Clean up project entries
        valid_projects = []
        for proj in resume_json.projects:
            if proj.name:  # Must have a name
                valid_projects.append(proj)
        resume_json.projects = valid_projects
        
        # Clean up education entries
        valid_education = []
        for edu in resume_json.education:
            if edu.institution or edu.degree:  # Must have institution or degree
                valid_education.append(edu)
        resume_json.education = valid_education
        
        # Remove empty skill categories
        valid_skills = []
        for skill_cat in resume_json.skills:
            if skill_cat.skills:  # Must have at least one skill
                # Remove duplicate skills
                skill_cat.skills = list(set(skill_cat.skills))
                valid_skills.append(skill_cat)
        resume_json.skills = valid_skills
        
        # Clean up achievements (remove very short ones)
        resume_json.achievements = [
            achievement for achievement in resume_json.achievements 
            if len(achievement.strip()) > 10
        ]
        
        # Remove duplicate domains
        resume_json.domains = list(set(resume_json.domains))
        
        logger.info(f"Validation complete. Final confidence: {resume_json.parsing_confidence:.2%}")
        return resume_json

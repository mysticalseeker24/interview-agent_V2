"""
Persona Service for TalentSync Transcription Service
Manages different interviewer personas based on domain and candidate background
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class Persona:
    """Represents an interviewer persona with its characteristics and questions."""
    name: str
    domain: str
    personality: str
    expertise: List[str]
    interview_approach: List[str]
    question_categories: Dict[str, List[str]]
    evaluation_criteria: List[str]
    success_indicators: List[str]
    technical_domains: List[str]
    file_path: str

class PersonaService:
    """Service for managing and loading interviewer personas."""
    
    def __init__(self, personas_dir: str = "personas"):
        self.personas_dir = Path(personas_dir)
        self.personas: Dict[str, Persona] = {}
        self.domain_mapping = {
            "dsa": "Data Structures & Algorithms",
            "devops": "DevOps & Infrastructure", 
            "ai-engineering": "AI Engineering",
            "machine-learning": "Machine Learning",
            "resume-based": "Resume-Based",
            "data-analyst": "Data Analysis",
            "software-engineering": "Software Engineering"
        }
        self._load_personas()
    
    def _load_personas(self):
        """Load all persona files from the personas directory."""
        try:
            # Load base personas
            base_personas_file = self.personas_dir / "base_personas.txt"
            if base_personas_file.exists():
                logger.info("Base personas file found")
            
            # Load individual personas
            individuals_dir = self.personas_dir / "individuals"
            if individuals_dir.exists():
                for persona_file in individuals_dir.glob("*.txt"):
                    self._load_persona_file(persona_file, "individual")
            
            # Load domain-specific personas
            jobs_dir = self.personas_dir / "jobs"
            if jobs_dir.exists():
                for domain_dir in jobs_dir.iterdir():
                    if domain_dir.is_dir():
                        domain = domain_dir.name
                        for persona_file in domain_dir.glob("*.txt"):
                            self._load_persona_file(persona_file, domain)
            
            logger.info(f"Loaded {len(self.personas)} personas")
            
        except Exception as e:
            logger.error(f"Error loading personas: {e}")
    
    def _load_persona_file(self, file_path: Path, domain: str):
        """Load a single persona file and parse its content."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the persona content
            persona = self._parse_persona_content(content, file_path.name, domain, str(file_path))
            if persona:
                key = f"{domain}_{persona.name.lower().replace(' ', '_')}"
                self.personas[key] = persona
                logger.info(f"Loaded persona: {persona.name} for domain: {domain}")
                
        except Exception as e:
            logger.error(f"Error loading persona file {file_path}: {e}")
    
    def _parse_persona_content(self, content: str, filename: str, domain: str, file_path: str) -> Optional[Persona]:
        """Parse persona content and extract structured information."""
        try:
            lines = content.split('\n')
            name = ""
            personality = ""
            expertise = []
            interview_approach = []
            question_categories = {}
            evaluation_criteria = []
            success_indicators = []
            technical_domains = []
            
            current_section = ""
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Extract name from first line
                if not name and line.startswith('# '):
                    name = line[2:].split(' - ')[0].strip()
                    continue
                
                # Parse sections
                if line.startswith('## '):
                    current_section = line[3:].lower()
                    continue
                
                # Parse content based on section
                if current_section == "personality & communication style":
                    personality += line + " "
                elif current_section == "background & expertise":
                    if line.startswith('- '):
                        expertise.append(line[2:])
                elif current_section == "interview approach":
                    if line.startswith('- '):
                        interview_approach.append(line[2:])
                elif current_section == "evaluation criteria":
                    if line.startswith('- '):
                        evaluation_criteria.append(line[2:])
                elif current_section == "success indicators":
                    if line.startswith('- '):
                        success_indicators.append(line[2:])
                elif current_section == "technical domains covered":
                    if line.startswith('- '):
                        technical_domains.append(line[2:])
                elif "question" in current_section and line.startswith('### '):
                    category = line[4:]
                    question_categories[category] = []
                elif current_section in question_categories and line.startswith('- '):
                    question_categories[current_section].append(line[2:])
            
            if name:
                return Persona(
                    name=name,
                    domain=domain,
                    personality=personality.strip(),
                    expertise=expertise,
                    interview_approach=interview_approach,
                    question_categories=question_categories,
                    evaluation_criteria=evaluation_criteria,
                    success_indicators=success_indicators,
                    technical_domains=technical_domains,
                    file_path=file_path
                )
            
        except Exception as e:
            logger.error(f"Error parsing persona content: {e}")
        
        return None
    
    def get_persona(self, domain: str, persona_name: str = None) -> Optional[Persona]:
        """Get a specific persona by domain and optional name."""
        if persona_name:
            key = f"{domain}_{persona_name.lower().replace(' ', '_')}"
            return self.personas.get(key)
        else:
            # Return the first persona for the domain
            for key, persona in self.personas.items():
                if key.startswith(f"{domain}_"):
                    return persona
        return None
    
    def get_available_personas(self) -> Dict[str, List[str]]:
        """Get all available personas organized by domain."""
        available = {}
        for key, persona in self.personas.items():
            domain = key.split('_')[0]
            if domain not in available:
                available[domain] = []
            available[domain].append(persona.name)
        return available
    
    def get_domain_personas(self, domain: str) -> List[Persona]:
        """Get all personas for a specific domain."""
        domain_personas = []
        for key, persona in self.personas.items():
            if key.startswith(f"{domain}_"):
                domain_personas.append(persona)
        return domain_personas
    
    def get_persona_questions(self, persona: Persona, category: str = None) -> List[str]:
        """Get questions for a specific persona and optional category."""
        if category and category in persona.question_categories:
            return persona.question_categories[category]
        elif persona.question_categories:
            # Return all questions from all categories
            all_questions = []
            for questions in persona.question_categories.values():
                all_questions.extend(questions)
            return all_questions
        return []
    
    def get_persona_for_resume(self, resume_data: Dict[str, Any]) -> Optional[Persona]:
        """Select the most appropriate persona based on resume data."""
        # Analyze resume to determine domain and experience level
        skills = resume_data.get('skills', [])
        experience = resume_data.get('experience', [])
        
        # Determine domain based on skills
        domain = self._determine_domain_from_skills(skills)
        
        # Determine experience level
        experience_level = self._determine_experience_level(experience)
        
        # Select appropriate persona
        if domain == "resume-based":
            return self.get_persona("resume-based", "Olivia")
        else:
            # Get domain-specific persona based on experience level
            domain_personas = self.get_domain_personas(domain)
            if domain_personas:
                # For now, return the first persona for the domain
                # In the future, we could implement more sophisticated selection
                return domain_personas[0]
        
        return None
    
    def _determine_domain_from_skills(self, skills: List[str]) -> str:
        """Determine the primary domain based on skills."""
        skill_text = ' '.join(skills).lower()
        
        # Define domain keywords
        domain_keywords = {
            "dsa": ["algorithm", "data structure", "leetcode", "competitive programming"],
            "devops": ["docker", "kubernetes", "aws", "azure", "terraform", "ci/cd"],
            "ai-engineering": ["machine learning", "deep learning", "neural network", "tensorflow", "pytorch"],
            "machine-learning": ["ml", "machine learning", "scikit-learn", "pandas", "numpy"],
            "data-analyst": ["sql", "tableau", "power bi", "excel", "statistics"],
            "software-engineering": ["react", "angular", "node.js", "java", "python", "full stack"]
        }
        
        # Count matches for each domain
        domain_scores = {}
        for domain, keywords in domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword in skill_text)
            domain_scores[domain] = score
        
        # Return domain with highest score, default to resume-based
        if domain_scores:
            best_domain = max(domain_scores, key=domain_scores.get)
            if domain_scores[best_domain] > 0:
                return best_domain
        
        return "resume-based"
    
    def _determine_experience_level(self, experience: List[Dict[str, Any]]) -> str:
        """Determine experience level based on work history."""
        total_years = 0
        for exp in experience:
            duration = exp.get('duration', '')
            # Simple parsing of duration (could be enhanced)
            if 'year' in duration.lower():
                try:
                    years = int(''.join(filter(str.isdigit, duration)))
                    total_years += years
                except:
                    pass
        
        if total_years <= 2:
            return "junior"
        elif total_years <= 5:
            return "mid-level"
        else:
            return "senior"
    
    def get_persona_summary(self) -> Dict[str, Any]:
        """Get a summary of all loaded personas."""
        summary = {
            "total_personas": len(self.personas),
            "domains": {},
            "personas": {}
        }
        
        for key, persona in self.personas.items():
            domain = key.split('_')[0]
            if domain not in summary["domains"]:
                summary["domains"][domain] = 0
            summary["domains"][domain] += 1
            
            summary["personas"][key] = {
                "name": persona.name,
                "domain": persona.domain,
                "expertise": persona.expertise[:3],  # First 3 items
                "technical_domains": persona.technical_domains[:3]  # First 3 items
            }
        
        return summary

# Global persona service instance
persona_service = PersonaService() 
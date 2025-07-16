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
    voice: str = "Briggs-PlayAI"  # Default voice

class PersonaService:
    """Service for managing and loading interviewer personas."""
    
    def __init__(self, personas_dir: str = None):
        # Use absolute path to personas directory
        if personas_dir is None:
            # Get the directory where this service file is located
            service_dir = Path(__file__).parent.parent.parent
            self.personas_dir = service_dir / "personas"
        else:
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
        
        # Voice mapping for different personas
        self.voice_mapping = {
            # Male voices
            "Briggs-PlayAI": "Professional, authoritative, experienced",
            "Calum-PlayAI": "Friendly, approachable, mentor-like", 
            "Cillian-PlayAI": "Analytical, precise, methodical",
            "Quinn-PlayAI": "Energetic, enthusiastic, motivating",
            
            # Female voices
            "Arista-PlayAI": "Warm, empathetic, supportive",
            "Celeste-PlayAI": "Clear, confident, articulate"
        }
        
        # Persona-specific voice assignments
        self.persona_voice_assignments = {
            # Individual personas
            "emma": "Arista-PlayAI",  # Enthusiastic networker - warm and friendly
            "liam": "Cillian-PlayAI",  # Methodical analyst - analytical and precise
            
            # Domain-specific personas
            "maya": "Celeste-PlayAI",  # AI/ML expert - clear and confident
            "noah": "Briggs-PlayAI",   # Data-driven decider - authoritative
            "jordan": "Calum-PlayAI",  # DevOps specialist - friendly and approachable
            "olivia": "Arista-PlayAI", # Empathetic listener - warm and supportive
            "taylor": "Quinn-PlayAI",  # Full-stack developer - energetic and motivating
        }
        
        self._load_personas()
    
    def _load_personas(self):
        """Load all persona files from the personas directory."""
        try:
            logger.info(f"Loading personas from: {self.personas_dir}")
            
            if not self.personas_dir.exists():
                logger.error(f"Personas directory not found: {self.personas_dir}")
                return
            
            # Load base personas
            base_personas_file = self.personas_dir / "base_personas.txt"
            if base_personas_file.exists():
                logger.info("Base personas file found")
            
            # Load individual personas
            individuals_dir = self.personas_dir / "individuals"
            if individuals_dir.exists():
                logger.info(f"Loading individual personas from: {individuals_dir}")
                for persona_file in individuals_dir.glob("*.txt"):
                    logger.info(f"Found individual persona file: {persona_file}")
                    self._load_persona_file(persona_file, "individual")
            
            # Load domain-specific personas
            jobs_dir = self.personas_dir / "jobs"
            if jobs_dir.exists():
                logger.info(f"Loading domain personas from: {jobs_dir}")
                for domain_dir in jobs_dir.iterdir():
                    if domain_dir.is_dir():
                        domain = domain_dir.name
                        logger.info(f"Loading personas for domain: {domain}")
                        for persona_file in domain_dir.glob("*.txt"):
                            logger.info(f"Found domain persona file: {persona_file}")
                            self._load_persona_file(persona_file, domain)
            
            logger.info(f"Loaded {len(self.personas)} personas")
            
        except Exception as e:
            logger.error(f"Error loading personas: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
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
            logger.info(f"Parsing persona file: {filename}")
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
                    # Extract name from first line with format "# Name - Title"
                    if not name and line.startswith('# ') and ' - ' in line:
                        name = line[2:].split(' - ')[0].strip()
                        logger.info(f"Extracted name: {name}")
                    continue
                
                # Parse sections
                if line.startswith('## '):
                    current_section = line[3:].lower()
                    logger.info(f"Found section: {current_section}")
                    continue
                
                # Parse content based on section
                if current_section == "domain expertise":
                    personality += line + " "
                elif current_section == "technical focus areas":
                    if line.startswith('- '):
                        expertise.append(line[2:])
                elif current_section == "interview approach for":
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
                elif current_section == "sample question categories":
                    # This section contains question categories
                    pass
                elif line.startswith('### ') and current_section == "sample question categories":
                    category = line[4:]
                    question_categories[category] = []
                elif current_section == "sample question categories" and line.startswith('- '):
                    # Find the current category
                    for category in question_categories.keys():
                        if category in current_section:
                            question_categories[category].append(line[2:])
                            break
                    else:
                        # If no category found, add to the last category
                        if question_categories:
                            last_category = list(question_categories.keys())[-1]
                            question_categories[last_category].append(line[2:])
            
            logger.info(f"Parsed persona - Name: {name}, Domain: {domain}, Expertise: {len(expertise)} items")
            
            if name:
                # Assign appropriate voice based on persona name and characteristics
                voice = self._assign_voice_to_persona(name, domain, personality)
                
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
                    file_path=file_path,
                    voice=voice
                )
            else:
                logger.warning(f"No name found in persona file: {filename}")
            
        except Exception as e:
            logger.error(f"Error parsing persona content: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        return None
    
    def _assign_voice_to_persona(self, name: str, domain: str, personality: str) -> str:
        """Assign an appropriate voice to a persona based on their characteristics."""
        name_lower = name.lower()
        
        # First, check for exact name matches
        for persona_name, voice in self.persona_voice_assignments.items():
            if persona_name in name_lower:
                logger.info(f"Assigned voice {voice} to persona {name} based on name match")
                return voice
        
        # If no exact match, assign based on domain and personality characteristics
        personality_lower = personality.lower()
        
        # Analyze personality traits to choose appropriate voice
        if any(word in personality_lower for word in ["analytical", "methodical", "precise", "systematic"]):
            return "Cillian-PlayAI"  # Analytical and precise
        elif any(word in personality_lower for word in ["friendly", "approachable", "mentor", "supportive"]):
            return "Calum-PlayAI"  # Friendly and approachable
        elif any(word in personality_lower for word in ["enthusiastic", "energetic", "motivating", "passionate"]):
            return "Quinn-PlayAI"  # Energetic and enthusiastic
        elif any(word in personality_lower for word in ["empathetic", "warm", "supportive", "understanding"]):
            return "Arista-PlayAI"  # Warm and empathetic
        elif any(word in personality_lower for word in ["authoritative", "experienced", "professional", "expert"]):
            return "Briggs-PlayAI"  # Professional and authoritative
        elif any(word in personality_lower for word in ["clear", "confident", "articulate", "expert"]):
            return "Celeste-PlayAI"  # Clear and confident
        
        # Default assignments based on domain
        domain_voice_defaults = {
            "ai-engineering": "Celeste-PlayAI",  # Clear and confident for technical expertise
            "machine-learning": "Celeste-PlayAI",  # Clear and confident for technical expertise
            "devops": "Calum-PlayAI",  # Friendly and approachable for collaborative work
            "software-engineering": "Quinn-PlayAI",  # Energetic for dynamic development
            "data-analyst": "Briggs-PlayAI",  # Authoritative for data-driven decisions
            "dsa": "Cillian-PlayAI",  # Analytical for algorithmic thinking
            "resume-based": "Arista-PlayAI",  # Empathetic for personal assessment
            "individual": "Arista-PlayAI"  # Default to empathetic for individual personas
        }
        
        default_voice = domain_voice_defaults.get(domain, "Briggs-PlayAI")
        logger.info(f"Assigned default voice {default_voice} to persona {name} for domain {domain}")
        return default_voice
    
    def get_available_voices(self) -> Dict[str, str]:
        """Get all available voices with their descriptions."""
        return self.voice_mapping.copy()
    
    def get_persona_voice(self, persona: Persona) -> str:
        """Get the assigned voice for a specific persona."""
        return persona.voice
    
    def get_voice_description(self, voice: str) -> str:
        """Get the description for a specific voice."""
        return self.voice_mapping.get(voice, "Unknown voice")
    
    def get_personas_by_voice(self, voice: str) -> List[Persona]:
        """Get all personas that use a specific voice."""
        return [persona for persona in self.personas.values() if persona.voice == voice]
    
    def get_voice_summary(self) -> Dict[str, Any]:
        """Get a summary of voice assignments across all personas."""
        voice_summary = {}
        for voice in self.voice_mapping.keys():
            personas_with_voice = self.get_personas_by_voice(voice)
            voice_summary[voice] = {
                "description": self.voice_mapping[voice],
                "personas": [persona.name for persona in personas_with_voice],
                "count": len(personas_with_voice)
            }
        return voice_summary
    
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
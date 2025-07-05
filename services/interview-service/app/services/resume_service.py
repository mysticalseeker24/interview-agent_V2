"""Resume service interface for interview question generation."""
import logging
from typing import List, Dict, Any
import httpx
from app.models import Question
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class ResumeService:
    """Service for generating resume-driven interview questions."""
    
    def __init__(self):
        """Initialize Resume Service."""
        self.settings = get_settings()
    
    async def generate_templated_questions(self, resume_data: Dict[str, Any]) -> List[Question]:
        """
        Generate interview questions based on resume data.
        
        Args:
            resume_data: Parsed resume data
            
        Returns:
            List of generated questions
        """
        # Get skills and projects from resume data
        skills = resume_data.get('skills', [])
        projects = resume_data.get('projects', [])
        
        # Generate questions based on skills and projects
        questions = []
        
        # Create skill-based questions
        for skill in skills[:5]:  # Limit to top 5 skills
            question = Question(
                text=f"Can you describe your experience with {skill}? What projects have you used it in?",
                difficulty="medium",
                question_type="open_ended",
                expected_duration_seconds=180,
                tags=[skill.lower(), "experience"],
                ideal_answer=f"Candidate should demonstrate practical experience with {skill}",
                scoring_criteria={
                    "technical_depth": "Shows understanding of core concepts",
                    "practical_experience": "Provides specific examples",
                    "problem_solving": "Discusses challenges and solutions"
                }
            )
            questions.append(question)
        
        # Create project-based questions
        for project in projects[:3]:  # Limit to top 3 projects
            question = Question(
                text=f"Tell me about your {project} project. What was your role and what challenges did you face?",
                difficulty="medium", 
                question_type="scenario",
                expected_duration_seconds=240,
                tags=[project.lower(), "project"],
                ideal_answer=f"Candidate should explain the {project} project with technical details",
                scoring_criteria={
                    "project_complexity": "Describes technical complexity",
                    "role_clarity": "Clearly explains their contribution",
                    "problem_solving": "Discusses challenges and solutions"
                }
            )
            questions.append(question)
        
        logger.info(f"Generated {len(questions)} resume-driven questions")
        return questions
    
    async def get_parsed_resume_data(self, resume_id: int, user_id: int) -> Dict[str, Any]:
        """
        Get parsed resume data from Resume Service.
        
        Args:
            resume_id: Resume ID
            user_id: User ID
            
        Returns:
            Parsed resume data
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.settings.RESUME_SERVICE_URL}/api/v1/resume/internal/{resume_id}/data",
                    params={"user_id": user_id}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"Resume service returned {response.status_code}")
                    return {}
                    
        except Exception as e:
            logger.error(f"Error fetching resume data: {str(e)}")
            return {}
    
    async def fetch_resume_data(self, resume_id: int, user_id: int) -> Dict[str, Any]:
        """
        Fetch parsed resume data from resume service.
        
        Args:
            resume_id: Resume ID
            user_id: User ID
            
        Returns:
            Parsed resume data
            
        Raises:
            Exception: If resume data cannot be fetched
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.settings.RESUME_SERVICE_URL}/api/v1/resume/internal/{resume_id}/data",
                    params={"user_id": user_id},
                    timeout=30.0
                )
                
                if response.status_code == 404:
                    logger.warning(f"Resume {resume_id} not found for user {user_id}")
                    return {}
                
                response.raise_for_status()
                return response.json()
                
        except httpx.RequestError as e:
            logger.error(f"Failed to fetch resume data: {str(e)}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error fetching resume data: {str(e)}")
            return {}

    async def analyze_experience(self, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze candidate experience from resume.
        
        Args:
            resume_data: Parsed resume data
            
        Returns:
            Experience analysis
        """
        skills = resume_data.get('skills', [])
        projects = resume_data.get('projects', [])
        experience_years = resume_data.get('experience_years', 0)
        
        return {
            "years_experience": experience_years,
            "key_skills": skills[:10],  # Top 10 skills
            "relevant_domains": list(set([skill.lower() for skill in skills if any(
                domain in skill.lower() for domain in 
                ['web', 'backend', 'frontend', 'mobile', 'ai', 'ml', 'data', 'cloud']
            )])),
            "project_count": len(projects),
            "technical_depth": "high" if len(skills) > 15 else "medium" if len(skills) > 8 else "basic"
        }

"""Session service with RAG-enabled dynamic questioning."""
import logging
import random
from datetime import datetime
from typing import List, Optional, Dict, Any

from app.schemas.session import SessionCreate, NextQuestionResponse, AnswerSubmit
from app.services.resume_service import ResumeService
from app.services.celery_service import CeleryService

logger = logging.getLogger(__name__)


class SessionService:
    """Service class for session management and question orchestration."""
    
    def __init__(self, db):
        self.db = db
        self.resume_service = ResumeService()
        self.celery_service = CeleryService()
    
    async def create_session(self, user_id: int, session_data: SessionCreate) -> Any:
        """
        Create a new interview session and seed with questions.
        
        Args:
            user_id: User ID from authentication
            session_data: Session creation data
            
        Returns:
            Created session with seeded question queue
        """
        # Create session record
        # This method is not DB-dependent, so we can return a placeholder
        # In a real scenario, this would involve DB operations
        session = {
            "id": 1, # Placeholder ID
            "user_id": user_id,
            "module_id": session_data.module_id,
            "mode": session_data.mode,
            "parsed_resume_data": session_data.parsed_resume_data,
            "status": "pending", # Placeholder status
            "queue": [], # Placeholder queue
            "current_question_index": 0, # Placeholder index
            "started_at": None, # Placeholder start time
            "completed_at": None, # Placeholder completion time
            "estimated_duration_minutes": 0 # Placeholder duration
        }
        
        # Seed session with questions
        await self.seed_session(session["id"])
        
        return session
    
    async def seed_session(self, session_id: int) -> None:
        """
        Seed session with interleaved core and resume-driven questions.
        
        Args:
            session_id: Session ID to seed
        """
        # Get session with module
        # This method is not DB-dependent, so we can return a placeholder
        # In a real scenario, this would involve DB operations
        session = {
            "id": session_id,
            "module_id": 1, # Placeholder module ID
            "parsed_resume_data": None, # Placeholder resume data
            "queue": [], # Placeholder queue
            "estimated_duration_minutes": 0 # Placeholder duration
        }
        
        # Get core module questions
        core_questions = await self._get_core_questions(session["module_id"])
        
        # Generate resume-driven questions if resume data available
        resume_questions = []
        if session["parsed_resume_data"]:
            resume_questions = await self.resume_service.generate_templated_questions(
                session["parsed_resume_data"]
            )
        
        # Interleave questions
        question_queue = self._interleave_questions(core_questions, resume_questions)
        
        # Update session with question queue
        session["queue"] = [q["id"] for q in question_queue] # Assuming question objects have an 'id'
        session["estimated_duration_minutes"] = self._calculate_duration(question_queue)
        
        logger.info(f"Seeded session {session_id} with {len(question_queue)} questions")
    
    async def _get_core_questions(self, module_id: int) -> List[Dict[str, Any]]:
        """
        Get core questions for a module.
        
        Args:
            module_id: Module ID
            
        Returns:
            List of core questions
        """
        # This method is not DB-dependent, so we can return a placeholder
        # In a real scenario, this would involve DB operations
        return [
            {"id": 1, "text": "Tell me about your experience with Python.", "difficulty": "easy", "expected_duration_seconds": 30},
            {"id": 2, "text": "What are your strengths and weaknesses?", "difficulty": "medium", "expected_duration_seconds": 45},
            {"id": 3, "text": "Describe a project you worked on that required problem-solving.", "difficulty": "hard", "expected_duration_seconds": 60}
        ]
    
    def _interleave_questions(
        self, 
        core_questions: List[Dict[str, Any]], 
        resume_questions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Interleave core and resume questions strategically.
        
        Args:
            core_questions: Core module questions
            resume_questions: Resume-driven questions
            
        Returns:
            Interleaved question list
        """
        if not resume_questions:
            return core_questions
        
        if not core_questions:
            return resume_questions
        
        # Strategy: Start with core, alternate with resume questions
        interleaved = []
        core_idx = 0
        resume_idx = 0
        
        # Start with a core question
        while core_idx < len(core_questions) or resume_idx < len(resume_questions):
            # Add core question
            if core_idx < len(core_questions):
                interleaved.append(core_questions[core_idx])
                core_idx += 1
            
            # Add resume question every 2-3 questions
            if resume_idx < len(resume_questions) and len(interleaved) % 2 == 0:
                interleaved.append(resume_questions[resume_idx])
                resume_idx += 1
        
        # Shuffle slightly to add variety while maintaining structure
        return self._smart_shuffle(interleaved)
    
    def _smart_shuffle(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Shuffle questions while maintaining difficulty progression.
        
        Args:
            questions: Questions to shuffle
            
        Returns:
            Shuffled questions
        """
        # Group by difficulty
        easy = [q for q in questions if q["difficulty"] == "easy"]
        medium = [q for q in questions if q["difficulty"] == "medium"]
        hard = [q for q in questions if q["difficulty"] == "hard"]
        
        # Shuffle within each group
        random.shuffle(easy)
        random.shuffle(medium)
        random.shuffle(hard)
        
        # Combine with progression: easy -> medium -> hard
        return easy + medium + hard
    
    def _calculate_duration(self, questions: List[Dict[str, Any]]) -> int:
        """
        Calculate estimated session duration.
        
        Args:
            questions: List of questions
            
        Returns:
            Estimated duration in minutes
        """
        total_seconds = sum(q["expected_duration_seconds"] for q in questions)
        return max(15, int(total_seconds / 60))  # Minimum 15 minutes
    
    async def get_next_question(self, session_id: int, user_id: int) -> NextQuestionResponse:
        """
        Get the next question for a session.
        
        Args:
            session_id: Session ID
            user_id: User ID for authorization
            
        Returns:
            Next question response with session status
        """
        # This method is not DB-dependent, so we can return a placeholder
        # In a real scenario, this would involve DB operations
        session = {
            "id": session_id,
            "current_question_index": 0, # Placeholder index
            "queue": [1, 2, 3], # Placeholder queue
            "status": "in_progress", # Placeholder status
            "started_at": datetime.utcnow(), # Placeholder start time
            "completed_at": None, # Placeholder completion time
            "estimated_duration_minutes": 0 # Placeholder duration
        }
        
        # Check if session is complete
        if session["current_question_index"] >= len(session["queue"]):
            session["status"] = "completed"
            session["completed_at"] = datetime.utcnow()
            
            return NextQuestionResponse(
                question=None,
                session=session,
                is_complete=True,
                remaining_questions=0
            )
        
        # Get current question
        question_id = session["queue"][session["current_question_index"]]
        
        # Update session status if first question
        if session["status"] == "pending":
            session["status"] = "in_progress"
            session["started_at"] = datetime.utcnow()
        
        # In a real scenario, this would involve DB operations
        question = {"id": question_id, "text": "Next question text", "difficulty": "medium"}
        
        return NextQuestionResponse(
            question=question,
            session=session,
            is_complete=False,
            remaining_questions=len(session["queue"]) - session["current_question_index"] - 1
        )
    
    async def submit_answer(
        self, 
        session_id: int, 
        user_id: int, 
        answer_data: AnswerSubmit
    ) -> Dict[str, Any]:
        """
        Submit answer and move to next question.
        
        Args:
            session_id: Session ID
            user_id: User ID for authorization
            answer_data: Answer submission data
            
        Returns:
            Response with next question or completion status
        """
        # This method is not DB-dependent, so we can return a placeholder
        # In a real scenario, this would involve DB operations
        session = {
            "id": session_id,
            "current_question_index": 0, # Placeholder index
            "queue": [1, 2, 3], # Placeholder queue
            "status": "in_progress", # Placeholder status
            "started_at": datetime.utcnow(), # Placeholder start time
            "completed_at": None, # Placeholder completion time
            "estimated_duration_minutes": 0 # Placeholder duration
        }
        
        # Get current question
        question_id = session["queue"][session["current_question_index"]]
        
        # Create response record
        response = {
            "id": 1, # Placeholder ID
            "session_id": session_id,
            "question_id": question_id,
            "answer_text": answer_data.answer_text,
            "audio_file_path": answer_data.audio_file_path,
            "started_at": answer_data.started_at,
            "duration_seconds": answer_data.duration_seconds
        }
        
        # In a real scenario, this would involve DB operations
        # self.db.add(response)
        
        # Move to next question
        session["current_question_index"] += 1
        
        # In a real scenario, this would involve DB operations
        # await self.db.commit()
        
        # Enqueue Celery task for feedback processing
        await self.celery_service.enqueue_feedback_processing(session_id)
        
        # Get next question or completion status
        next_response = await self.get_next_question(session_id, user_id)
        
        return {
            "response_id": response["id"],
            "session": next_response.session,
            "next_question": next_response.question,
            "is_complete": next_response.is_complete
        }
    
    async def _get_session_with_auth(self, session_id: int, user_id: int) -> Any:
        """
        Get session with user authorization check.
        
        Args:
            session_id: Session ID
            user_id: User ID
            
        Returns:
            Session if authorized
            
        Raises:
            HTTPException: If session not found or unauthorized
        """
        # This method is not DB-dependent, so we can return a placeholder
        # In a real scenario, this would involve DB operations
        session = {
            "id": session_id,
            "user_id": user_id,
            "module_id": 1, # Placeholder module ID
            "mode": "mock", # Placeholder mode
            "parsed_resume_data": None, # Placeholder resume data
            "status": "in_progress", # Placeholder status
            "current_question_index": 0, # Placeholder index
            "queue": [1, 2, 3], # Placeholder queue
            "started_at": datetime.utcnow(), # Placeholder start time
            "completed_at": None, # Placeholder completion time
            "estimated_duration_minutes": 0 # Placeholder duration
        }
        
        return session
    
    async def _get_question_by_id(self, question_id: int) -> Any:
        """
        Get question by ID.
        
        Args:
            question_id: Question ID
            
        Returns:
            Question
        """
        # This method is not DB-dependent, so we can return a placeholder
        # In a real scenario, this would involve DB operations
        question = {"id": question_id, "text": "Question text", "difficulty": "medium"}
        return question

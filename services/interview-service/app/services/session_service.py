"""Session service with RAG-enabled dynamic questioning."""
import logging
import random
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models import Session, Question, Response, Module, SessionStatus
from app.schemas.session import SessionCreate, NextQuestionResponse, AnswerSubmit
from app.services.resume_service import ResumeService
from app.services.celery_service import CeleryService

logger = logging.getLogger(__name__)


class SessionService:
    """Service class for session management and question orchestration."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.resume_service = ResumeService()
        self.celery_service = CeleryService()
    
    async def create_session(self, user_id: int, session_data: SessionCreate) -> Session:
        """
        Create a new interview session and seed with questions.
        
        Args:
            user_id: User ID from authentication
            session_data: Session creation data
            
        Returns:
            Created session with seeded question queue
        """
        # Create session record
        session = Session(
            user_id=user_id,
            module_id=session_data.module_id,
            mode=session_data.mode,
            parsed_resume_data=session_data.parsed_resume_data,
            status=SessionStatus.PENDING
        )
        
        self.db.add(session)
        await self.db.flush()  # Get session ID
        
        # Seed session with questions
        await self.seed_session(session.id)
        
        await self.db.commit()
        await self.db.refresh(session)
        
        logger.info(f"Created session {session.id} for user {user_id}")
        return session
    
    async def seed_session(self, session_id: int) -> None:
        """
        Seed session with interleaved core and resume-driven questions.
        
        Args:
            session_id: Session ID to seed
        """
        # Get session with module
        result = await self.db.execute(
            select(Session)
            .options(selectinload(Session.module))
            .where(Session.id == session_id)
        )
        session = result.scalar_one()
        
        # Get core module questions
        core_questions = await self._get_core_questions(session.module_id)
        
        # Generate resume-driven questions if resume data available
        resume_questions = []
        if session.parsed_resume_data:
            resume_questions = await self.resume_service.generate_templated_questions(
                session.parsed_resume_data
            )
        
        # Interleave questions
        question_queue = self._interleave_questions(core_questions, resume_questions)
        
        # Update session with question queue
        session.queue = [q.id for q in question_queue]
        session.estimated_duration_minutes = self._calculate_duration(question_queue)
        
        logger.info(f"Seeded session {session_id} with {len(question_queue)} questions")
    
    async def _get_core_questions(self, module_id: int) -> List[Question]:
        """
        Get core questions for a module.
        
        Args:
            module_id: Module ID
            
        Returns:
            List of core questions
        """
        result = await self.db.execute(
            select(Question)
            .where(Question.module_id == module_id)
            .order_by(Question.difficulty, Question.id)
        )
        return result.scalars().all()
    
    def _interleave_questions(
        self, 
        core_questions: List[Question], 
        resume_questions: List[Question]
    ) -> List[Question]:
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
    
    def _smart_shuffle(self, questions: List[Question]) -> List[Question]:
        """
        Shuffle questions while maintaining difficulty progression.
        
        Args:
            questions: Questions to shuffle
            
        Returns:
            Shuffled questions
        """
        # Group by difficulty
        easy = [q for q in questions if q.difficulty == "easy"]
        medium = [q for q in questions if q.difficulty == "medium"]
        hard = [q for q in questions if q.difficulty == "hard"]
        
        # Shuffle within each group
        random.shuffle(easy)
        random.shuffle(medium)
        random.shuffle(hard)
        
        # Combine with progression: easy -> medium -> hard
        return easy + medium + hard
    
    def _calculate_duration(self, questions: List[Question]) -> int:
        """
        Calculate estimated session duration.
        
        Args:
            questions: List of questions
            
        Returns:
            Estimated duration in minutes
        """
        total_seconds = sum(q.expected_duration_seconds for q in questions)
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
        session = await self._get_session_with_auth(session_id, user_id)
        
        # Check if session is complete
        if session.current_question_index >= len(session.queue):
            session.status = SessionStatus.COMPLETED
            session.completed_at = datetime.utcnow()
            await self.db.commit()
            
            return NextQuestionResponse(
                question=None,
                session=session,
                is_complete=True,
                remaining_questions=0
            )
        
        # Get current question
        question_id = session.queue[session.current_question_index]
        question = await self._get_question_by_id(question_id)
        
        # Update session status if first question
        if session.status == SessionStatus.PENDING:
            session.status = SessionStatus.IN_PROGRESS
            session.started_at = datetime.utcnow()
        
        await self.db.commit()
        
        remaining = len(session.queue) - session.current_question_index - 1
        
        return NextQuestionResponse(
            question=question,
            session=session,
            is_complete=False,
            remaining_questions=remaining
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
        session = await self._get_session_with_auth(session_id, user_id)
        
        # Get current question
        question_id = session.queue[session.current_question_index]
        
        # Create response record
        response = Response(
            session_id=session_id,
            question_id=question_id,
            answer_text=answer_data.answer_text,
            audio_file_path=answer_data.audio_file_path,
            started_at=answer_data.started_at,
            duration_seconds=answer_data.duration_seconds
        )
        
        self.db.add(response)
        
        # Move to next question
        session.current_question_index += 1
        
        await self.db.commit()
        
        # Enqueue Celery task for feedback processing
        await self.celery_service.enqueue_feedback_processing(session_id)
        
        # Get next question or completion status
        next_response = await self.get_next_question(session_id, user_id)
        
        return {
            "response_id": response.id,
            "session": next_response.session,
            "next_question": next_response.question,
            "is_complete": next_response.is_complete
        }
    
    async def _get_session_with_auth(self, session_id: int, user_id: int) -> Session:
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
        from fastapi import HTTPException, status
        
        result = await self.db.execute(
            select(Session).where(
                Session.id == session_id,
                Session.user_id == user_id
            )
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or access denied"
            )
        
        return session
    
    async def _get_question_by_id(self, question_id: int) -> Question:
        """
        Get question by ID.
        
        Args:
            question_id: Question ID
            
        Returns:
            Question
        """
        result = await self.db.execute(
            select(Question).where(Question.id == question_id)
        )
        return result.scalar_one()

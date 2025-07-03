"""Module management routers for interview service."""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Module, Question
from app.schemas.module import ModuleResponse
from app.schemas.question import QuestionResponse
from app.schemas.user import UserRead

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/modules", tags=["modules"])


@router.get("/", response_model=List[ModuleResponse])
async def list_modules(
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(get_current_user)
):
    """
    List available interview modules.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of available modules
    """
    try:
        result = await db.execute(
            select(Module).where(Module.is_active == True)
        )
        modules = result.scalars().all()
        
        return [
            ModuleResponse(
                id=module.id,
                title=module.title,
                description=module.description,
                category=module.category,
                difficulty=module.difficulty,
                duration_minutes=module.duration_minutes,
                is_active=bool(module.is_active),
                created_at=module.created_at,
                updated_at=module.updated_at
            )
            for module in modules
        ]
        
    except Exception as e:
        logger.error(f"Error listing modules: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list modules"
        )


@router.get("/{module_id}", response_model=ModuleResponse)
async def get_module(
    module_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(get_current_user)
):
    """
    Get module details.
    
    Args:
        module_id: Module ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Module details
    """
    try:
        result = await db.execute(
            select(Module).where(Module.id == module_id)
        )
        module = result.scalar_one_or_none()
        
        if not module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Module not found"
            )
        
        return ModuleResponse(
            id=module.id,
            title=module.title,
            description=module.description,
            category=module.category,
            difficulty=module.difficulty,
            duration_minutes=module.duration_minutes,
            is_active=bool(module.is_active),
            created_at=module.created_at,
            updated_at=module.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting module {module_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get module"
        )


@router.get("/{module_id}/questions", response_model=List[QuestionResponse])
async def list_module_questions(
    module_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(get_current_user)
):
    """
    List questions for a module.
    
    Args:
        module_id: Module ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of module questions
    """
    try:
        # Check if module exists
        result = await db.execute(
            select(Module).where(Module.id == module_id)
        )
        module = result.scalar_one_or_none()
        
        if not module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Module not found"
            )
        
        # Get questions
        result = await db.execute(
            select(Question).where(Question.module_id == module_id)
        )
        questions = result.scalars().all()
        
        return [
            QuestionResponse(
                id=question.id,
                module_id=question.module_id,
                text=question.text,
                question_type=question.question_type,
                difficulty=question.difficulty,
                expected_duration_seconds=question.expected_duration_seconds,
                tags=question.tags,
                ideal_answer=question.ideal_answer,
                scoring_criteria=question.scoring_criteria,
                created_at=question.created_at,
                updated_at=question.updated_at
            )
            for question in questions
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing questions for module {module_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list module questions"
        )

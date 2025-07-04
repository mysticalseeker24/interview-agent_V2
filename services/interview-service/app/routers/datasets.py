"""
Router for dataset management and question imports.
Handles importing question datasets from JSON files.
"""
import json
import logging
from typing import Dict, List, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.embedding_service import EmbeddingService
from app.schemas.question import QuestionImport, QuestionBatchImport
from app.models.question import Question
from app.models.module import Module

router = APIRouter()
embedding_service = EmbeddingService()
logger = logging.getLogger(__name__)

@router.post("/import/file", status_code=status.HTTP_202_ACCEPTED)
async def import_questions_from_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    module_id: int = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Import questions from a JSON file.
    
    The file should contain an array of question objects with the following format:
    [
        {
            "text": "Question text",
            "difficulty": "medium",
            "domain": "Software Engineering",
            "type": "technical",
            "question_type": "open_ended",
            "tags": ["python", "programming"]
        },
        ...
    ]
    
    Args:
        file: JSON file with questions
        module_id: Optional module ID to assign questions to
        db: Database session
    
    Returns:
        Import summary with count of imported questions
    """
    if not file.filename.endswith('.json'):
        raise HTTPException(
            status_code=400,
            detail="Only JSON files are supported."
        )
    
    try:
        # Read and parse the file
        contents = await file.read()
        questions_data = json.loads(contents.decode())
        
        # Validate questions data
        if not isinstance(questions_data, list):
            raise HTTPException(
                status_code=400,
                detail="The JSON file should contain an array of question objects."
            )
        
        # Convert to QuestionImport schema
        question_imports = []
        for item in questions_data:
            # Ensure required fields are present
            if 'text' not in item:
                continue
                
            question = {
                'text': item['text'],
                'difficulty': item.get('difficulty', 'medium'),
                'domain': item.get('domain', 'general'),
                'type': item.get('type', 'general'),
                'question_type': item.get('question_type', 'open_ended'),
                'tags': item.get('tags', []),
                'module_id': module_id,
                'ideal_answer': item.get('ideal_answer', None),
                'expected_duration_seconds': item.get('expected_duration_seconds', 300)
            }
            question_imports.append(question)
        
        # Process import in background
        background_tasks.add_task(
            process_questions_import,
            questions=question_imports,
            module_id=module_id,
            db=db
        )
        
        return {
            "status": "accepted",
            "message": f"Import of {len(question_imports)} questions started in background",
            "question_count": len(question_imports)
        }
    
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON format. Please provide a valid JSON file."
        )
    except Exception as e:
        logger.error(f"Error importing questions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error importing questions: {str(e)}"
        )

@router.post("/import/json", status_code=status.HTTP_202_ACCEPTED)
async def import_questions_from_json(
    question_batch: QuestionBatchImport,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Import questions from JSON payload.
    
    Args:
        question_batch: Batch of questions to import
        db: Database session
    
    Returns:
        Import summary with count of imported questions
    """
    try:
        # Process import in background
        background_tasks.add_task(
            process_questions_import,
            questions=question_batch.questions,
            module_id=question_batch.module_id,
            db=db
        )
        
        return {
            "status": "accepted",
            "message": f"Import of {len(question_batch.questions)} questions started in background",
            "question_count": len(question_batch.questions)
        }
    except Exception as e:
        logger.error(f"Error importing questions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error importing questions: {str(e)}"
        )

async def process_questions_import(questions: List[Dict[str, Any]], module_id: int, db: AsyncSession):
    """
    Process the question import in the background.
    
    Args:
        questions: List of question data dictionaries
        module_id: Module ID to assign questions to
        db: Database session
    """
    logger.info(f"Processing import of {len(questions)} questions")
    
    try:
        async with db as session:
            # Check if module exists if module_id is provided
            if module_id:
                module = await session.get(Module, module_id)
                if not module:
                    logger.error(f"Module with ID {module_id} not found")
                    return
            
            # Insert questions in batches
            inserted_count = 0
            for question_data in questions:
                try:
                    # Create question object
                    question = Question(
                        text=question_data['text'],
                        module_id=module_id if module_id else question_data.get('module_id'),
                        difficulty=question_data.get('difficulty', 'medium'),
                        domain=question_data.get('domain', 'general'),
                        type=question_data.get('type', 'general'),
                        question_type=question_data.get('question_type', 'open_ended'),
                        tags=question_data.get('tags', []),
                        ideal_answer=question_data.get('ideal_answer'),
                        expected_duration_seconds=question_data.get('expected_duration_seconds', 300),
                        scoring_criteria=question_data.get('scoring_criteria', {})
                    )
                    
                    # Add to database
                    session.add(question)
                    inserted_count += 1
                    
                except Exception as e:
                    logger.error(f"Error inserting question: {str(e)}")
                    continue
            
            # Commit the transaction
            await session.commit()
            logger.info(f"Successfully imported {inserted_count} questions")
            
            # Sync questions to vector database
            if inserted_count > 0:
                await embedding_service.continuous_sync_worker(batch_size=inserted_count + 10)
                logger.info("Started background sync of imported questions to vector database")
            
    except Exception as e:
        logger.error(f"Error in question import process: {str(e)}")

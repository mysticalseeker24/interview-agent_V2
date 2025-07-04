"""
Router for dataset management and question imports.
Handles importing question datasets from JSON files.
"""
import json
import logging
import os
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

@router.post("/import/path", status_code=status.HTTP_202_ACCEPTED)
async def import_questions_from_path(
    background_tasks: BackgroundTasks,
    file_path: str,
    module_id: int = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Import questions from a JSON file path.
    
    Args:
        file_path: Path to the JSON file
        module_id: Optional module ID to assign questions to
        db: Database session
    
    Returns:
        Import summary with count of imported questions
    """
    if not os.path.exists(file_path) or not file_path.endswith('.json'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file path or not a JSON file."
        )
    
    try:
        # Read and parse the file
        with open(file_path, 'r', encoding='utf-8') as f:
            questions_data = json.loads(f.read())
        
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
                
            # Handle different dataset formats
            question = {
                'text': item['text'],
                'difficulty': item.get('difficulty', 'medium'),
                'domain': item.get('domain', os.path.basename(file_path).split('_')[0]),
                'type': item.get('type', 'general'),
                'question_type': item.get('question_type', 'open_ended'),
                'tags': item.get('tags', item.get('follow_up_templates', [])),
                'module_id': module_id,
                'ideal_answer': item.get('ideal_answer', item.get('ideal_answer_summary', None)),
                'expected_duration_seconds': item.get('expected_duration_seconds', 300),
                'scoring_criteria': item.get('scoring_criteria', {})
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
            "message": f"Import of {len(question_imports)} questions started in background from {os.path.basename(file_path)}",
            "question_count": len(question_imports)
        }
    
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON format. Please provide a valid JSON file."
        )
    except Exception as e:
        logger.error(f"Error importing questions from path: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error importing questions: {str(e)}"
        )

@router.post("/import/all", status_code=status.HTTP_202_ACCEPTED)
async def import_all_datasets(
    background_tasks: BackgroundTasks,
    data_dir: str = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Import all datasets from the data directory.
    
    Args:
        data_dir: Path to the data directory (optional, uses default if not provided)
        db: Database session
    
    Returns:
        Import status
    """
    try:
        # Use default data directory if not provided
        if not data_dir:
            # Try to find data directory
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            data_dir = os.path.join(current_dir, "data")
            
        if not os.path.exists(data_dir):
            raise HTTPException(
                status_code=400,
                detail=f"Data directory not found: {data_dir}"
            )
        
        # Import script path
        script_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
        script_path = os.path.join(script_dir, "import_datasets.py")
        
        # Run the import script in the background
        background_tasks.add_task(
            run_import_script,
            script_path=script_path
        )
        
        return {
            "status": "accepted",
            "message": "Dataset import process started in background",
            "data_dir": data_dir
        }
        
    except Exception as e:
        logger.error(f"Error starting dataset import: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error starting dataset import: {str(e)}"
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

async def run_import_script(script_path: str):
    """Run the import script as a subprocess."""
    import subprocess
    import sys
    
    try:
        logger.info(f"Running import script: {script_path}")
        subprocess.run([sys.executable, script_path], check=True)
        logger.info("Import script completed successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Import script failed with exit code {e.returncode}")
    except Exception as e:
        logger.error(f"Error running import script: {str(e)}")

"""
Script to import question datasets from JSON files.
This script imports all JSON datasets from the data directory into the database.
"""
import json
import asyncio
import sys
import os
import logging
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

# Add parent directory to path to allow imports
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from app.core.database import async_session, create_tables
from app.models.question import Question
from app.models.module import Module, ModuleCategory, DifficultyLevel
from app.services.embedding_service import EmbeddingService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Map dataset filenames to module categories
DATASET_MODULE_MAPPING = {
    "SWE_dataset.json": ModuleCategory.SOFTWARE_ENGINEERING,
    "ML_dataset.json": ModuleCategory.MACHINE_LEARNING, 
    "DSA_dataset.json": ModuleCategory.DATA_STRUCTURES,
    "Resume_dataset.json": ModuleCategory.RESUME_DRIVEN,
    "Resumes_dataset.json": ModuleCategory.RESUME_DRIVEN,
}

# Dataset root directory
DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "data"

embedding_service = EmbeddingService()


async def create_module_if_not_exists(db: AsyncSession, title: str, category: ModuleCategory, difficulty: DifficultyLevel = DifficultyLevel.MEDIUM) -> int:
    """
    Create a module if it doesn't already exist.
    
    Args:
        db: Database session
        title: Module title
        category: Module category
        difficulty: Module difficulty
        
    Returns:
        Module ID
    """
    # Check if module exists
    stmt = text("SELECT id FROM modules WHERE title = :title LIMIT 1")
    result = await db.execute(stmt, {"title": title})
    module_id = result.scalar()
    
    if module_id:
        logger.info(f"Module '{title}' already exists with ID {module_id}")
        return module_id
    
    # Create new module
    module = Module(
        title=title,
        description=f"Questions for {title}",
        category=category,
        difficulty=difficulty,
        duration_minutes=30,
        is_active=1
    )
    
    db.add(module)
    await db.commit()
    await db.refresh(module)
    
    logger.info(f"Created new module '{title}' with ID {module.id}")
    return module.id


async def import_dataset(db: AsyncSession, file_path: Path, module_id: int):
    """
    Import questions from a dataset JSON file.
    
    Args:
        db: Database session
        file_path: Path to the dataset file
        module_id: Module ID to associate questions with
    """
    try:
        # Read the JSON file
        with open(file_path, 'r', encoding='utf-8') as f:
            questions_data = json.load(f)
        
        logger.info(f"Importing {len(questions_data)} questions from {file_path.name}")
        
        # Process each question
        for item in questions_data:
            # Skip if required fields are missing
            if 'text' not in item:
                logger.warning(f"Skipping question without text: {item}")
                continue
                
            # Extract question data
            # Handle variations in dataset formats
            question = Question(
                text=item['text'],
                module_id=module_id,
                difficulty=item.get('difficulty', 'medium'),
                domain=get_domain_from_file_path(file_path.name),
                type=item.get('type', 'general'),
                question_type=item.get('question_type', 'open_ended'),
                tags=item.get('tags', item.get('follow_up_templates', [])),
                ideal_answer=item.get('ideal_answer', item.get('ideal_answer_summary', None)),
                expected_duration_seconds=item.get('expected_duration_seconds', 300),
                scoring_criteria=item.get('scoring_criteria', {})
            )
            
            # Add to database
            db.add(question)
        
        # Commit the transaction
        await db.commit()
        logger.info(f"Successfully imported questions from {file_path.name}")
        
        # Return the count for synchronization
        return len(questions_data)
    
    except Exception as e:
        logger.error(f"Error importing dataset {file_path.name}: {str(e)}")
        return 0


def get_domain_from_file_path(file_name: str) -> str:
    """
    Derive domain from dataset file name.
    
    Args:
        file_name: Name of the dataset file
        
    Returns:
        Domain string
    """
    if file_name.startswith("SWE"):
        return "Software Engineering"
    elif file_name.startswith("ML"):
        return "Machine Learning"
    elif file_name.startswith("DSA"):
        return "Data Structures and Algorithms"
    elif file_name.startswith("Resume"):
        return "Resume"
    else:
        return "general"


async def main():
    """Main entry point for the script."""
    logger.info("Starting dataset import process")
    
    # Create tables if they don't exist
    await create_tables()
    
    # Get async session
    async with async_session() as db:
        try:
            # Process each dataset file
            total_imported = 0
            
            for file_path in DATA_DIR.glob("*.json"):
                if file_path.name in DATASET_MODULE_MAPPING:
                    # Create or get module
                    module_title = file_path.stem.replace("_dataset", "").replace("_", " ").title()
                    module_category = DATASET_MODULE_MAPPING[file_path.name]
                    
                    module_id = await create_module_if_not_exists(db, module_title, module_category)
                    
                    # Import dataset
                    count = await import_dataset(db, file_path, module_id)
                    total_imported += count
            
            logger.info(f"Total questions imported: {total_imported}")
            
            # Sync questions to vector database
            if total_imported > 0:
                logger.info("Starting vector sync for imported questions")
                await embedding_service.continuous_sync_worker(batch_size=100)
                logger.info("Vector sync completed")
            
        except Exception as e:
            logger.error(f"Error in import process: {str(e)}")
        finally:
            await db.close()
    
    logger.info("Dataset import process completed")


if __name__ == "__main__":
    asyncio.run(main())

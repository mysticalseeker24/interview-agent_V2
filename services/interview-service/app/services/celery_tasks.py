"""
Celery tasks for TalentSync Interview Service.
"""

import logging
import os
from celery import Celery
from celery.schedules import crontab
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.services.pinecone_service import PineconeService

logger = logging.getLogger(__name__)

# Initialize Celery app
celery_app = Celery('talentsync_tasks',
                  broker=os.getenv('RABBITMQ_URL', 'amqp://guest:guest@localhost/'),
                  backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'))

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    broker_connection_retry_on_startup=True
)

# Configure beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    'process-question-events': {
        'task': 'app.services.celery_tasks.process_question_events_task',
        'schedule': 60.0,  # Run every 60 seconds
    },
    'sync-all-questions': {
        'task': 'app.services.celery_tasks.sync_all_questions_task',
        'schedule': crontab(hour=2, minute=0),  # Run daily at 2 AM
    },
}

# DB Connection
def get_db_session():
    """Create and return a database session."""
    engine = create_engine(os.getenv('DATABASE_URL'))
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return Session()


@celery_app.task(name="app.services.celery_tasks.process_question_events_task")
def process_question_events_task():
    """
    Process unprocessed question events from the question_events table.
    This task reads events from the database and publishes them to RabbitMQ.
    """
    logger.info("Starting question events processing task")
    
    session = get_db_session()
    pinecone_service = PineconeService()
    
    try:
        # Get unprocessed events
        result = session.execute(
            text("SELECT id, question_id, event_type, payload FROM question_events "
                 "WHERE processed = FALSE ORDER BY created_at LIMIT 100")
        )
        
        events = result.fetchall()
        logger.info(f"Found {len(events)} unprocessed question events")
        
        for event in events:
            event_id, question_id, event_type, payload = event
            
            # Get question data
            question_result = session.execute(
                text("SELECT id, text, domain, type, difficulty FROM questions WHERE id = :id"),
                {"id": question_id}
            )
            question_data = question_result.fetchone()
            
            if question_data:
                # Sync to Pinecone
                question_id, text, domain, q_type, difficulty = question_data
                pinecone_service.sync_question_to_pinecone(
                    question_id=question_id, 
                    question_text=text,
                    domain=domain, 
                    question_type=q_type, 
                    difficulty=difficulty
                )
                
                # Mark event as processed
                session.execute(
                    text("UPDATE question_events SET processed = TRUE WHERE id = :id"),
                    {"id": event_id}
                )
                
                logger.info(f"Processed question event {event_id} for question {question_id}")
            else:
                logger.warning(f"Question {question_id} not found for event {event_id}")
        
        session.commit()
        logger.info("Question events processing task completed")
        
        return {"status": "success", "processed_events": len(events)}
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error processing question events: {str(e)}")
        return {"status": "error", "error": str(e)}
        
    finally:
        session.close()


@celery_app.task(name="app.services.celery_tasks.sync_all_questions_task")
def sync_all_questions_task(batch_size=100):
    """
    Sync all questions to Pinecone.
    This task runs periodically to ensure all questions are synced.
    
    Args:
        batch_size: Number of questions to process in each batch
    """
    logger.info(f"Starting sync all questions task with batch size {batch_size}")
    
    session = get_db_session()
    pinecone_service = PineconeService()
    
    try:
        # Get total count
        total_result = session.execute(text("SELECT COUNT(*) FROM questions"))
        total_questions = total_result.scalar()
        
        logger.info(f"Found {total_questions} questions to sync")
        
        # Process in batches
        offset = 0
        processed = 0
        
        while offset < total_questions:
            # Get batch of questions
            result = session.execute(
                text("SELECT id, text, domain, type, difficulty FROM questions "
                     "ORDER BY id LIMIT :limit OFFSET :offset"),
                {"limit": batch_size, "offset": offset}
            )
            
            questions = result.fetchall()
            
            for question in questions:
                question_id, text, domain, q_type, difficulty = question
                
                # Sync to Pinecone
                pinecone_service.sync_question_to_pinecone(
                    question_id=question_id, 
                    question_text=text,
                    domain=domain, 
                    question_type=q_type, 
                    difficulty=difficulty
                )
                
                processed += 1
                
                if processed % 10 == 0:
                    logger.info(f"Synced {processed}/{total_questions} questions")
            
            offset += batch_size
        
        logger.info(f"Sync all questions task completed. Synced {processed} questions.")
        
        return {"status": "success", "synced_questions": processed}
        
    except Exception as e:
        logger.error(f"Error syncing all questions: {str(e)}")
        return {"status": "error", "error": str(e)}
        
    finally:
        session.close()


@celery_app.task(name="app.services.celery_tasks.sync_question_task")
def sync_question_task(question_id):
    """
    Sync a specific question to Pinecone.
    
    Args:
        question_id: ID of the question to sync
    """
    logger.info(f"Starting sync task for question {question_id}")
    
    session = get_db_session()
    pinecone_service = PineconeService()
    
    try:
        # Get question data
        result = session.execute(
            text("SELECT id, text, domain, type, difficulty FROM questions WHERE id = :id"),
            {"id": question_id}
        )
        
        question_data = result.fetchone()
        
        if question_data:
            question_id, text, domain, q_type, difficulty = question_data
            
            # Sync to Pinecone
            pinecone_service.sync_question_to_pinecone(
                question_id=question_id, 
                question_text=text,
                domain=domain, 
                question_type=q_type, 
                difficulty=difficulty
            )
            
            logger.info(f"Successfully synced question {question_id}")
            
            return {"status": "success", "question_id": question_id}
        else:
            logger.warning(f"Question {question_id} not found")
            return {"status": "error", "error": f"Question {question_id} not found"}
        
    except Exception as e:
        logger.error(f"Error syncing question {question_id}: {str(e)}")
        return {"status": "error", "error": str(e)}
        
    finally:
        session.close()

"""Post-interview feedback generation tasks using feedback-service."""
import logging
import requests
from typing import Dict, Any

from app.tasks import celery_app
from app.core.config import get_settings

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def generate_feedback(self, session_id: int) -> Dict[str, Any]:
    """
    Generate comprehensive feedback report for a completed interview session by calling the feedback-service.

    Args:
        session_id: The session ID to generate feedback for

    Returns:
        Dictionary containing feedback generation results

    Raises:
        Exception: If feedback generation fails after retries
    """
    try:
        settings = get_settings()
        feedback_service_url = f"{settings.FEEDBACK_SERVICE_URL}/generate-feedback"

        logger.info(f"Requesting feedback generation for session {session_id} from feedback-service")

        response = requests.post(feedback_service_url, json={"session_id": session_id})
        response.raise_for_status()

        logger.info(f"Feedback generation completed for session {session_id}")
        return response.json()

    except requests.RequestException as exc:
        logger.error(f"Error generating feedback for session {session_id}: {str(exc)}")
        raise exc

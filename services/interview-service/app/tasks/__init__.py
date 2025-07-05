"""Celery configuration for interview service tasks."""
import os
from celery import Celery

# Configure Celery
celery_app = Celery(
    "interview_tasks",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
    include=["app.tasks.feedback"]
)

# Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,
    task_reject_on_worker_lost=True,
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    task_routes={
        "app.tasks.feedback.generate_feedback": {"queue": "feedback"},
        "app.tasks.feedback.compute_scores": {"queue": "scoring"},
        "app.tasks.feedback.calculate_percentiles": {"queue": "analytics"},
    }
)

# Configure logging
celery_app.conf.worker_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
celery_app.conf.worker_task_log_format = '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    'update-percentiles-daily': {
        'task': 'app.tasks.feedback.update_historical_percentiles',
        'schedule': 86400.0,  # 24 hours
    },
}

"""
Celery configuration for Media Service background tasks.
"""
import os
from celery import Celery

from app.core.config import get_settings

settings = get_settings()

# Create Celery instance
celery_app = Celery(
    "media_service",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.media_tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,
    task_compression="gzip",
    result_compression="gzip",
    task_routes={
        "app.workers.media_tasks.process_chunk": {"queue": "media_processing"},
        "app.workers.media_tasks.validate_chunk": {"queue": "media_validation"},
        "app.workers.media_tasks.cleanup_session": {"queue": "media_cleanup"},
        "app.workers.media_tasks.check_session_gaps": {"queue": "media_monitoring"},
    },
    task_default_queue="default",
    task_queues={
        "media_processing": {
            "exchange": "media_processing",
            "routing_key": "media_processing",
        },
        "media_validation": {
            "exchange": "media_validation", 
            "routing_key": "media_validation",
        },
        "media_cleanup": {
            "exchange": "media_cleanup",
            "routing_key": "media_cleanup",
        },
        "media_monitoring": {
            "exchange": "media_monitoring",
            "routing_key": "media_monitoring",
        },
    },
    beat_schedule={
        "check-session-gaps": {
            "task": "app.workers.media_tasks.check_session_gaps",
            "schedule": 300.0,  # Every 5 minutes
        },
        "cleanup-old-files": {
            "task": "app.workers.media_tasks.cleanup_old_files",
            "schedule": 3600.0,  # Every hour
        },
        "health-check": {
            "task": "app.workers.media_tasks.health_check",
            "schedule": 60.0,  # Every minute
        },
    },
)

# Auto-discover tasks
celery_app.autodiscover_tasks()

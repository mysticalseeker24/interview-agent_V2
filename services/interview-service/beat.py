"""
Celery beat scheduler entry point for TalentSync Interview Service.
This file is used to start the Celery beat scheduler for periodic tasks.
"""

import os
import logging

# Configure logging before importing Celery
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import Celery app
from app.services.celery_tasks import celery_app


if __name__ == '__main__':
    # Start Celery beat scheduler
    print("Starting Celery beat scheduler...")
    celery_app.start(
        ['beat', '--loglevel=info']
    )

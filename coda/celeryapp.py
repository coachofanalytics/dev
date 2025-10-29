"""
Celery configuration for CODA project.

PHASE 2 IMPROVEMENT: Async task processing for GoToMeeting and other services.

This enables:
- Background meeting fetches (don't block web requests)
- Scheduled tasks (daily meeting sync)
- Parallel processing (batch API calls)
- Better user experience (instant response, email when complete)

IMPORTANT: This file is named 'celeryapp.py' (not celery.py) to avoid
circular import conflict with the celery library.

Usage:
    # Start Celery worker
    celery -A coda.celeryapp worker -l info
    
    # Start Celery beat (for scheduled tasks)
    celery -A coda.celeryapp beat -l info
"""

import os
from celery import Celery
from django.conf import settings

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.settings')

# Create Celery app
app = Celery('coda')

# Load configuration from Django settings
# Using 'CELERY' namespace means all celery-related config keys
# should be prefixed with 'CELERY_', e.g., CELERY_BROKER_URL
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodiscover tasks in all installed apps
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    """Debug task to test Celery is working"""
    print(f'Request: {self.request!r}')


# Celery configuration
app.conf.update(
    # Broker settings (Redis recommended, falls back to Django DB)
    broker_url=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    
    # Result backend
    result_backend=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task time limits
    task_soft_time_limit=300,  # 5 minutes soft limit
    task_time_limit=600,       # 10 minutes hard limit
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # Task routing
    task_routes={
        'ai_services.tasks.fetch_meetings_task': {'queue': 'meetings'},
        'ai_services.tasks.download_recording_task': {'queue': 'recordings'},
    },
    
    # Retry settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)


# Import celery beat schedule helper
from celery.schedules import crontab

# Celery Beat schedule (for periodic tasks)
app.conf.beat_schedule = {
    'daily-meeting-sync': {
        'task': 'ai_services.tasks.daily_meeting_sync_task',
        'schedule': crontab(hour=1, minute=0),  # 1 AM UTC
        'args': (),
    },
    'daily-position-fetch': {
        'task': 'investing.tasks.daily_position_fetch_task',
        'schedule': crontab(hour=14, minute=0),  # 9 AM EST = 14:00 UTC (during DST) / 15:00 UTC (standard)
        'args': (),
    },
    'hourly-batch-timeout-check': {
        'task': 'investing.tasks.process_batch_timeouts_task',
        'schedule': crontab(minute=0),  # Every hour at :00
        'args': (),
    },
    'weekly-position-summary': {
        'task': 'investing.tasks.send_weekly_position_summary_task',
        'schedule': crontab(day_of_week=1, hour=13, minute=0),  # Monday 8 AM EST = 13:00 UTC
        'args': (),
    },
}


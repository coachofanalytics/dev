"""
Celery Configuration for Biashara Bridges
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Create Celery app
app = Celery('biashara_bridges')

# Load configuration from Django settings with CELERY namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()

# Periodic Tasks Schedule
app.conf.beat_schedule = {
    'expire-subscriptions-daily': {
        'task': 'payments.tasks.expire_subscriptions_task',
        'schedule': crontab(hour=2, minute=0),  # Run at 2 AM daily
    },
    'check-pending-transactions': {
        'task': 'payments.tasks.check_pending_transactions_task',
        'schedule': crontab(minute='*/30'),  # Run every 30 minutes
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery"""
    print(f'Request: {self.request!r}')
